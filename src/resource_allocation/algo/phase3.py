import copy
import pickle
from typing import Dict, List, Optional, Tuple, Union

from hungarian_algorithm import algorithm

from src.channel_model.sinr import ChannelModel
from src.resource_allocation.algo.space import empty_space, Space
from src.resource_allocation.ds.cochannel import cochannel
from src.resource_allocation.ds.eutran import ENodeB
from src.resource_allocation.ds.frame import Layer
from src.resource_allocation.ds.ngran import GNodeB, GUserEquipment
from src.resource_allocation.ds.rb import ResourceBlock
from src.resource_allocation.ds.ue import UserEquipment
from src.resource_allocation.ds.util_enum import E_MCS, G_MCS, NodeBType, Numerology, UEType
from src.resource_allocation.ds.util_type import Coordinate


class Phase3:
    def __init__(self, channel_model: ChannelModel, gnb: GNodeB, enb: ENodeB,
                 ue_list_allocated: Tuple[Tuple[UserEquipment, ...], ...],
                 ue_list_unallocated: Tuple[Tuple[UserEquipment, ...], ...]):
        self.channel_model: ChannelModel = channel_model
        self.gnb: GNodeB = gnb
        self.enb: ENodeB = enb
        self.gue_allocated: List[UserEquipment, ...] = list(ue_list_allocated[0])
        self.gue_unallocated: List[UserEquipment, ...] = list(ue_list_unallocated[0])
        self.due_allocated: List[UserEquipment, ...] = list(ue_list_allocated[1])
        self.due_unallocated: List[UserEquipment, ...] = list(ue_list_unallocated[1])
        self.eue_allocated: List[UserEquipment, ...] = list(ue_list_allocated[2])
        self.eue_unallocated: List[UserEquipment, ...] = list(ue_list_unallocated[2])

        self.mcs_ordered: Tuple[Union[E_MCS, G_MCS], ...] = self.order_mcs()

    def increase_resource_efficiency(self):
        self.adjust_mcs_allocated_ues()

        for mcs in self.mcs_ordered:
            # find the UEs using this mcs
            ue_list: List[UserEquipment] = []
            if isinstance(mcs, E_MCS):
                for ue in self.due_allocated + self.eue_allocated:
                    if ue.enb_info.mcs is mcs:
                        ue_list.append(ue)
            elif isinstance(mcs, G_MCS):
                for ue in self.due_allocated + self.gue_allocated:
                    if ue.gnb_info.mcs is mcs:
                        ue_list.append(ue)
            if not ue_list:
                continue

            # find empty spaces
            gnb_empty_space: List[Space] = []
            for layer in self.gnb.frame.layer:
                gnb_empty_space.extend(empty_space(layer))
            gnb_empty_space: Tuple[Space] = tuple(gnb_empty_space)
            enb_empty_space: Tuple[Space] = empty_space(self.enb.frame.layer[0])

            # calculate the weight of ue to space
            graph: Dict[str, Dict[str, float]] = self.calc_weight(mcs, ue_list, gnb_empty_space, enb_empty_space)

            # bipartite matching
            match: List[Tuple[Tuple[str, str], float]] = self.matching(graph)

    def adjust_mcs_allocated_ues(self):
        while True:
            is_all_adjusted: bool = True
            for ue in self.gue_allocated + self.due_allocated + self.eue_allocated:
                if ue.is_to_recalculate_mcs:
                    is_all_adjusted: bool = False
                    self.channel_model.sinr_ue(ue)
                    self.adjust_mcs(ue)
            if is_all_adjusted:
                break

    def adjust_mcs(self, ue: UserEquipment, is_hungarian: bool = False):
        # TODO: 反向操作，先看SINR最好的RB需要幾個RB > 更新MCS > 再算一次需要幾個RB > 刪掉多餘SINR較差的RB (RB照freq time排序)
        if hasattr(ue, 'gnb_info'):
            ue.gnb_info.rb.sort(key=lambda x: x.sinr, reverse=True)
        if hasattr(ue, 'enb_info'):
            ue.enb_info.rb.sort(key=lambda x: x.sinr, reverse=True)

        while True:  # ue_throughput >= QoS
            # sum throughput
            ue_throughput: float = 0.0
            if hasattr(ue, 'gnb_info'):
                ue_throughput += self.throughput_ue(ue.gnb_info.rb)
            if hasattr(ue, 'enb_info'):
                ue_throughput += self.throughput_ue(ue.enb_info.rb)

            # Temporarily remove the RB with lowest data rate efficiency
            if ue.ue_type == UEType.D:
                if ue.gnb_info.rb:
                    worst_gnb_rb: ResourceBlock = ue.gnb_info.rb[-1]
                    worst_gnb_rb_eff: float = worst_gnb_rb.mcs.efficiency
                else:
                    worst_gnb_rb: Optional[ResourceBlock] = None
                    worst_gnb_rb_eff: float = 0.0
                if ue.enb_info.rb:
                    worst_enb_rb: ResourceBlock = ue.enb_info.rb[-1]
                    worst_enb_rb_eff: float = worst_enb_rb.mcs.efficiency
                else:
                    worst_enb_rb: Optional[ResourceBlock] = None
                    worst_enb_rb_eff: float = 0.0
                worst_rb: ResourceBlock = worst_gnb_rb if worst_gnb_rb_eff > worst_enb_rb_eff else worst_enb_rb
                if isinstance(worst_rb.mcs, G_MCS):
                    tmp_ue_throughput: float = self.throughput_ue(ue.gnb_info.rb[:-1]) + self.throughput_ue(
                        ue.enb_info.rb)
                elif isinstance(worst_rb.mcs, E_MCS):
                    tmp_ue_throughput: float = self.throughput_ue(ue.enb_info.rb[:-1]) + self.throughput_ue(
                        ue.gnb_info.rb)
                else:
                    raise AttributeError
            elif ue.ue_type == UEType.G:
                worst_rb: ResourceBlock = ue.gnb_info.rb[-1]
                tmp_ue_throughput: float = self.throughput_ue(ue.gnb_info.rb[:-1])
            elif ue.ue_type == UEType.E:
                worst_rb: ResourceBlock = ue.enb_info.rb[-1]
                tmp_ue_throughput: float = self.throughput_ue(ue.enb_info.rb[:-1])
            else:
                raise AttributeError

            if tmp_ue_throughput > ue.request_data_rate:
                # Officially remove the RB
                worst_rb.remove()
                continue
            elif ue_throughput >= ue.request_data_rate:
                # Update the MCS and throughput of the UE
                ue.throughput = ue_throughput
                if hasattr(ue, 'gnb_info'):
                    if ue.gnb_info.rb:
                        ue.gnb_info.mcs = ue.gnb_info.rb[-1].mcs
                    else:
                        ue.gnb_info.mcs = None
                if hasattr(ue, 'enb_info'):
                    if ue.enb_info.rb:
                        ue.enb_info.mcs = ue.enb_info.rb[-1].mcs
                    else:
                        ue.enb_info.mcs = None
                ue.is_to_recalculate_mcs = False
                break
            elif is_hungarian:
                # the temporarily moved UE has negative effected to this UE
                return False
            elif ue_throughput == 0.0:
                # if SINR is out of range, kick out this UE.
                ue.remove()
                if ue.ue_type == UEType.G:
                    self.gue_allocated.remove(ue)
                    self.gue_unallocated.append(ue)
                elif ue.ue_type == UEType.D:
                    self.due_allocated.remove(ue)
                    self.due_unallocated.append(ue)
                elif ue.ue_type == UEType.E:
                    self.eue_allocated.remove(ue)
                    self.eue_unallocated.append(ue)
                break
            else:
                raise ValueError

    def calc_weight(self, mcs: Union[E_MCS, G_MCS], ue_list: List[UserEquipment], gnb_spaces: Tuple[Space],
                    enb_spaces: Tuple[Space]) -> Dict[str, Dict[str, float]]:
        restore_nb_ue: RestoreNodebUE = RestoreNodebUE(self)

        weight: Dict[str, Dict[str, float]] = {}
        num_of_bu_origin: int = self.calc_num_bu(self.gue_allocated + self.due_allocated + self.eue_allocated)
        for ue in ue_list:
            weight[str(ue.uuid)] = {}
            for space in gnb_spaces + enb_spaces:
                is_to_try: bool = False
                if space.nb.nb_type == NodeBType.G and (ue.ue_type == UEType.G or ue.ue_type == UEType.D):
                    for numerology in space.numerology:
                        if ue.numerology_in_use is numerology:
                            # the size of the space is large enough for at least one RB of the numerology in use
                            is_to_try: bool = True
                            break
                        else:
                            continue
                elif space.nb.nb_type == NodeBType.E and (ue.ue_type == UEType.E or ue.ue_type == UEType.D):
                    """
                    Warning: LTE RBs are well aligned. 
                    If the RBs are properly placed one after another. 
                    It will naturally be aligned every 0.5 ms.
                    """
                    is_to_try: bool = True

                if is_to_try:
                    is_usable: bool = self.ue_to_space(ue, space, mcs)
                    if is_usable:
                        num_of_bu_new: int = self.calc_num_bu(
                            self.gue_allocated + self.due_allocated + self.eue_allocated)
                        weight[str(ue.uuid)][str(space.uuid)] = num_of_bu_origin - num_of_bu_new
                        assert weight[str(ue.uuid)][str(space.uuid)] >= 0, "There are UE getting lower mcs than before."
                restore_nb_ue.restore()
        return weight

    def ue_to_space(self, ue: UserEquipment, space: Space, mcs: Union[E_MCS, G_MCS]) -> bool:
        # the space can place at least one RB of the size(numerology/LTE) the UE is using
        bu_i: int = space.starting_i
        bu_j: int = space.starting_j
        while True:
            rb: Optional[ResourceBlock] = space.layer.allocate_resource_block(bu_i, bu_j, ue)
            if not rb:
                # UE overlapped with itself
                # the coordination of next RB
                if bu := space.next_rb(bu_i, bu_j, ue.numerology_in_use):
                    bu_i: int = bu[0]
                    bu_j: int = bu[1]
                    continue
                else:
                    # running out of space
                    return False

            self.channel_model.sinr_rb(rb)
            if rb.mcs.efficiency < (ue.gnb_info if isinstance(rb.mcs, G_MCS) else ue.enb_info).mcs.efficiency:
                # the mcs of new RB is lower than the mcs the UE is currently using
                rb.remove()
                # the coordination of next RB
                if bu := space.next_rb(bu_i, bu_j, ue.numerology_in_use):
                    bu_i: int = bu[0]
                    bu_j: int = bu[1]
                    continue
                else:
                    # running out of space
                    return False

            self.adjust_mcs(ue)
            if (ue.gnb_info if isinstance(mcs, G_MCS) else ue.enb_info).rb[-1].mcs.efficiency > mcs.efficiency:
                return self.effected_ue()

            # the coordination of next RB
            if bu := space.next_rb(bu_i, bu_j, ue.numerology_in_use):
                bu_i: int = bu[0]
                bu_j: int = bu[1]
            else:
                # running out of space
                return False

    def effected_ue(self) -> bool:
        while True:
            is_all_adjusted: bool = True
            for ue in self.gue_allocated + self.due_allocated + self.eue_allocated:
                if ue.is_to_recalculate_mcs:
                    is_all_adjusted: bool = False
                    self.channel_model.sinr_ue(ue)
                    if not self.adjust_mcs(ue, is_hungarian=True):
                        # the ue moving to the space lower down a original UEs' MCS
                        return False
            if is_all_adjusted:
                # the space is suitable for this ue
                return True

    @staticmethod
    def matching(graph) -> List[Tuple[Tuple[str, str], float]]:
        if len(graph) <= 1:
            # greedy
            max_weight: float = -1
            max_weight_space: str = ''
            output: List[Tuple[Tuple[str, str], float]] = []
            for ue in graph:
                for space in graph[ue]:
                    if graph[ue][space] > max_weight:
                        max_weight: float = graph[ue][space]
                        max_weight_space: str = space
                output: List[Tuple[Tuple[str, str], float]] = [((ue, max_weight_space), max_weight)]
        else:
            """
            Hungarian Algorithm: https://github.com/benchaplin/hungarian-algorithm
            Constraint in directed graph:
                1. The starting vertexes must be more than one.
                2. The starting vertexes and ending vertexes should not be the same.
            Tip:
                1. Do not input too many edges. Ignore the edge <= 0.
            """
            output: List[Tuple[Tuple[str, str], float]] = algorithm.find_matching(graph)
            if not output:  # return False
                raise ValueError
        return output

    @staticmethod
    def calc_num_bu(ue_list: List[UserEquipment]) -> int:
        # for weight
        num_of_bu: int = 0
        for ue in ue_list:
            if hasattr(ue, 'gnb_info'):
                num_of_bu += len(ue.gnb_info.rb) * 16
            if hasattr(ue, 'enb_info'):
                num_of_bu += len(ue.enb_info.rb) * 8
        return num_of_bu

    def calc_system_throughput(self) -> float:
        system_throughput: float = 0.0
        for ue in self.gue_allocated + self.due_allocated + self.eue_allocated:
            system_throughput += ue.throughput
        return system_throughput

    @staticmethod
    def order_mcs() -> Tuple[Union[E_MCS, G_MCS], ...]:
        mcs_list: List[List[Union[E_MCS, G_MCS], float]] = []
        for mcs in E_MCS:
            mcs_list.append([mcs, mcs.efficiency])
        for mcs in G_MCS:
            mcs_list.append([mcs, mcs.efficiency])
        mcs_list.sort(key=lambda x: x[1])

        ordered_mcs: List[Union[E_MCS, G_MCS]] = []
        for mcs in mcs_list:
            ordered_mcs.append(mcs[0])
        return tuple(ordered_mcs)

    @staticmethod
    def throughput_ue(rb_list: List[ResourceBlock]) -> float:
        if rb_list:
            lowest_mcs: Union[E_MCS, G_MCS] = rb_list[-1].mcs
            return lowest_mcs.value * len(rb_list)
        else:
            return 0.0


