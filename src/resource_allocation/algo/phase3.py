from typing import Dict, List, Optional, Tuple, Union

from hungarian_algorithm import algorithm

from src.channel_model.sinr import ChannelModel
from src.resource_allocation.algo.space import empty_space, Space
from src.resource_allocation.ds.eutran import ENodeB
from src.resource_allocation.ds.ngran import GNodeB
from src.resource_allocation.ds.rb import ResourceBlock
from src.resource_allocation.ds.ue import UserEquipment
from src.resource_allocation.ds.util_enum import E_MCS, G_MCS, UEType


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

    def decrease_num_of_rb(self):
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
                    self.adjust_mcs(ue)
            if is_all_adjusted:
                break

    def adjust_mcs(self, ue: UserEquipment):
        # TODO: 反向操作，先看SINR最好的RB需要幾個RB > 更新MCS > 再算一次需要幾個RB > 刪掉多餘SINR較差的RB (RB照freq time排序)
        self.channel_model.sinr_ue(ue)

        while True:  # ue_throughput >= QoS
            # sum throughput
            ue_throughput: float = 0.0
            if hasattr(ue, 'gnb_info'):
                ue_throughput += self._throughput_ue(ue.gnb_info.rb)
            if hasattr(ue, 'enb_info'):
                ue_throughput += self._throughput_ue(ue.enb_info.rb)

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
                worst_rb_data_rate: float = worst_rb.mcs.value
            else:
                worst_rb: ResourceBlock = (ue.gnb_info if ue.ue_type == UEType.G else ue.enb_info).rb[-1]
                worst_rb_data_rate: float = worst_rb.mcs.value
            tmp_ue_throughput: float = ue_throughput - worst_rb_data_rate

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
                if hasattr(ue, 'enb_info'):
                    if ue.enb_info.rb:
                        ue.enb_info.mcs = ue.enb_info.rb[-1].mcs
                ue.is_to_recalculate_mcs = False
                break
            else:
                assert ue_throughput <= 0.0, "There's bug in this algorithm."
                # if SINR is out of range, kick out this UE and put in a new one.
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

    def calc_weight(self, mcs: Union[E_MCS, G_MCS], ue_list: List[UserEquipment], gnb_spaces: Tuple[Space],
                    enb_spaces: Tuple[Space]) -> Dict[str, Dict[str, float]]:
        for ue in ue_list:
            # fetch the index of the first RB with the mcs in the ue
            idx_rb: int = -1
            for i, rb in enumerate((ue.gnb_info if isinstance(mcs, G_MCS) else ue.enb_info).rb):
                if rb.mcs is mcs:
                    idx_rb: int = i
                    break

            if ue.ue_type == UEType.G or ue.ue_type == UEType.D:
                for space in gnb_spaces:
                    if ue.numerology_in_use in space.numerology:
                        # 每放一個RB，檢查mcs是否<目前(未搬移)，if <: continue，else
                        pass
            if ue.ue_type == UEType.E or ue.ue_type == UEType.D:
                for space in enb_spaces:
                    pass

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
        return output

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
    def _throughput_ue(rb_list: List[ResourceBlock]) -> float:
        if rb_list:
            lowest_mcs: Union[E_MCS, G_MCS] = rb_list[-1].mcs
            return lowest_mcs.value * len(rb_list)
        else:
            return 0.0
