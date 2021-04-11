from typing import Dict, List, Tuple, Union

from src.channel_model.adjust_mcs import AdjustMCS
from src.channel_model.sinr import ChannelModel
from src.resource_allocation.algo.dual_connection import DualConnection
from src.resource_allocation.algo.new_resource_allocation import AllocateUE
from src.resource_allocation.algo.utils import calc_system_throughput
from src.resource_allocation.ds.eutran import ENodeB
from src.resource_allocation.ds.ngran import GNodeB
from src.resource_allocation.ds.rb import ResourceBlock
from src.resource_allocation.ds.space import empty_space, Space
from src.resource_allocation.ds.ue import UserEquipment
from src.resource_allocation.ds.undo import Undo
from src.resource_allocation.ds.util_enum import NodeBType, Numerology, UEType
from src.resource_allocation.ds.util_type import LappingPosition, LappingPositionList
from src.resource_allocation.ds.zone import Zone


class Phase3(Undo):
    def __init__(self, channel_model: ChannelModel, gnb: GNodeB, enb: ENodeB):
        super().__init__()
        self.gnb: GNodeB = gnb
        self.enb: ENodeB = enb
        self.channel_model: ChannelModel = channel_model

        self.throughput_threshold: int = 10  # bit per frame

    def phase2_ue_adjust_mcs(self, nb_type: NodeBType, zones: List[List[Zone]]):
        """
        Adjust the MCS of the allocated UEs in Phase 2.
        :param nb_type: Adjust the MCS of the UEs in this BS.
        :param zones: The zones in each layer.
        """
        # FIXME: add dUE cut!!!!
        position: Dict[Numerology, LappingPositionList] = {numerology: LappingPositionList() for numerology in
                                                           Numerology.gen_candidate_set()}

        # layer 0
        layer_index: int = 0
        for zone in zones[layer_index]:
            for ue in zone.ue_list:
                self.channel_model.sinr_ue(ue)
                AdjustMCS().from_highest_mcs(ue, ue.gnb_info.rb if nb_type == NodeBType.G else ue.enb_info.rb,
                                             self.channel_model)
                if nb_type == NodeBType.G:
                    self.marking_occupied_position(ue.gnb_info.rb, position)

        # layers above 0. (For gFrame only.)
        layer_index += 1
        for zones_in_layer in zones[layer_index:]:
            for zone in zones_in_layer:
                for ue in zone.ue_list:
                    assert ue.gnb_info, "The UE isn't allocated to gNB."
                    self.channel_model.sinr_ue(ue)
                    AdjustMCS().from_lapped_rb(ue, position[ue.numerology_in_use], self.channel_model)
                    self.marking_occupied_position(ue.gnb_info.rb, position)

        # FIXME: 受影響的UE還要調整，要重新統計position。留意是否有UE已被移除

    @staticmethod
    def marking_occupied_position(rb_list: List[ResourceBlock], position: Dict[Numerology, LappingPositionList]):
        for rb in rb_list:
            index = position[rb.numerology].exist([rb.i_start, rb.j_start, rb.numerology])
            if index is not None:
                position[rb.numerology][index].overlapping()
            else:
                position[rb.numerology].append(LappingPosition([rb.i_start, rb.j_start], rb.numerology))

    def allocate_new_ue(self, nb_type: NodeBType, ue_to_allocate: Tuple[UserEquipment],
                        allocated_ue: Tuple[UserEquipment], worsen_threshold: float = 0.0):
        nb: Union[GNodeB, ENodeB] = self.gnb if nb_type == NodeBType.G else self.enb
        unallocated_ue: List[UserEquipment] = list(ue_to_allocate)
        unallocated_next_round: List[UserEquipment] = []
        allocated_ue: List[UserEquipment] = list(allocated_ue)
        spaces: List[Space] = self.update_empty_space(nb)
        system_throughput: float = calc_system_throughput(tuple(allocated_ue))
        while (unallocated_ue or unallocated_next_round) and spaces:
            ue: UserEquipment = unallocated_ue.pop(0)
            is_allocated: bool = False
            for space in spaces:
                # from utils.assertion import check_undo_copy
                # copy_ue = check_undo_copy(ue_allocated)
                is_allocated: bool = self.allocate(ue, (space,), nb_type, allocated_ue, worsen_threshold)
                if is_allocated:
                    spaces: List[Space] = self.update_empty_space(nb)
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
                unallocated_ue: List[UserEquipment] = unallocated_next_round
                unallocated_next_round: List[UserEquipment] = []
                system_throughput: float = new_system_throughput

    @Undo.undo_func_decorator
    def allocate(self, ue: UserEquipment, spaces: Tuple[Space, ...], nb_type: NodeBType,
                 ue_allocated: List[UserEquipment], worsen_threshold: float) -> bool:
        # allocate new ue
        allocate_ue: AllocateUE = AllocateUE(ue, spaces, self.channel_model)
        is_allocated: bool = allocate_ue.allocate()
        self.append_undo(lambda a_u=allocate_ue: a_u.undo(), lambda a_u=allocate_ue: a_u.purge_undo())

        if is_allocated and ue.ue_type == UEType.D:
            dc: DualConnection = DualConnection(ue, self.channel_model)
            is_cut: bool = dc.cutting(ue.gnb_info if nb_type == NodeBType.G else ue.enb_info)
            if is_cut:
                self.append_undo(lambda d=dc: d.undo(), lambda d=dc: d.purge_undo())

        # the effected UEs
        if is_allocated:
            origin_sys_throughput: float = calc_system_throughput(tuple(ue_allocated))
            is_allocated: bool = self.adjust_mcs_allocated_ues([ue] + ue_allocated,
                                                               origin_sys_throughput, worsen_threshold)
        return is_allocated

    def adjust_mcs_allocated_ues(self, ue_allocated: List[UserEquipment],
                                 origin_sys_throughput, worsen_threshold) -> bool:
        self.assert_undo_function()
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
                    self.append_undo(lambda: self.channel_model.undo(), lambda: self.channel_model.purge_undo())
                    adjust_mcs: AdjustMCS = AdjustMCS()
                    is_fulfilled: bool = adjust_mcs.remove_worst_rb(ue, allow_lower_than_cqi0=False,
                                                                    channel_model=self.channel_model)
                    self.append_undo(lambda a_m=adjust_mcs: a_m.undo(), lambda a_m=adjust_mcs: a_m.purge_undo())
                    if not is_fulfilled:
                        # the mcs of the ue is lowered down by another UE.
                        return False
            if is_all_adjusted:
                return True

    @staticmethod
    def update_empty_space(nb: Union[GNodeB, ENodeB]) -> List[Space]:
        spaces: List[Space] = [space for layer in nb.frame.layer for space in empty_space(layer)]  # sort by layer
        spaces.sort(key=lambda s: s.starting_j)  # sort by time
        spaces.sort(key=lambda s: s.starting_i)  # sort by freq
        return spaces
