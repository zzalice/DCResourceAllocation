from typing import List, Optional, Tuple, Union

from src.channel_model.sinr import ChannelModel
from src.resource_allocation.ds.rb import ResourceBlock
from src.resource_allocation.ds.ue import UserEquipment
from src.resource_allocation.ds.util_enum import E_MCS, G_MCS, UEType


class Phase3:
    def __init__(self, ue_list_allocated: Tuple[UserEquipment], ue_list_unallocated: Tuple[UserEquipment]):
        self.ue_list_allocated: Tuple[UserEquipment] = ue_list_allocated
        self.ue_list_unallocated: Tuple[UserEquipment] = ue_list_unallocated

    def improve_system_throughput(self):
        for ue in self.ue_list_allocated:
            self.adjust_mcs(ue)

        # for mcs in E_MCS.__members__:
        #     # print('{:15} = {}'.format(mcs.name, mcs.value))
        #     is_improved: bool = True
        #     while is_improved:
        #         system_throughput: float = 0.0
        #         new_system_throughput: float = 0.0
        #         is_improved: bool = new_system_throughput > system_throughput

    def adjust_mcs(self, ue: UserEquipment):
        ChannelModel().sinr_ue(ue)

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
            else:
                assert ue_throughput >= ue.request_data_rate, "The number of RB a UE get isn't enough."
                # Update the MCS and throughput of the UE
                ue.throughput = ue_throughput
                if hasattr(ue, 'gnb_info'):
                    if ue.gnb_info.rb:
                        ue.gnb_info.update_mcs(ue.gnb_info.rb[-1].mcs)
                if hasattr(ue, 'enb_info'):
                    if ue.enb_info.rb:
                        ue.enb_info.update_mcs(ue.enb_info.rb[-1].mcs)
                break

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
