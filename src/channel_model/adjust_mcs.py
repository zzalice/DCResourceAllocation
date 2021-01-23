from typing import List, Optional, Union

from src.channel_model.sinr import ChannelModel
from src.resource_allocation.ds.eutran import EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GUserEquipment
from src.resource_allocation.ds.nodeb import ENBInfo, GNBInfo
from src.resource_allocation.ds.rb import ResourceBlock
from src.resource_allocation.ds.ue import UserEquipment
from src.resource_allocation.ds.undo import Undo
from src.resource_allocation.ds.util_enum import E_MCS, G_MCS, UEType


class AdjustMCS(Undo):
    def __init__(self, channel_model: ChannelModel,
                 gue_allocated: List[GUserEquipment], gue_unallocated: List[GUserEquipment],
                 due_allocated: List[DUserEquipment], due_unallocated: List[DUserEquipment],
                 eue_allocated: List[EUserEquipment], eue_unallocated: List[EUserEquipment]):
        super().__init__()
        self.channel_model: ChannelModel = channel_model
        self.gue_allocated: List[GUserEquipment] = gue_allocated
        self.gue_unallocated: List[GUserEquipment] = gue_unallocated
        self.due_allocated: List[DUserEquipment] = due_allocated
        self.due_unallocated: List[DUserEquipment] = due_unallocated
        self.eue_allocated: List[EUserEquipment] = eue_allocated
        self.eue_unallocated: List[EUserEquipment] = eue_unallocated

    def adjust_mcs_allocated_ues(self, allow_lower_mcs: bool = True) -> bool:
        while True:
            is_all_adjusted: bool = True
            for ue in self.gue_allocated + self.due_allocated + self.eue_allocated:
                if ue.is_to_recalculate_mcs:
                    is_all_adjusted: bool = False
                    self.channel_model.sinr_ue(ue)
                    self.append_undo(
                        [lambda c_m=self.channel_model: c_m.undo(), lambda c_m=self.channel_model: c_m.purge_undo()])
                    has_positive_effect: bool = self.adjust(ue, allow_lower_mcs)
                    if not has_positive_effect:
                        # the mcs of the ue is lowered down by another UE.
                        return False
            if is_all_adjusted:
                return True

    def adjust(self, ue: Union[UserEquipment, GUserEquipment, DUserEquipment, EUserEquipment],
               allow_lower_mcs: bool = True) -> bool:
        # TODO: 反向操作，先看SINR最好的RB需要幾個RB > 更新MCS > 再算一次需要幾個RB > 刪掉多餘SINR較差的RB (RB照freq time排序)
        if hasattr(ue, 'gnb_info'):
            ue.gnb_info.rb.sort(key=lambda x: x.sinr, reverse=True)  # TODO: sort by MCS，又依照i,j排序，才不會讓空間很零碎。但是phase 3 calc_weight時可能會刪掉index大的RB
            self.append_undo([lambda: ue.gnb_info.rb.sort(key=lambda x: x.sinr, reverse=True)])
        if hasattr(ue, 'enb_info'):
            ue.enb_info.rb.sort(key=lambda x: x.sinr, reverse=True)
            self.append_undo([lambda: ue.enb_info.rb.sort(key=lambda x: x.sinr, reverse=True)])

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
                    worst_gnb_rb_eff: float = float("inf")
                if ue.enb_info.rb:
                    worst_enb_rb: ResourceBlock = ue.enb_info.rb[-1]
                    worst_enb_rb_eff: float = worst_enb_rb.mcs.efficiency
                else:
                    worst_enb_rb: Optional[ResourceBlock] = None
                    worst_enb_rb_eff: float = float("inf")
                worst_rb: ResourceBlock = worst_gnb_rb if worst_gnb_rb_eff < worst_enb_rb_eff else worst_enb_rb
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
                self.append_undo([lambda rb=worst_rb: rb.undo(), lambda rb=worst_rb:rb.purge_undo()])
                continue
            elif ue_throughput >= ue.request_data_rate:
                # Update the MCS and throughput of the UE
                origin_throughput: float = ue.throughput
                ue.throughput = ue_throughput
                self.append_undo([lambda u=ue: setattr(u, 'throughput', origin_throughput)])

                # update MCS
                for nb_info in ['gnb_info', 'enb_info']:
                    if hasattr(ue, nb_info):
                        ue_nb_info: Union[GNBInfo, ENBInfo] = getattr(ue, nb_info)
                        origin_mcs: Optional[G_MCS, E_MCS] = ue_nb_info.mcs
                        if ue_nb_info.rb:
                            ue_nb_info.mcs = ue_nb_info.rb[-1].mcs
                        else:
                            ue_nb_info.mcs = None
                        self.append_undo([lambda n_i=ue_nb_info: setattr(n_i, 'mcs', origin_mcs)])

                ue.is_to_recalculate_mcs = False
                return True
            elif not allow_lower_mcs:
                # the temporarily moved UE has negative effected to this UE
                return False
            elif ue_throughput == 0.0:
                # if SINR is out of range, kick out this UE.
                # Happens only in the MCS adjust for the first time in my Algo, so doesn't have to undo.
                ue.remove()
                if ue.ue_type == UEType.G:      # TODO: 刪？不然loop會出問題
                    self.gue_allocated.remove(ue)
                    self.gue_unallocated.append(ue)
                elif ue.ue_type == UEType.D:
                    self.due_allocated.remove(ue)
                    self.due_unallocated.append(ue)
                elif ue.ue_type == UEType.E:
                    self.eue_allocated.remove(ue)
                    self.eue_unallocated.append(ue)
                return True
            else:
                raise ValueError

    @staticmethod
    def throughput_ue(rb_list: List[ResourceBlock]) -> float:
        if rb_list:
            lowest_mcs: Union[E_MCS, G_MCS] = rb_list[-1].mcs
            return lowest_mcs.value * len(rb_list)
        else:
            return 0.0
