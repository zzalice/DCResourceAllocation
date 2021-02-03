from typing import List, Optional, Tuple, Union

from src.channel_model.sinr import ChannelModel
from src.resource_allocation.algo.max_subarray import MaxSubarray
from src.resource_allocation.algo.new_ue_allocation import AllocateUE
from src.resource_allocation.ds.eutran import EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GUserEquipment
from src.resource_allocation.ds.nodeb import ENBInfo, GNBInfo
from src.resource_allocation.ds.rb import ResourceBlock
from src.resource_allocation.ds.space import empty_space, next_rb_in_space, Space
from src.resource_allocation.ds.ue import UserEquipment
from src.resource_allocation.ds.undo import Undo
from src.resource_allocation.ds.util_enum import E_MCS, G_MCS, NodeBType, UEType


class AdjustMCS(Undo):
    def __init__(self):
        super().__init__()

    def remove_worst_rb(self, ue: Union[UserEquipment, GUserEquipment, DUserEquipment, EUserEquipment],
                        allow_lower_mcs: bool = True, allow_lower_than_cqi0: bool = True,
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
                self.append_undo([lambda b=worst_rb: b.undo(), lambda b=worst_rb: b.purge_undo()])
                worst_rb.remove()
                continue
            elif ue_throughput >= ue.request_data_rate:
                # Update the UE
                # update MCS
                for nb_info in ['gnb_info', 'enb_info']:
                    if hasattr(ue, nb_info):
                        ue_nb_info: Union[GNBInfo, ENBInfo] = getattr(ue, nb_info)
                        origin_mcs: Optional[G_MCS, E_MCS] = ue_nb_info.mcs
                        if ue_nb_info.rb:
                            ue_nb_info.mcs = ue_nb_info.rb[-1].mcs
                        else:
                            ue_nb_info.mcs = None
                        self.append_undo([lambda n_i=ue_nb_info, m=origin_mcs: setattr(n_i, 'mcs', m)])

                # update throughput
                origin_throughput: float = ue.throughput
                ue.update_throughput()
                self.append_undo([lambda: setattr(ue, 'throughput', origin_throughput)])

                origin_recalc: bool = ue.is_to_recalculate_mcs
                ue.is_to_recalculate_mcs = False
                self.append_undo([lambda: setattr(ue, 'is_to_recalculate_mcs', origin_recalc)])
                return True
            elif not allow_lower_mcs:
                # the temporarily moved UE has negative effected to this UE
                return False
            elif ue_throughput == 0.0:
                if allow_lower_than_cqi0:
                    # if SINR is out of range, kick out this UE.
                    # Happens only in the MCS adjust for the first time in my Algo, so doesn't have to undo.
                    ue.remove()
                    return True
                else:
                    # Happens when allocating new UE
                    return False
            else:
                # add a new RB
                # Happens when allocating new UE
                rb: Union[ResourceBlock, bool] = self.add_one_rb(ue, channel_model)
                if rb is False:
                    return False

    def add_one_rb(self, ue: UserEquipment, channel_model: ChannelModel) -> Union[ResourceBlock, bool]:
        # the RB in highest frequency and latest time in a frame
        last_rb_gnb: Optional[ResourceBlock] = None
        last_rb_enb: Optional[ResourceBlock] = None
        last_rb: Optional[ResourceBlock] = None
        if hasattr(ue, 'gnb_info'):
            last_rb_gnb: Optional[ResourceBlock] = self.highest_freq_rb(ue.gnb_info.rb)
        if hasattr(ue, 'enb_info'):
            last_rb_enb: Optional[ResourceBlock] = self.highest_freq_rb(ue.enb_info.rb)
        if last_rb_gnb and last_rb_enb:
            # pick the one with higher efficiency
            last_rb: ResourceBlock = last_rb_gnb if last_rb_gnb.mcs.efficiency > last_rb_enb.mcs.efficiency else last_rb_enb
        elif last_rb_gnb:
            last_rb: ResourceBlock = last_rb_gnb
        elif last_rb_enb:
            last_rb: ResourceBlock = last_rb_enb
        else:
            assert last_rb_gnb is not None or last_rb_enb is not None, "The UE isn't allocated."

        # check if there is empty space for one RB after the last_rb
        next_rb: Optional[Tuple[int, int]] = next_rb_in_space(last_rb.i_start, last_rb.j_start, ue.numerology_in_use,
                                                              last_rb.layer, 0, 0, last_rb.layer.FREQ,
                                                              last_rb.layer.TIME)
        if next_rb is None:  # no continuous space for another RB. run out of space.
            return False

        # allocate a RB in the space
        new_rb: Optional[ResourceBlock] = last_rb.layer.allocate_resource_block(next_rb[0], next_rb[1], ue)
        if new_rb is None:  # allocation failed
            return False
        self.append_undo([lambda l=new_rb.layer: l.undo(), lambda l=new_rb.layer: l.purge_undo()])

        # the SINR of the new RB
        assert channel_model is not None, "Channel model isn't passed in to add a new RB."
        channel_model.sinr_rb(new_rb)
        self.append_undo([lambda: channel_model.undo(), lambda: channel_model.purge_undo()])
        (ue.gnb_info if new_rb.layer.nodeb.nb_type == NodeBType.G else ue.enb_info).rb.sort(key=lambda x: x.mcs.value,
                                                                                            reverse=True)
        return new_rb

    @staticmethod
    def throughput_ue(rb_list: List[ResourceBlock]) -> float:
        if rb_list:
            lowest_mcs: Union[E_MCS, G_MCS] = rb_list[-1].mcs
            return lowest_mcs.value * len(rb_list)
        else:
            return 0.0

    @staticmethod
    def highest_freq_rb(rb_list: List[ResourceBlock]) -> Optional[ResourceBlock]:
        if not rb_list:
            return None
        last_rb: ResourceBlock = rb_list[0]
        for rb in rb_list[1:]:
            if rb.i_start > last_rb.i_start or (rb.i_start == last_rb.i_start and rb.j_start > last_rb.j_start):
                # higher frequency or later time
                last_rb: ResourceBlock = rb
        return last_rb

    def remove_from_high_freq(self, ue: UserEquipment, ue_rb_list: List[ResourceBlock], channel_model: ChannelModel,
                              precalculate: bool = False) -> int:
        ue_rb_list.sort(key=lambda x: x.j_start)  # sort by time
        ue_rb_list.sort(key=lambda x: x.i_start)  # sort by freq
        return self.pick_in_order(ue, ue_rb_list, channel_model, precalculate)

    # def pick_in_overlapped_rb(self, ue: Union[UserEquipment, GUserEquipment, EUserEquipment],
    #                           rb_position: List[Tuple[int, int]], channel_model: ChannelModel):
    #     """
    #     Use the RBs in certain positions. Unless the RBs are not enough to fulfill QoS.
    #     For gNB.
    #     :param ue: The UE to adjust mcs. The ue has SINGLE CONNECTION and request RBs in single layer.
    #     :param rb_position: The position of RBs to use in the first place.
    #     :param channel_model: For add new RBs if the MCS is lower than the old one.
    #     """
    #     # collect the overlapped RBs in ue
    #     non_lapped_rb: List[ResourceBlock] = []
    #     lapped_rb: List[ResourceBlock] = []
    #     is_lapped: bool = False
    #     for rb in ue.gnb_info.rb:
    #         for position in rb_position:
    #             if rb.i_start == position[0] and rb.j_start == position[1]:
    #                 is_lapped: bool = True
    #                 break
    #         lapped_rb.append(rb) if is_lapped else non_lapped_rb.append(rb)
    #
    #     # adjust mcs
    #     lapped_rb.sort(key=lambda x: x.j_start)  # sort by time
    #     lapped_rb.sort(key=lambda x: x.i_start)  # sort by freq
    #     lapped_rb.sort(key=lambda x: x.mcs.value, reverse=True)  # sort by mcs
    #     non_lapped_rb.sort(key=lambda x: x.j_start)  # sort by time
    #     non_lapped_rb.sort(key=lambda x: x.i_start)  # sort by freq
    #     self.pick_in_order(ue, lapped_rb + non_lapped_rb, channel_model)

    def pick_in_order(self, ue: UserEquipment, rb_list: List[ResourceBlock], channel_model: ChannelModel,
                      precalculate: bool = False) -> int:
        """
        Delete the RB with highest freq & latest time.
        Only get better MCS or remove(CQI 0).
        Undo not implemented, no need.
        :param ue: The UE to adjust mcs. For UE with SINGLE CONNECTION and had a number of RBs calculated by CQI_1
        :param rb_list: The UEs' RBs in gnb_info or enb_info.
        :param channel_model: For adding new RBs.
        :param precalculate: If is "True", don't actually remove the ue or add RBs.
        :return: The number of RB this ue needs.
        """
        current_mcs: Union[G_MCS, E_MCS] = rb_list[0].mcs
        nb_info: Union[GNBInfo, ENBInfo] = ue.gnb_info if isinstance(current_mcs, G_MCS) else ue.enb_info
        i: int = 1
        while True:
            if current_mcs.efficiency == 0.0:  # CQI 0
                return 0 if precalculate else ue.remove()

            if i == current_mcs.calc_required_rb_count(ue.request_data_rate):
                # The current RBs can fulfill QoS
                if not precalculate:
                    # Remove the extra RBs
                    while len(rb_list) > i:
                        rb_list[-1].remove()  # call the remove method in rb.py
                        if nb_info.rb is not rb_list:
                            # if rb_list is a combination of lists, not "the" nb_info in ue.
                            # else the RB will be removed from rb_list at the remove() in rb.py
                            rb_list.pop()
                    nb_info.mcs = current_mcs
                    ue.update_throughput()
                    ue.is_to_recalculate_mcs = False
                return i
            elif i == len(rb_list) and i < current_mcs.calc_required_rb_count(ue.request_data_rate):
                # need more RBs (why is mcs lower than the last round? May be caused by the random of seed in sinr.py)
                for _ in range(i, current_mcs.calc_required_rb_count(ue.request_data_rate)):
                    if rb := self.add_one_rb(ue, channel_model):
                        if nb_info.rb is not rb_list:
                            rb_list.append(rb)
                    else:  # no continuous empty space or ue overlapped with itself(unlikely)
                        raise AssertionError
            elif i >= len(rb_list):
                raise AssertionError

            # main
            for rb in rb_list[i:current_mcs.calc_required_rb_count(ue.request_data_rate)]:
                i += 1
                if rb.mcs.efficiency < current_mcs.efficiency:
                    current_mcs: Union[G_MCS, E_MCS] = rb.mcs
                    break

    def due_cutting(self, ue: DUserEquipment, ue_nb_info: Union[GNBInfo, ENBInfo], channel_model: ChannelModel) -> bool:
        # TODO: debug
        assert ue.ue_type == UEType.D
        self.purge_undo()

        # crop the RBs with lower MCS
        ue_nb_info.rb.sort(key=lambda x: x.j_start)  # sort by time
        ue_nb_info.rb.sort(key=lambda x: x.i_start)  # sort by freq
        ue_nb_info.rb.sort(key=lambda x: x.layer.layer_index)  # sort by layer
        rm_from, rm_to, new_mcs = MaxSubarray().max_subarray([rb.mcs for rb in ue_nb_info.rb])
        if rm_from == rm_to:
            # no cutting
            return True
        for _ in range(rm_to - rm_from):
            self.append_undo([lambda rb=ue_nb_info.rb[rm_from]: rb.undo(), lambda rb=ue_nb_info.rb[rm_from]: rb.purge_undo()])
            ue_nb_info.rb[rm_from].remove()
        self.append_undo([lambda: setattr(ue_nb_info, 'mcs', ue_nb_info.mcs)])
        ue_nb_info.mcs = new_mcs
        new_throughput: float = ue_nb_info.mcs.value * len(ue_nb_info.rb)

        # find spaces in another BS to fulfill QoS
        another_nb_info: Union[GNBInfo, ENBInfo] = ue.enb_info if isinstance(ue_nb_info, GNBInfo) else ue.gnb_info
        spaces: List[Space] = [space for layer in another_nb_info.nb.frame.layer for space in empty_space(layer)]

        # add new RBs
        allocate_ue = AllocateUE(ue, ue.request_data_rate - new_throughput, tuple(spaces), channel_model)
        is_succeed: bool = allocate_ue.allocate()
        self.append_undo([lambda: allocate_ue.undo(), lambda: allocate_ue.purge_undo()])
        # TODO: if the MCS is higher than cqi-left/right

        if not is_succeed:
            self.undo()
        else:
            self.purge_undo()
        return True
