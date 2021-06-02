from typing import Dict, List, Optional, Tuple, Union

from src.channel_model.adjust_mcs import AdjustMCS
from src.channel_model.sinr import ChannelModel
from src.resource_allocation.algo.max_subarray import MaxSubarray
from src.resource_allocation.algo.new_single_ue import AllocateUE
from src.resource_allocation.algo.utils import calc_system_throughput
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.resource_allocation.ds.nodeb import ENBInfo, GNBInfo
from src.resource_allocation.ds.rb import ResourceBlock
from src.resource_allocation.ds.space import empty_space, Space
from src.resource_allocation.ds.ue import UserEquipment
from src.resource_allocation.ds.undo import Undo
from src.resource_allocation.ds.util_enum import E_MCS, G_MCS, LTEResourceBlock, NodeBType, Numerology, UEType
from src.resource_allocation.ds.util_type import LappingPosition, LappingPositionList
from src.resource_allocation.ds.zone import Zone

UE = Union[UserEquipment, DUserEquipment, GUserEquipment, EUserEquipment]


class Phase3(Undo):
    def __init__(self, channel_model: ChannelModel):
        super().__init__()
        self.channel_model: ChannelModel = channel_model

        self.throughput_threshold: int = 10  # bit per frame

    def phase2_ue_adjust_mcs(self, nb: Union[GNodeB, ENodeB], zones: List[List[Zone]]):
        """
        Adjust the MCS of the allocated UEs in Phase 2.
        :param nb: Adjust the MCS of the UEs in this BS.
        :param zones: The zones in each layer.
        """
        position: Dict[Numerology, LappingPositionList] = {numerology: LappingPositionList() for numerology in
                                                           Numerology.gen_candidate_set()}

        for layer, zones_in_layer in enumerate(zones):
            for zone in zones_in_layer:
                for ue in zone.ue_list:
                    self.channel_model.sinr_ue(ue)
                    if layer == 0:
                        AdjustMCS().from_highest_mcs(
                            ue, ue.gnb_info.rb if nb.nb_type == NodeBType.G else ue.enb_info.rb, self.channel_model)
                    else:
                        assert ue.gnb_info, "The UE isn't allocated to gNB."
                        AdjustMCS().from_lapped_rb(ue, position[ue.numerology_in_use], self.channel_model)

                    if nb.nb_type == NodeBType.G:
                        self.marking_occupied_position(ue.gnb_info.rb, position)

        # adjust MCS of effected UE
        ue_allocated: List[UE] = []
        for zones_in_layer in zones:
            for zone in zones_in_layer:
                for ue in zone.ue_list:
                    if ue.is_allocated:
                        ue_allocated.append(ue)
        self.adjust_mcs_allocated_ues(ue_allocated, to_undo=False)  # only the UE in this BS

    @staticmethod
    def marking_occupied_position(rb_list: List[ResourceBlock], position: Dict[Numerology, LappingPositionList]):
        for rb in rb_list:
            index = position[rb.numerology].exist([rb.i_start, rb.j_start, rb.numerology])
            if index is not None:
                position[rb.numerology][index].overlapping()
            else:
                position[rb.numerology].append(LappingPosition([rb.i_start, rb.j_start], rb.numerology))

    def allocate_new_ue(self, nb: Union[GNodeB, ENodeB], ue_to_allocate: Tuple[UE, ...], allocated_ue: Tuple[UE, ...],
                        worsen_threshold: float = 0.0):
        unallocated_ue: List[UE] = list(ue_to_allocate)
        unallocated_next_round: List[UE] = []
        allocated_ue: List[UE] = list(allocated_ue)
        spaces: Tuple[Space] = self.update_empty_space(nb)
        system_throughput: float = calc_system_throughput(tuple(allocated_ue))
        while (unallocated_ue or unallocated_next_round) and spaces:
            ue: UE = unallocated_ue.pop(0)
            filtered_space: Tuple[Space] = self.filter_space(spaces, nb.nb_type, ue.numerology_in_use)
            if not filtered_space:  # no suitable space for ue
                continue

            is_allocated: bool = self.allocate(ue, filtered_space, nb.nb_type, allocated_ue, worsen_threshold)
            if is_allocated:
                spaces: Tuple[Space] = self.update_empty_space(nb)
                self.purge_undo()
            else:
                self.undo()

            (allocated_ue if is_allocated else unallocated_next_round).append(ue)

            if not unallocated_ue:  # is empty  TODO: similar to AllocateUEList
                new_system_throughput: float = calc_system_throughput(tuple(allocated_ue))
                if (new_system_throughput - system_throughput) <= self.throughput_threshold:
                    break
                unallocated_ue: List[UE] = unallocated_next_round
                unallocated_next_round: List[UE] = []
                system_throughput: float = new_system_throughput

    @Undo.undo_func_decorator
    def allocate(self, ue: UE, spaces: Tuple[Space, ...], nb_type: NodeBType,
                 ue_allocated: List[UE], worsen_threshold: float) -> bool:
        # allocate new ue
        allocate_ue: AllocateUE = AllocateUE(ue, spaces, self.channel_model)
        is_allocated: bool = allocate_ue.allocate(to_allow_non_continuous=True)
        self.append_undo(lambda a_u=allocate_ue: a_u.undo(), lambda a_u=allocate_ue: a_u.purge_undo())

        if is_allocated:
            self.ue_cut(ue, nb_type, to_undo=True)

        # the effected UEs
        if is_allocated:
            origin_sys_throughput: float = calc_system_throughput(tuple(ue_allocated))
            is_allocated: bool = self.adjust_mcs_allocated_ues([ue] + ue_allocated,
                                                               origin_sys_throughput, worsen_threshold)
        return is_allocated

    def adjust_mcs_allocated_ues(self, ue_allocated: List[UE], origin_sys_throughput: float = 0.0,
                                 worsen_threshold: float = -1000000000, to_undo: bool = True) -> bool:
        self.assert_undo_function() if to_undo else None
        while True:
            # check if the new movement lowers down the system throughput
            if not (calc_system_throughput(tuple(ue_allocated)) - origin_sys_throughput) >= worsen_threshold:
                return False

            # main
            is_all_adjusted: bool = True
            for ue in ue_allocated:
                if ue.is_to_recalculate_mcs:
                    assert ue.is_allocated
                    is_all_adjusted: bool = False
                    self.channel_model.sinr_ue(ue)
                    self.append_undo(lambda: self.channel_model.undo(),
                                     lambda: self.channel_model.purge_undo()) if to_undo else None
                    adjust_mcs: AdjustMCS = AdjustMCS()
                    is_fulfilled: bool = adjust_mcs.remove_worst_rb(ue, allow_lower_than_cqi0=False,
                                                                    channel_model=self.channel_model)
                    self.append_undo(lambda a_m=adjust_mcs: a_m.undo(),
                                     lambda a_m=adjust_mcs: a_m.purge_undo()) if to_undo else None
                    if not is_fulfilled:
                        # the mcs of the ue is lowered down by another UE.
                        return False
            if is_all_adjusted:
                return True

    @staticmethod
    def update_empty_space(nb: Union[GNodeB, ENodeB]) -> Tuple[Space]:
        spaces: List[Space] = [space for layer in nb.frame.layer for space in empty_space(layer)]  # sort by layer
        spaces.sort(key=lambda s: s.starting_j)  # sort by time
        spaces.sort(key=lambda s: s.starting_i)  # sort by freq
        return tuple(spaces)

    @staticmethod
    def filter_space(spaces: Tuple[Space], nb_type: NodeBType, rb_type: Union[Numerology, LTEResourceBlock],
                     ) -> Tuple[Space]:
        if nb_type == NodeBType.E:
            rb_type: LTEResourceBlock = LTEResourceBlock.E  # TODO: refactor or redesign

        filter_spaces: List[Space] = list(spaces)
        for space in spaces:
            if rb_type not in space.rb_type:
                filter_spaces.remove(space)
        return tuple(filter_spaces)

    def ue_cut(self, ue: UE, nb_type: NodeBType, to_undo: bool = False):
        if ue.ue_type == UEType.G or ue.ue_type == UEType.E:
            pass
            # self.ue_cross_spaces(ue, to_undo)
        elif ue.ue_type == UEType.D:
            self.ue_cross_bs(ue, nb_type, to_undo)
        else:
            raise AssertionError('UE type undefined.')

    def ue_cross_spaces(self, ue: UE, to_undo: bool):
        assert ue.ue_type == UEType.G or ue.ue_type == UEType.E
        cs: CrossSpace = CrossSpace(ue, self.channel_model)
        nb_info: Union[GNBInfo, ENBInfo] = ue.gnb_info if ue.ue_type == UEType.G else ue.enb_info
        is_cut: bool = cs.cutting(nb_info, nb_info)
        if is_cut and to_undo:
            self.assert_undo_function()
            self.append_undo(lambda c=cs: c.undo(), lambda c=cs: c.purge_undo())
        else:
            del cs  # undo was done in CrossSpace

    def ue_cross_bs(self, ue: DUserEquipment, nb_type: NodeBType, to_undo: bool):
        assert ue.ue_type == UEType.D
        dc: CrossSpace = CrossSpace(ue, self.channel_model)
        nb_info: Union[GNBInfo, ENBInfo] = ue.gnb_info if nb_type == NodeBType.G else ue.enb_info
        another_nb_info: Union[GNBInfo, ENBInfo] = ue.enb_info if nb_type == NodeBType.G else ue.gnb_info
        is_cut: bool = dc.cutting(nb_info, another_nb_info)
        if is_cut and to_undo:
            self.assert_undo_function()
            self.append_undo(lambda d=dc: d.undo(), lambda d=dc: d.purge_undo())
        else:
            del dc  # undo was done in CrossSpace


