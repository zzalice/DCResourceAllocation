from typing import List, Optional, Tuple, Union

from src.channel_model.sinr import ChannelModel
from src.resource_allocation.ds.nodeb import ENBInfo, GNBInfo
from src.resource_allocation.ds.rb import ResourceBlock
from src.resource_allocation.ds.space import Space
from src.resource_allocation.ds.ue import UserEquipment
from src.resource_allocation.ds.undo import Undo
from src.resource_allocation.ds.util_enum import E_MCS, G_MCS, LTEResourceBlock, NodeBType, Numerology, UEType


class AllocateUE(Undo):
    """
    In this method, self.ue will be allocated to one BS only.
    The RBs can be discontinuous.
    :return: If the allocation has succeed.
    """

    def __init__(self, ue: UserEquipment, spaces: Tuple[Space, ...],
                 channel_model: ChannelModel):
        super().__init__()
        self.ue: UserEquipment = ue
        assert len(
            set([s.layer.nodeb.nb_type for s in spaces])) == 1, "The input spaces are not from the same BS or is empty."
        self.spaces: List[Space] = list(spaces)
        self.channel_model: ChannelModel = channel_model

    @Undo.undo_func_decorator
    def allocate(self) -> bool:
        tmp_numerology: Numerology = self.ue.numerology_in_use
        if self.spaces[0].layer.nodeb.nb_type == NodeBType.E and self.ue.ue_type == UEType.D:
            self.ue.numerology_in_use = LTEResourceBlock.E  # TODO: refactor or redesign

        is_succeed: bool = self._allocate()

        self.ue.numerology_in_use = tmp_numerology  # restore

        return is_succeed

    def _allocate(self) -> bool:
        assert self.ue.calc_throughput() < self.ue.request_data_rate
        nb_info: Union[GNBInfo, ENBInfo] = (
            self.ue.gnb_info if self.spaces[0].layer.nodeb.nb_type == NodeBType.G else self.ue.enb_info)
        bu_i: int = -1
        bu_j: int = -1
        space: Optional[Space] = None
        is_to_next_space: bool = True
        while True:
            # the position for the new RB
            if is_to_next_space:
                if self.spaces:
                    space: Space = self.spaces.pop(0)
                    if self.ue.numerology_in_use in space.rb_type:
                        bu_i: int = space.starting_i
                        bu_j: int = space.starting_j
                        is_to_next_space: bool = False
                    else:
                        # the space is not big enough for a RB the UE is using
                        continue
                else:
                    # run out of spaces before achieving QoS
                    return False
            else:
                if bu := space.next_rb(bu_i, bu_j, self.ue.numerology_in_use):
                    bu_i: int = bu[0]
                    bu_j: int = bu[1]
                else:
                    # running out of space in this "space"
                    is_to_next_space: bool = True
                    continue

            # allocate a new RB
            rb: Optional[ResourceBlock] = space.layer.allocate_resource_block(bu_i, bu_j, self.ue)
            self.append_undo(lambda l=space.layer: l.undo(), lambda l=space.layer: l.purge_undo())
            if not rb:
                # overlapped with itself
                continue

            self.channel_model.sinr_rb(rb)
            self.append_undo(lambda: self.channel_model.undo(), lambda: self.channel_model.purge_undo())
            if rb.mcs is (G_MCS if nb_info.nb_type == NodeBType.G else E_MCS).CQI0:
                # SINR out of range
                return False  # TODO: [refactor] 可以只刪掉這個rb，繼續試下一個位子(非is_to_next_space=True)

            # check if the allocated RBs fulfill request data rate
            if self.ue.calc_throughput() >= self.ue.request_data_rate:
                self.append_undo(lambda origin=nb_info.mcs: setattr(nb_info, 'mcs', origin))
                self.append_undo(lambda origin=self.ue.throughput: setattr(self.ue, 'throughput', origin))
                self.append_undo(
                    lambda origin=self.ue.is_to_recalculate_mcs: setattr(self.ue, 'is_to_recalculate_mcs', origin))

                nb_info.update_mcs()
                self.ue.update_throughput()
                self.ue.is_to_recalculate_mcs = False
                return True
