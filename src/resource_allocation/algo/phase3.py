from typing import Dict, List, Optional, Tuple, Union

from hungarian_algorithm import algorithm  # https://github.com/benchaplin/hungarian-algorithm

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

    def improve_system_throughput(self):
        # adjust the mcs of the UEs
        while True:
            is_all_adjusted: bool = True
            for ue in self.gue_allocated + self.eue_allocated + self.due_allocated:
                if ue.is_to_recalculate_mcs:
                    is_all_adjusted: bool = False
                    self.adjust_mcs(ue)
            if is_all_adjusted:
                break

        # find empty spaces
        gnb_empty_space: List[Space] = []
        for layer in self.gnb.frame.layer:
            gnb_empty_space.extend(empty_space(layer))
        enb_empty_space: List[Space] = []
        enb_empty_space.extend(empty_space(self.enb.frame.layer[0]))

        # G: Dict[Dict] = {
        #     'Ann': {'RB': 3, 'CAM': 2, 'GK': 1},
        #     'Ben': {'LW': 3, 'S': 2, 'CM': 1},
        #     'Cal': {'CAM': 3, 'RW': 2, 'SWP': 1},
        #     'Dan': {'S': 3, 'LW': 2, 'GK': 1},
        #     'Ela': {'GK': 3, 'LW': 2, 'F': 1},
        #     'Fae': {'CM': 3, 'GK': 2, 'CAM': 1},
        #     'Gio': {'GK': 3, 'CM': 2, 'S': 1},
        #     'Hol': {'CAM': 3, 'F': 2, 'SWP': 1},
        #     'Ian': {'S': 3, 'RW': 2, 'RB': 1},
        #     'Jon': {'F': 3, 'LW': 2, 'CB': 1},
        #     'Kay': {'GK': 3, 'RW': 2, 'LW': 1, 'LB': 0}
        # }
        # output: List[Tuple[Tuple[UserEquipment, Space], float]] = algorithm.find_matching(G, matching_type='max', return_type='list')

        # for mcs in E_MCS:
        #     # print('{:15} = {}'.format(mcs.name, mcs.value))
        #     is_improved: bool = True
        #     while is_improved:
        #         system_throughput: float = 0.0
        #         new_system_throughput: float = 0.0
        #         is_improved: bool = new_system_throughput > system_throughput

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
                    worst_gnb_rb_eff: float = self._mcs_efficiency(worst_gnb_rb.mcs)
                else:
                    worst_gnb_rb: Optional[ResourceBlock] = None
                    worst_gnb_rb_eff: float = 0.0
                if ue.enb_info.rb:
                    worst_enb_rb: ResourceBlock = ue.enb_info.rb[-1]
                    worst_enb_rb_eff: float = self._mcs_efficiency(worst_enb_rb.mcs)
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
                        ue.gnb_info.update_mcs(ue.gnb_info.rb[-1].mcs)
                if hasattr(ue, 'enb_info'):
                    if ue.enb_info.rb:
                        ue.enb_info.update_mcs(ue.enb_info.rb[-1].mcs)
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

    def calc_system_throughput(self) -> float:
        system_throughput: float = 0.0
        for ue in self.gue_allocated + self.due_allocated + self.eue_allocated:
            system_throughput += ue.throughput
        return system_throughput

    @staticmethod
    def _throughput_ue(rb_list: List[ResourceBlock]) -> float:
        if rb_list:
            lowest_mcs: Union[E_MCS, G_MCS] = rb_list[-1].mcs
            return lowest_mcs.value * len(rb_list)
        else:
            return 0.0

    @staticmethod
    def _mcs_efficiency(mcs: Union[E_MCS, G_MCS]) -> float:
        """
        The transmit efficiency of a LTE RB is always higher than NR RB.
        e.g. E_MCS.CQI1_QPSK * 2 > G_MCS.CQI1_QPSK
        In some cases, LTE RB is even one level higher than NR RB.
        e.g. E_MCS.CQI9_16QAM * 2 > G_MCS.CQI10_64QAM
        This is why we should calculate the efficiency of MCS.
        """
        if isinstance(mcs, G_MCS):
            return mcs.value / 16
        elif isinstance(mcs, E_MCS):
            return mcs.value / 8