class RestoreNodebUE:
    def __init__(self, phase3: Phase3):
        self.phase3: Phase3 = phase3
        self._copy_gnb: GNodeB = copy.deepcopy(phase3.gnb)
        self._copy_enb: ENodeB = copy.deepcopy(phase3.enb)
        self._copy_g_allo: List[UserEquipment, ...] = copy.deepcopy(phase3.gue_allocated)
        self._copy_g_unallo: List[UserEquipment, ...] = copy.deepcopy(phase3.gue_unallocated)
        self._copy_d_allo: List[UserEquipment, ...] = copy.deepcopy(phase3.due_allocated)
        self._copy_d_unallo: List[UserEquipment, ...] = copy.deepcopy(phase3.due_unallocated)
        self._copy_e_allo: List[UserEquipment, ...] = copy.deepcopy(phase3.eue_allocated)
        self._copy_e_unallo: List[UserEquipment, ...] = copy.deepcopy(phase3.eue_unallocated)

    def restore(self):
        self.phase3.gnb = self._copy_gnb
        self.phase3.enb = self._copy_enb
        self.phase3.gue_allocated = self._copy_g_allo
        self.phase3.gue_unallocated = self._copy_g_unallo
        self.phase3.due_allocated = self._copy_d_allo
        self.phase3.due_unallocated = self._copy_d_unallo
        self.phase3.eue_allocated = self._copy_e_allo
        self.phase3.eue_unallocated = self._copy_e_unallo


