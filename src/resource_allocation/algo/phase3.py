from typing import Dict, List, Tuple, Union

from src.channel_model.adjust_mcs import AdjustMCS
from src.channel_model.sinr import ChannelModel
from src.resource_allocation.algo.dual_connection import DualConnection
from src.resource_allocation.algo.new_single_ue import AllocateUE
from src.resource_allocation.algo.utils import calc_system_throughput
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
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

        # ue cut
        for ue in ue_allocated:
            if ue.is_allocated:
                self.ue_cut(ue, nb.nb_type)

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
            filtered_space: Tuple[Space] = self.filter_space(
                spaces, nb.nb_type, ue.numerology_in_use, ue.request_data_rate)
            is_allocated: bool = False
            for space in filtered_space:
                # from utils.assertion import check_undo_copy
                # copy_ue = check_undo_copy(ue_allocated)
                is_allocated: bool = self.allocate(ue, (space,), nb.nb_type, allocated_ue, worsen_threshold)
                if is_allocated:
                    spaces: Tuple[Space] = self.update_empty_space(nb)
                    self.purge_undo()
                    break
                else:
                    self.undo()
                    # from utils.assertion import check_undo_compare
                    # check_undo_compare(ue_allocated, copy_ue)
                # from utils.assertion import assert_is_empty
                # assert_is_empty(spaces, ue, is_allocated)
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
        is_allocated: bool = allocate_ue.allocate()
        self.append_undo(lambda a_u=allocate_ue: a_u.undo(), lambda a_u=allocate_ue: a_u.purge_undo())

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
                     ue_request: float) -> Tuple[Space]:
        if nb_type == NodeBType.E:
            rb_type: LTEResourceBlock = LTEResourceBlock.E  # TODO: refactor or redesign

        filter_spaces: List[Space] = list(spaces)
        for space in spaces:
            best_mcs: Union[G_MCS, E_MCS] = (G_MCS if nb_type == NodeBType.G else E_MCS).get_best()
            if not space.request_fits(ue_request, rb_type, best_mcs):
                filter_spaces.remove(space)
        return tuple(filter_spaces)

    def ue_cut(self, ue: UE, nb_type: NodeBType, to_undo: bool = False):
        if ue.ue_type == UEType.G or ue.ue_type == UEType.E:
            self.ue_cross_spaces(ue, to_undo)
        elif ue.ue_type == UEType.D:
            self.ue_cross_bs(ue, nb_type, to_undo)
        else:
            raise AssertionError('UE type undefined.')

    def ue_cross_spaces(self, ue: UE, to_undo: bool):
        # FIXME 切較差的一半到別的空間，而且MCS要>=目前的
        pass

    def ue_cross_bs(self, ue: DUserEquipment, nb_type: NodeBType, to_undo: bool):
        dc: DualConnection = DualConnection(ue, self.channel_model)
        is_cut: bool = dc.cutting(ue.gnb_info if nb_type == NodeBType.G else ue.enb_info)
        if is_cut and to_undo:
            self.assert_undo_function()
            self.append_undo(lambda d=dc: d.undo(), lambda d=dc: d.purge_undo())
