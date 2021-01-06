from typing import List, Optional, Union

from src.channel_model.sinr import ChannelModel
from src.resource_allocation.algo.space import Space
from src.resource_allocation.ds.nodeb import ENBInfo, GNBInfo
from src.resource_allocation.ds.rb import ResourceBlock
from src.resource_allocation.ds.ue import UserEquipment
from src.resource_allocation.ds.util_enum import LTEResourceBlock, NodeBType, Numerology, UEType


class AllocateUE:
    def __init__(self, ue: UserEquipment, spaces: List[Space], channel_model: ChannelModel):
        assert ue.is_allocated is False
        self.ue: UserEquipment = ue
        assert len(set([s.layer.nodeb.nb_type for s in spaces])) == 1
        self.spaces: List[Space] = spaces
        self.channel_model: ChannelModel = channel_model

    def allocate(self) -> bool:
        tmp_numerology: Numerology = self.ue.numerology_in_use
        if self.spaces[0].layer.nodeb.nb_type == NodeBType.E and self.ue.ue_type == UEType.D:
            self.ue.numerology_in_use = LTEResourceBlock.E  # TODO: refactor or redesign

        is_succeed: bool = self.new_ue()

        self.ue.numerology_in_use = tmp_numerology  # restore

        return is_succeed

    def new_ue(self) -> bool:
        """
        The self.ue must be an unallocated UE.
        In this method, self.ue will be allocated to one BS only.
        :return: If the allocation has succeed.
        """
        bu_i: int = -1
        bu_j: int = -1
        nb_info: Optional[GNBInfo, ENBInfo] = None
        space: Optional[Space] = None
        is_to_next_space: bool = True
        while True:
            if is_to_next_space:
                if self.spaces:
                    space: Space = self.spaces.pop(0)
                    if self.ue.numerology_in_use in space.rb_type:
                        bu_i: int = space.starting_i
                        bu_j: int = space.starting_j
                        nb_info: Union[GNBInfo, ENBInfo] = (
                            self.ue.gnb_info if space.layer.nodeb.nb_type == NodeBType.G else self.ue.enb_info)
                        is_to_next_space: bool = False
                    else:
                        # the space is not big enough for a RB the UE is using
                        continue
                else:
                    # run out of spaces before achieving QoS
                    return False

            rb: Optional[ResourceBlock] = space.layer.allocate_resource_block(bu_i, bu_j, self.ue)
            if rb is None:
                # overlapped with itself
                raise AssertionError

            self.channel_model.sinr_rb(rb)
            nb_info.rb.sort(key=lambda x: x.sinr, reverse=True)

            tmp_throughput: float = nb_info.rb[-1].mcs.value * len(nb_info.rb)

            if tmp_throughput >= self.ue.request_data_rate:
                self.ue.throughput = tmp_throughput
                self.ue.is_allocated = True
                self.ue.is_to_recalculate_mcs = False
                return True

            if bu := space.next_rb(bu_i, bu_j, self.ue.numerology_in_use):
                bu_i: int = bu[0]
                bu_j: int = bu[1]
            else:
                # running out of space in this "space"
                is_to_next_space: bool = True

    def undo(self):
        pass
