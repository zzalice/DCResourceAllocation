from typing import List, Optional, Tuple, Union

from src.channel_model.adjust_mcs import AdjustMCS
from src.channel_model.sinr import ChannelModel
from src.resource_allocation.ds.nodeb import ENBInfo, GNBInfo, NodeB
from src.resource_allocation.ds.rb import ResourceBlock
from src.resource_allocation.ds.space import Space
from src.resource_allocation.ds.ue import UserEquipment
from src.resource_allocation.ds.undo import Undo
from src.resource_allocation.ds.util_enum import E_MCS, G_MCS, LTEResourceBlock, NodeBType, Numerology, UEType
from utils.assertion import ThroughputError


class AllocateUE(Undo):
    """
    In this method, self.ue will be allocated to one BS only.
    The new RBs can be continuous or non-continuous.
    :return: If the allocation has succeed.
    """

    def __init__(self, ue: UserEquipment, spaces: Tuple[Space, ...], channel_model: ChannelModel,
                 request_data_rate: Optional[float] = None):
        super().__init__()
        self.ue: UserEquipment = ue
        assert len(
            set([s.layer.nodeb.nb_type for s in spaces])) == 1, "The input spaces are not from the same BS or is empty."
        self.spaces: List[Space] = list(spaces)
        self.channel_model: ChannelModel = channel_model
        assert request_data_rate is None or request_data_rate > 0.0, 'Data rate too low.'
        self.request: Optional[float] = request_data_rate

    @Undo.undo_func_decorator
    def allocate(self, to_allow_non_continuous: bool = False) -> bool:
        tmp_numerology: Numerology = self.ue.numerology_in_use
        if self.spaces[0].layer.nodeb.nb_type == NodeBType.E and self.ue.ue_type == UEType.D:
            self.ue.numerology_in_use = LTEResourceBlock.E  # TODO: refactor or redesign

        is_succeed: bool = self._allocate(to_allow_non_continuous)

        self.ue.numerology_in_use = tmp_numerology  # restore

        return is_succeed

    def _allocate(self, to_allow_non_continuous: bool) -> bool:
        # assert self.ue.calc_throughput() < self.ue.request_data_rate  # TODO: refactor, for MCUP combine RA algorithms
        nb_info: Union[GNBInfo, ENBInfo] = (
            self.ue.gnb_info if self.spaces[0].layer.nodeb.nb_type == NodeBType.G else self.ue.enb_info)
        bu_i: int = -1
        bu_j: int = -1
        space: Optional[Space] = None
        is_to_next_space: bool = True
        while True:
            # the position for the new RB
            if is_to_next_space:
                if space_rb := self.next_space():
                    space: Space = space_rb[0]
                    bu_i: int = space_rb[1]
                    bu_j: int = space_rb[2]
                    is_to_next_space: bool = False
                else:  # run out of space
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
                if to_allow_non_continuous:
                    self.undo_in_last_func(last_move_times=1)
                    continue
                else:
                    return False

            self.channel_model.sinr_rb(rb)
            self.append_undo(lambda: self.channel_model.undo(), lambda: self.channel_model.purge_undo())
            if rb.mcs is (G_MCS if nb_info.nb_type == NodeBType.G else E_MCS).CQI0:
                # SINR out of range
                if to_allow_non_continuous:
                    self.undo_in_last_func(last_move_times=2)
                    continue
                else:
                    return False

            # check if the allocated RBs fulfill request data rate
            if self.is_fulfilled(nb_info):
                self.append_undo(lambda origin=nb_info.mcs: setattr(nb_info, 'mcs', origin))
                self.append_undo(lambda origin=self.ue.throughput: setattr(self.ue, 'throughput', origin))
                self.append_undo(
                    lambda origin=self.ue.is_to_recalculate_mcs: setattr(self.ue, 'is_to_recalculate_mcs', origin))

                nb_info.update_mcs()
                self.ue.update_throughput()
                self.ue.is_to_recalculate_mcs = False
                return True

    def is_fulfilled(self, nb_info: Union[GNBInfo, ENBInfo]) -> bool:
        if self.request is None:
            return self.ue.calc_throughput() >= self.ue.request_data_rate
        else:  # has input request
            return (min(nb_info.rb, key=lambda rb: rb.mcs.value).mcs.value * len(nb_info.rb)) >= self.request

    def next_space(self) -> Optional[Tuple[Space, int, int]]:
        while self.spaces:
            space: Space = self.spaces.pop(0)
            if self.ue.numerology_in_use in space.rb_type:  # the space is big enough for a RB the UE is using
                return space, space.starting_i, space.starting_j
        return None