if __name__ == '__main__':
    visualize_the_algo = True
    visualization_file_path = "../../../utils/frame_visualizer/vis_test_calc_weight"

    eNB: ENodeB = ENodeB(coordinate=Coordinate(0.0, 0.0), radius=0.5)
    gNB: GNodeB = GNodeB(coordinate=Coordinate(0.4, 0.0), radius=0.1)
    cochannel_index: Dict = cochannel(eNB, gNB)
    layer_e: Layer = eNB.frame.layer[0]
    layer_0: Layer = gNB.frame.layer[0]
    layer_1: Layer = gNB.frame.layer[1]
    layer_2: Layer = gNB.frame.layer[2]

    # GUE, N2
    gue_1: UserEquipment = GUserEquipment(820, [Numerology.N1, Numerology.N2], Coordinate(0.45, 0.0))
    gue_1.register_nb(eNB, gNB)
    gue_1.set_numerology(Numerology.N2)
    for i in range(0, 50, gue_1.numerology_in_use.freq):
        for j in range(0, gNB.frame.frame_time, gue_1.numerology_in_use.time):
            layer_0.allocate_resource_block(i, j, gue_1)

    # GUE, N2
    gue_2: UserEquipment = GUserEquipment(300, [Numerology.N1, Numerology.N2], Coordinate(0.5, 0.0))
    gue_2.register_nb(eNB, gNB)
    gue_2.set_numerology(Numerology.N2)
    for i in range(70, 120, gue_2.numerology_in_use.freq):
        for j in range(0, gNB.frame.frame_time, gue_2.numerology_in_use.time):
            layer_0.allocate_resource_block(i, j, gue_2)

    g_ue_list_allocated = (gue_1, gue_2)
    g_ue_list_unallocated = ()
    d_ue_list_allocated = ()
    d_ue_list_unallocated = ()
    e_ue_list_allocated = ()
    e_ue_list_unallocated = ()

    if visualize_the_algo:
        with open(visualization_file_path + ".P", "wb") as file:
            pickle.dump(["Phase3",
                         gNB.frame, eNB.frame, 0,
                         {"allocated": g_ue_list_allocated, "unallocated": g_ue_list_unallocated},
                         {"allocated": d_ue_list_allocated, "unallocated": d_ue_list_unallocated},
                         {"allocated": e_ue_list_allocated, "unallocated": e_ue_list_unallocated}],
                        file)

    cm = ChannelModel(cochannel_index)
    p3 = Phase3(cm, gNB, eNB, (g_ue_list_allocated, d_ue_list_allocated, e_ue_list_allocated),
                (g_ue_list_unallocated, d_ue_list_unallocated, e_ue_list_unallocated))
    p3.increase_resource_efficiency()
    # cm.sinr_ue(gue_1)
    # p3.adjust_mcs(gue_1)
    # cm.sinr_ue(gue_2)
    # p3.adjust_mcs(gue_2)
    # empty_space = empty_space(layer_2)
    # p3.calc_weight(G_MCS.CQI1_QPSK, [gue_1, gue_2], empty_space, ())

    if visualize_the_algo:
        with open(visualization_file_path + ".P", "ab+") as file:
            pickle.dump(["Phase3-space-efficiency",
                         gNB.frame, eNB.frame, 0,
                         {"allocated": g_ue_list_allocated, "unallocated": g_ue_list_unallocated},
                         {"allocated": d_ue_list_allocated, "unallocated": d_ue_list_unallocated},
                         {"allocated": e_ue_list_allocated, "unallocated": e_ue_list_unallocated}],
                        file)