class CrossSpace(Undo):
    def __init__(self, ue: UE, channel_model: ChannelModel):
        """
        :param ue: Can be a single or dual connection UE.
        :param channel_model:
        """
        super().__init__()
        assert ue.is_allocated
        self.ue: UE = ue
        self.channel_model: ChannelModel = channel_model

    def cutting(self, nb_info: Union[GNBInfo, ENBInfo], another_nb_info: Union[GNBInfo, ENBInfo]) -> bool:
        """
        Cut part of the RBs in a space to another BS or space.
        To improve resource efficiency by using fewer RBs.
        :param nb_info: The BS to be modified.
        :param another_nb_info: Can be the same as nb_info.
        :return: If the UE is cut into half.
        """
        is_cut: bool = self._cutting(nb_info, another_nb_info)
        if not is_cut:
            self.undo()
        return is_cut

    @Undo.undo_func_decorator
    def _cutting(self, nb_info: Union[GNBInfo, ENBInfo], another_nb_info: Union[GNBInfo, ENBInfo]) -> bool:
        origin_mcs: Union[G_MCS, E_MCS] = nb_info.mcs
        assert origin_mcs, 'UE not allocate to the nb.'
        while True:
            if not self.remove_list_of_rb(nb_info, another_nb_info):
                return False  # no need to cut

            if self.ue.calc_throughput() >= self.ue.request_data_rate:
                # SPECIAL CASE: After the MCS is improved, the QoS is fulfill and might even need less RBs.
                # For example, the origin RB list is [CQI 2, CQI 1, CQI 11, CQI 11, CQI 11, CQI 11, CQI 11, CQI 2],
                #   throughput = CQI 1 * 8 = 176.085
                # After removing the first two RBs, the RB list became [CQI 11, CQI 11, CQI 11, CQI 11, CQI 11, CQI 2],
                #   throughput = CQI 2 * 6 = 203.175
                # but the ue.request_data_rate is 160.
                # Eventually, the UE only need ONE RB of CQI 11.
                self.adjust_mcs()
                continue

            # find spaces in another_nb_info to fulfill QoS
            spaces: Tuple[Space, ...] = self.space_from_another_nb_info(another_nb_info)

            # add new RBs
            if spaces:
                for space in spaces:
                    allocate_ue = AllocateUE(self.ue, (space,), self.channel_model)
                    is_succeed: bool = allocate_ue.allocate(to_allow_non_continuous=True)
                    if is_succeed and (another_nb_info.mcs.efficiency > origin_mcs.efficiency):
                        # resource efficiency is improved
                        self.append_undo(lambda a_u=allocate_ue: a_u.undo(), lambda a_u=allocate_ue: a_u.purge_undo())
                        self.adjust_mcs()   # because the new RB(s) may exceed the rate demand
                        return True
                    else:
                        allocate_ue.undo()
                        del allocate_ue
                return False  # every space fail to allocate
            else:
                # run out of spaces in another_nb_info
                return False

    def remove_list_of_rb(self, ue_nb_info: Union[GNBInfo, ENBInfo], another_nb_info: Union[ENBInfo, GNBInfo]) -> bool:
        if not ue_nb_info.rb:
            return False

        # where to crop the RBs with lower MCS
        max_subarray: MaxSubarray = MaxSubarray(ue_nb_info)
        if not max_subarray.max_subarray():
            # if the MCS can not be improved
            # don't cut
            return False

        if ue_nb_info != another_nb_info:
            assert self.ue.ue_type == UEType.D
            # if the MCS of the other space is lower than the old(current) MCS of this space, don't cut RBs.
            mcs_of_another_bs: Optional[G_MCS, E_MCS] = another_nb_info.mcs
            assert another_nb_info.rb if (mcs_of_another_bs is not None) else (not another_nb_info.rb
                                                                               ), "The MCS in NBInfo isn't up-to-date."
            if mcs_of_another_bs is not None and max_subarray.lower_mcs.efficiency >= mcs_of_another_bs.efficiency:
                # if (the dUE was allocated to another BS) and (the other BS has bad MCS)
                # don't cut
                return False

        max_subarray.remove_rbs()
        self.append_undo(lambda: max_subarray.undo(), lambda: max_subarray.purge_undo())
        return True

    def space_from_another_nb_info(self, another_nb_info: Union[GNBInfo, ENBInfo]) -> Tuple[Space, ...]:
        spaces: Tuple[Space] = tuple(space for layer in another_nb_info.nb.frame.layer for space in empty_space(layer))
        request: float = self.ue.request_data_rate - self.ue.calc_throughput()
        assert request > 0.0, 'No need to request more resource.'
        return Phase3.filter_space(spaces, another_nb_info.nb_type, self.ue.numerology_in_use)

    def adjust_mcs(self):
        adjust_mcs: AdjustMCS = AdjustMCS()
        adjust_mcs.remove_worst_rb(self.ue, channel_model=self.channel_model)
        self.append_undo(lambda a_m=adjust_mcs: a_m.undo(), lambda a_m=adjust_mcs: a_m.purge_undo())
        if not self.ue.is_allocated:
            raise AssertionError