class DCProportionAllocate(Undo):
    """
    This class is for DC UE allocation.
    In this method, the dUE will be allocate to two BSs by the proportion of channel quality (force DC).
    The RBs in a BS will be continuous.
    """

    def __init__(self, ue: UserEquipment, channel_model: ChannelModel):
        super().__init__()
        assert ue.ue_type == UEType.D
        self.ue: UserEquipment = ue
        self.channel_model: ChannelModel = channel_model

    @Undo.undo_func_decorator
    def allocate(self, space_in_nbs: Tuple[Tuple[Space, ...]]) -> bool:
        """
        :param space_in_nbs: The empty spaces to allocate in two different BSs.
        :return: If the allocation succeed.
        """
        assert len(space_in_nbs) == 2, 'Should input the spaces in two BSs.'
        assert len(set([s.layer.nodeb.nb_type for s in
                        space_in_nbs[0]])) == 1, "The input spaces are not from the same BS or is empty."
        assert len(set([s.layer.nodeb.nb_type for s in
                        space_in_nbs[1]])) == 1, "The input spaces are not from the same BS or is empty."
        nbs: Tuple[NodeB, NodeB] = (space_in_nbs[0][0].layer.nodeb, space_in_nbs[1][0].layer.nodeb)
        assert nbs[0] != nbs[1], "Two lists of spaces aren't from two different of BS."

        request: Tuple[float, float] = self.calc_request_proportion(nbs)

        # force DC
        for i in range(len(space_in_nbs)):
            is_allocated: bool = self.allocate_nb(space_in_nbs[i], request[i])
            if not is_allocated:
                return False
        assert self.ue.calc_throughput() >= self.ue.request_data_rate, 'Fail to fulfill dUE.'

        has_succeed: bool = self.adjust_mcs()
        return has_succeed

    def allocate_nb(self, spaces: Tuple[Space, ...], request_data_rate):
        is_allocated: bool = False
        allocate_ue: AllocateUE = AllocateUE(self.ue, spaces, self.channel_model, request_data_rate=request_data_rate)
        try:
            is_allocated: bool = allocate_ue.allocate()
        except ThroughputError:
            pass
        self.append_undo(lambda a_u=allocate_ue: a_u.undo(), lambda a_u=allocate_ue: a_u.purge_undo())
        return is_allocated

    def adjust_mcs(self):
        adjust_mcs: AdjustMCS = AdjustMCS()
        has_succeed: bool = adjust_mcs.remove_from_tail(self.ue)
        self.append_undo(lambda a_m=adjust_mcs: a_m.undo(), lambda a_m=adjust_mcs: a_m.purge_undo())
        return has_succeed

    def calc_request_proportion(self, nbs: Tuple[NodeB, NodeB]) -> Tuple[float, float]:
        """
        Calculate the proportion of request data rate for two BSs according to channel quality.
        :param nbs: Two BSs.
        :return: The data rate request of the two BSs, in order.
        """
        assert len(nbs) == 2, 'Should input two BS types.'
        assert (nbs[0].nb_type == NodeBType.G and nbs[1].nb_type == NodeBType.E) or (
                nbs[0].nb_type == NodeBType.E and nbs[1].nb_type == NodeBType.G
        ), 'Should input two different types of BSs.'

        # calculate the proportion
        rx_power_nb: List[float] = []
        for nb in nbs:
            if nb.nb_type == NodeBType.G:
                rx_power: float = self.channel_model.power_rx(nb.nb_type, nb.power_tx, self.ue.coordinate.distance_gnb)
            elif nb.nb_type == NodeBType.E:
                rx_power: float = self.channel_model.power_rx(nb.nb_type, nb.power_tx, self.ue.coordinate.distance_enb)
            else:
                raise AssertionError
            rx_power_nb.append(rx_power)
        total: float = rx_power_nb[0] + rx_power_nb[1]
        proportion: List[float] = [i / total for i in rx_power_nb]

        # calculate the request data rate for each BS
        request: Tuple[float, float] = tuple(self.ue.request_data_rate * i for i in proportion)
        assert len(request) == 2
        return request
