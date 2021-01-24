from typing import Dict, List, Set, Tuple

from src.channel_model.adjust_mcs import AdjustMCS
from src.channel_model.sinr import ChannelModel
from src.resource_allocation.ds.eutran import ENodeB
from src.resource_allocation.ds.ngran import GNodeB
from src.resource_allocation.ds.ue import UserEquipment
from src.resource_allocation.ds.undo import Undo
from src.resource_allocation.ds.zone import Zone, ZoneGroup


class Phase3(Undo):
    def __init__(self, channel_model: ChannelModel, gnb: GNodeB, enb: ENodeB):
        super().__init__()
        self.channel_model: ChannelModel = channel_model
        self.gnb: GNodeB = gnb
        self.enb: ENodeB = enb
        self.adjust_mcs = AdjustMCS()

    def zone_adjust_mcs(self, zones: Tuple[Zone, ...]):
        for zone in zones:
            for ue in zone.ue_list:
                self.channel_model.sinr_ue(ue)
                self.adjust_mcs.remove_worst_rb(ue)

    def zone_group_adjust_mcs(self, zone_groups: Tuple[ZoneGroup, ...]):
        for zone_group in zone_groups:
            # precalculate the number of RBs in each bin(layer)
            num_rb_needed: Dict = {}
            for b, bin_ in enumerate(zone_group.bin):
                num_rb_needed[b] = 0
                for zone in bin_.zone:
                    for ue in zone.ue_list:
                        self.channel_model.sinr_ue(ue)
                        num_rb_needed[b] += self.adjust_mcs.remove_from_high_freq(ue, ue.gnb_info.rb, precalculate=True)

            # find the bin(layer) that will need most RBs
            max_num_rb_bin_index: int = 0
            for bin_index in num_rb_needed:
                if num_rb_needed[bin_index] > num_rb_needed[max_num_rb_bin_index]:
                    max_num_rb_bin_index: int = bin_index

            # adjust the mcs for the UEs in the bin(layer) of max_num_rb_bin_index
            rb_position: List[Tuple[int, int]] = []
            ue_in_zone_group: List[UserEquipment] = []
            for zone in zone_group.bin[max_num_rb_bin_index].zone:
                for ue in zone.ue_list:
                    self.adjust_mcs.remove_from_high_freq(ue, ue.gnb_info.rb)
                    # record the RB indexes
                    for rb in ue.gnb_info.rb:
                        rb_position.append((rb.i_start, rb.j_start))
                    ue_in_zone_group.append(ue)

            # adjust the mcs for rest of the UEs with the restrict of overlapping the RBs in max_num_rb_bin_index
            rb_position_2nd: Set[Tuple[int, int]] = set()
            for b, bin_ in enumerate(zone_group.bin):
                if b == max_num_rb_bin_index:
                    continue
                for zone in bin_.zone:
                    for ue in zone.ue_list:
                        self.channel_model.sinr_ue(ue)
                        self.adjust_mcs.pick_in_overlapped_rb(ue, rb_position)
                        # record the RB indexes
                        for rb in ue.gnb_info.rb:
                            rb_position_2nd.add((rb.i_start, rb.j_start))
                        ue_in_zone_group.append(ue)

            # adjust the effected UEs. Start from the ue in max_num_rb_bin_index
            while True:
                is_all_adjusted: bool = True
                for ue in ue_in_zone_group:
                    if ue.is_to_recalculate_mcs:
                        is_all_adjusted: bool = False
                        self.channel_model.sinr_ue(ue)
                        self.adjust_mcs.pick_in_overlapped_rb(ue, list(rb_position_2nd))
                if is_all_adjusted:
                    break
