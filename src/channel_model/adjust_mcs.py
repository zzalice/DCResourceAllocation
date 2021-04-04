from typing import List, Optional, Union

from src.channel_model.sinr import ChannelModel
from src.resource_allocation.algo.new_resource_allocation import NewResource
from src.resource_allocation.ds.eutran import EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GUserEquipment
from src.resource_allocation.ds.nodeb import ENBInfo, GNBInfo
from src.resource_allocation.ds.rb import ResourceBlock
from src.resource_allocation.ds.ue import UserEquipment
from src.resource_allocation.ds.undo import Undo
from src.resource_allocation.ds.util_enum import E_MCS, G_MCS, NodeBType, UEType
from src.resource_allocation.ds.util_type import LappingPositionList

UE = Union[UserEquipment, GUserEquipment, DUserEquipment, EUserEquipment]


class AdjustMCS(Undo):
    def __init__(self):
        super().__init__()

    @Undo.undo_func_decorator
    def remove_worst_rb(self, ue: UE, allow_lower_mcs: bool = True, allow_lower_than_cqi0: bool = True,
                        channel_model: ChannelModel = None) -> bool:
        """
        Delete the RB with worst MCS & highest freq & latest time.

        !!! To adjust mcs for the first time !!!
        allow_lower_mcs = True

        !!! After adding a certain new UE !!! (and this ue is effected)
        allow_lower_than_cqi0 = False and
        channel_model is to be given
        [or]
        allow_lower_mcs = False

        :param ue: The UE to adjust mcs. For UE with single or dual connection.
        :param allow_lower_mcs: If is "False", means
                                not allowing a certain UEs' new movement has negative effect to this UE.
        :param allow_lower_than_cqi0: If is "False", means a certain new UE can let this ue have lower mcs
                                      but CANNOT let it be too low to transmit.
        :param channel_model: If the algorithm allows the ue to add more RBs, channel_model will have to be passed in.
        :return: If the adjustment has succeed.
        """
        assert (allow_lower_than_cqi0 is False and channel_model is not None) or (
                allow_lower_than_cqi0 is True and channel_model is None)
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
                raise AssertionError

            if tmp_ue_throughput > ue.request_data_rate:
                # Officially remove the RB
                self.append_undo(lambda b=worst_rb: b.undo(), lambda b=worst_rb: b.purge_undo())
                worst_rb.remove_rb()
                continue
            elif ue_throughput >= ue.request_data_rate:
                # Update the UE
                # update MCS
                for nb_info in ['gnb_info', 'enb_info']:
                    if hasattr(ue, nb_info):
                        ue_nb_info: Union[GNBInfo, ENBInfo] = getattr(ue, nb_info)
                        self.append_undo(lambda n_i=ue_nb_info, origin=ue_nb_info.mcs: setattr(n_i, 'mcs', origin))
                        if ue_nb_info.rb:
                            ue_nb_info.mcs = ue_nb_info.rb[-1].mcs
                        else:
                            ue_nb_info.mcs = None

                # update throughput
                self.append_undo(lambda origin=ue.throughput: setattr(ue, 'throughput', origin))
                ue.update_throughput()

                self.append_undo(lambda origin=ue.is_to_recalculate_mcs: setattr(ue, 'is_to_recalculate_mcs', origin))
                ue.is_to_recalculate_mcs = False
                return True
            elif not allow_lower_mcs:
                # the temporarily moved UE has negative effected to this UE
                return False
            elif ue_throughput == 0.0:
                if allow_lower_than_cqi0:
                    # if SINR is out of range, kick out this UE.
                    # Happens only in the MCS adjust for the first time in my Algo, so doesn't have to undo.
                    ue.remove_ue()
                    return True
                else:
                    # Happens when allocating new UE
                    return False
            else:
                # add a new RB
                # Happens when allocating new UE
                new_resource = NewResource()
                rb: Union[ResourceBlock, bool] = new_resource.add_one_continuous_rb(ue, channel_model)
                if rb:
                    self.append_undo(lambda nr=new_resource: nr.undo(), lambda nr=new_resource: nr.purge_undo())
                else:
                    return False
                (ue.gnb_info if rb.layer.nodeb.nb_type == NodeBType.G else ue.enb_info).rb.sort(
                    key=lambda x: x.mcs.value, reverse=True)

    @staticmethod
    def throughput_ue(rb_list: List[ResourceBlock]) -> float:
        if rb_list:
            lowest_mcs: Union[E_MCS, G_MCS] = min(rb_list, key=lambda rb: rb.mcs.value).mcs
            return lowest_mcs.value * len(rb_list)
        else:
            return 0.0

    # def from_lowest_freq(self, ue: UE, ue_rb_list: List[ResourceBlock], channel_model: ChannelModel,
    #                      precalculate: bool = False) -> int:
    #     ue_rb_list.sort(key=lambda x: x.j_start)  # sort by time
    #     ue_rb_list.sort(key=lambda x: x.i_start)  # sort by freq
    #     return self.pick_in_order(ue, ue_rb_list, channel_model, precalculate)

    def from_highest_mcs(self, ue: UE, ue_rb_list: List[ResourceBlock], channel_model: ChannelModel):
        ue_rb_list.sort(key=lambda x: x.mcs.value, reverse=True)
        return self.pick_in_order(ue, ue_rb_list, channel_model)

    def from_lapped_rb(self, ue: UE, rb_position: LappingPositionList, channel_model: ChannelModel):
        """
        Use the RBs in certain positions. Unless the RBs are not enough to fulfill QoS.
        FOR gNB ONLY.
        :param ue: The UE to adjust mcs. The ue has SINGLE CONNECTION and request RBs in single layer.
        :param rb_position: The position of RBs to use in the first place.
        :param channel_model: For adding new RBs if the MCS is lower than the old one.
        """
        # Use the RB with highest overlap times
        rb_position.sort(key=lambda x: x.j_start, reverse=True)  # sort by time
        rb_position.sort(key=lambda x: x.i_start, reverse=True)  # sort by freq
        rb_position.sort(key=lambda x: x.time, reverse=True)

        # collect the overlapped RBs in ue
        lapped_rb: List[ResourceBlock] = []
        for position in rb_position:
            for rb in ue.gnb_info.rb:
                if rb.i_start == position.i_start and rb.j_start == position.j_start:
                    lapped_rb.append(rb)
                    break
        non_lapped_rb: List[ResourceBlock] = []
        for rb in ue.gnb_info.rb:
            if rb not in lapped_rb:
                non_lapped_rb.append(rb)

        non_lapped_rb.sort(key=lambda x: x.j_start)  # sort by time
        non_lapped_rb.sort(key=lambda x: x.i_start)  # sort by freq
        self.pick_in_order(ue, lapped_rb + non_lapped_rb, channel_model)

    @staticmethod
    def pick_in_order(ue: UE, rb_list: List[ResourceBlock], channel_model: ChannelModel) -> int:
        """
        Delete the RB with highest freq & latest time.
        Only get better MCS or remove(CQI 0).
        Undo not implemented, no need.
        :param ue: The UE to adjust mcs. For UE with SINGLE CONNECTION and had a number of RBs calculated by CQI_1
        :param rb_list: The UEs' RBs in gnb_info or enb_info.
        :param channel_model: For adding new RBs.
        :return: The number of RB this ue needs.
        """
        assert rb_list, 'Input empty list.'

        count_rb: int = 0
        pointer: int = 0
        first_time: bool = True
        current_mcs: Optional[G_MCS, E_MCS] = None
        nb_info: Optional[GNBInfo, ENBInfo] = None
        qos_fulfilled: bool = False
        for rb in rb_list[pointer:]:
            if first_time:
                first_time: bool = False
                current_mcs: Union[G_MCS, E_MCS] = rb.mcs
                nb_info: Union[GNBInfo, ENBInfo] = ue.gnb_info if isinstance(current_mcs, G_MCS) else ue.enb_info

            if rb.mcs.efficiency == 0.0 or qos_fulfilled:
                rb.remove_rb()
                if nb_info.rb is not rb_list:
                    rb_list.remove(rb)
            else:
                count_rb += 1
                if rb.mcs.efficiency < current_mcs.efficiency or current_mcs.efficiency == 0.0:
                    current_mcs: Union[G_MCS, E_MCS] = rb.mcs
                if count_rb == current_mcs.calc_required_rb_count(ue.request_data_rate):
                    qos_fulfilled: bool = True
                pointer += 1

        if qos_fulfilled:
            assert count_rb == len(nb_info.rb)
            nb_info.mcs = current_mcs
            ue.update_throughput()
            ue.is_to_recalculate_mcs = False
            return count_rb
        elif count_rb == 0 and pointer == len(rb_list):
            # the RBs in rb_list are all CQI 0
            ue.remove_ue()
            return count_rb
        elif count_rb < current_mcs.calc_required_rb_count(ue.request_data_rate):
            # need more RBs
            for _ in range(count_rb, current_mcs.calc_required_rb_count(ue.request_data_rate)):
                # add continuous RBs
                if NewResource().add_one_continuous_rb(ue, channel_model):
                    count_rb += 1
                else:  # no continuous empty space or ue overlapped with itself or the MCS of new RB is out of range
                    ue.remove_ue()
                    return 0
            return count_rb
        else:
            raise AssertionError

    def remove_from_tail(self, ue: UE, nb_info: Union[GNBInfo, ENBInfo]):
        """For single connection UE."""
        assert ue.is_allocated and not ue.cross_nb if ue.ue_type == UEType.D else ue.is_allocated
        nb_info.rb.sort(key=lambda x: x.j_start)  # sort by time
        nb_info.rb.sort(key=lambda x: x.i_start)  # sort by freq
        if self.throughput_ue(nb_info.rb) == 0.0:
            ue.remove_ue()
            return True
        else:
            while True:
                tmp_ue_throughput: float = self.throughput_ue(nb_info.rb[:-1])  # temporarily remove one RB
                if tmp_ue_throughput >= ue.request_data_rate:
                    nb_info.rb[-1].remove_rb()
                elif self.throughput_ue(nb_info.rb) >= ue.request_data_rate:
                    nb_info.mcs = min(nb_info.rb, key=lambda rb: rb.mcs.value).mcs
                    ue.update_throughput()
                    ue.is_to_recalculate_mcs = False
                    return True
                else:
                    raise AssertionError
