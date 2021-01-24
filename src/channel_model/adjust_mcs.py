from typing import List, Optional, Tuple, Union

from src.resource_allocation.ds.eutran import EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GUserEquipment
from src.resource_allocation.ds.nodeb import ENBInfo, GNBInfo
from src.resource_allocation.ds.rb import ResourceBlock
from src.resource_allocation.ds.ue import UserEquipment
from src.resource_allocation.ds.undo import Undo
from src.resource_allocation.ds.util_enum import E_MCS, G_MCS, UEType


class AdjustMCS(Undo):
    def __init__(self):
        super().__init__()

    def remove_worst_rb(self, ue: Union[UserEquipment, GUserEquipment, DUserEquipment, EUserEquipment],
                        allow_lower_mcs: bool = True) -> bool:
        """
        Delete the RB with worst MCS & highest freq & latest time.
        :param ue: The UE to adjust mcs. For UE with single or dual connection.
        :param allow_lower_mcs: If is "False", means a certain UEs' new movement has negative effect to this UE.
        :return: If the adjustment has succeed.
        """
        for nb_info in ['gnb_info', 'enb_info']:
            if hasattr(ue, nb_info):
                ue_nb_info: Union[GNBInfo, ENBInfo] = getattr(ue, nb_info)
                ue_nb_info.rb.sort(key=lambda x: x.j_start)  # sort by time
                ue_nb_info.rb.sort(key=lambda x: x.i_start)  # sort by freq
                ue_nb_info.rb.sort(key=lambda x: x.mcs.value, reverse=True)  # sort by mcs

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
                self.append_undo([lambda rb=worst_rb: rb.undo(), lambda rb=worst_rb: rb.purge_undo()])
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

    def remove_from_high_freq(self, ue: UserEquipment, ue_rb_list: List[ResourceBlock],
                              precalculate: bool = False) -> int:
        # how many RBs does the UE need?
        ue_rb_list.sort(key=lambda x: x.j_start)  # sort by time
        ue_rb_list.sort(key=lambda x: x.i_start)  # sort by freq
        return self.pick_in_order(ue, ue_rb_list, precalculate)

    def pick_in_overlapped_rb(self, ue: Union[UserEquipment, GUserEquipment, EUserEquipment],
                              rb_position: List[Tuple[int, int]]):
        """
        Use the RBs in certain positions. Unless the RBs are not enough to fulfill QoS.
        For gNB.
        :param ue: The UE to adjust mcs. The ue has single connection and request RBs in single layer.
        :param rb_position: The position of RBs to use in the first place.
        """
        # collect the overlapped RBs in ue
        non_lapped_rb: List[ResourceBlock] = []
        lapped_rb: List[ResourceBlock] = []
        is_lapped: bool = False
        for rb in ue.gnb_info.rb:
            for position in rb_position:
                if rb.i_start == position[0] and rb.j_start == position[1]:
                    is_lapped: bool = True
                    rb_position.remove(position)
                    break
            lapped_rb.append(rb) if is_lapped else non_lapped_rb.append(rb)

        # adjust mcs
        lapped_rb.sort(key=lambda x: x.j_start)  # sort by time
        lapped_rb.sort(key=lambda x: x.i_start)  # sort by freq
        lapped_rb.sort(key=lambda x: x.mcs.value, reverse=True)  # sort by mcs
        non_lapped_rb.sort(key=lambda x: x.j_start)  # sort by time
        non_lapped_rb.sort(key=lambda x: x.i_start)  # sort by freq
        non_lapped_rb.sort(key=lambda x: x.mcs.value, reverse=True)  # sort by mcs
        self.pick_in_order(ue, lapped_rb + non_lapped_rb)

    @staticmethod
    def pick_in_order(ue: UserEquipment, rb_list: List[ResourceBlock], precalculate: bool = False) -> int:
        """
        Delete the RB with highest freq & latest time.
        :param ue: The UE to adjust mcs. For UE with single connection.
        :param rb_list: The UEs' RBs in gnb_info or enb_info.
        :param precalculate: If is "True", don't remove or add RBs after knowing how many RBs to use.
        :return: The number of RB this ue needs.
        """
        current_mcs: Union[G_MCS, E_MCS] = rb_list[0].mcs
        i: int = 1
        while True:
            if current_mcs.efficiency == 0.0:  # CQI 0
                return 0 if precalculate else ue.remove()

            if i == current_mcs.calc_required_rb_count(ue.request_data_rate):
                # The current RBs can fulfill QoS
                if not precalculate:
                    # Remove the extra RBs
                    nb_info: Union[GNBInfo, ENBInfo] = ue.gnb_info if isinstance(current_mcs, G_MCS) else ue.enb_info
                    while len(rb_list) > i:
                        rb_list[-1].remove()
                        if nb_info.rb is not rb_list:
                            rb_list.pop()
                    ue.throughput = current_mcs.value * i
                    nb_info.mcs = current_mcs
                    ue.is_to_recalculate_mcs = False
                return i
            elif i > current_mcs.calc_required_rb_count(ue.request_data_rate):
                raise AssertionError    # need more RBs?

            # main
            for rb in rb_list[i:current_mcs.calc_required_rb_count(ue.request_data_rate)]:
                i += 1
                if rb.mcs.efficiency < current_mcs.efficiency:
                    current_mcs: Union[G_MCS, E_MCS] = rb.mcs
                    break
