import pickle
from datetime import datetime
from typing import Dict, List, Set, Tuple, Union

from src.channel_model.adjust_mcs import AdjustMCS
from src.channel_model.sinr import ChannelModel
from src.resource_allocation.algo.new_ue_allocation import AllocateUE
from src.resource_allocation.ds.eutran import ENodeB
from src.resource_allocation.ds.ngran import GNodeB
from src.resource_allocation.ds.space import empty_space, Space
from src.resource_allocation.ds.ue import UserEquipment
from src.resource_allocation.ds.undo import Undo
from src.resource_allocation.ds.util_enum import NodeBType
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
        # TODO: for dUE cross
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

    def allocate_new_ue(self, nb_type: NodeBType, ue_to_allocate: Tuple[UserEquipment],
                        ue_allocated: Tuple[UserEquipment]):
        nb: Union[GNodeB, ENodeB] = self.gnb if nb_type == NodeBType.G else self.enb
        ue_to_allocate: List[UserEquipment] = list(ue_to_allocate)
        ue_allocated: List[UserEquipment] = list(ue_allocated)

        spaces: List[Space] = [space for layer in nb.frame.layer for space in empty_space(layer)]

        while ue_to_allocate:
            ue: UserEquipment = ue_to_allocate.pop()
            ue_allocated.append(ue)
            is_allocated: bool = False
            for space in spaces:
                # allocate new ue
                allocate_ue: AllocateUE = AllocateUE(ue, (space,), self.channel_model)
                is_allocated: bool = allocate_ue.new_ue()  # TODO: for dUE
                self.append_undo([lambda a_u=allocate_ue: a_u.undo(), lambda a_u=allocate_ue: a_u.purge_undo()])

                # the effected UEs
                if is_allocated:
                    is_allocated: bool = self.adjust_mcs_allocated_ues(ue_allocated)

                if is_allocated:
                    spaces: List[Space] = [space for layer in nb.frame.layer for space in empty_space(layer)]
                    self.purge_undo()
                    break
                else:
                    self.undo()
            if not is_allocated:
                ue_allocated.remove(ue)

    def adjust_mcs_allocated_ues(self, ue_allocated: List[UserEquipment]) -> bool:
        while True:
            is_all_adjusted: bool = True
            for ue in ue_allocated:
                if ue.is_to_recalculate_mcs:
                    assert ue.is_allocated
                    is_all_adjusted: bool = False
                    self.channel_model.sinr_ue(ue)
                    self.append_undo(
                        [lambda c_m=self.channel_model: c_m.undo(), lambda c_m=self.channel_model: c_m.purge_undo()])
                    is_fulfilled: bool = self.adjust_mcs.remove_worst_rb(ue, allow_lower_than_cqi0=False,
                                                                         channel_model=self.channel_model)
                    self.append_undo(
                        [lambda a_m=self.adjust_mcs: a_m.undo(), lambda a_m=self.adjust_mcs: a_m.purge_undo()])
                    if not is_fulfilled:
                        # the mcs of the ue is lowered down by another UE.
                        return False
            if is_all_adjusted:
                return True

    def visualize(self, title):
        with open("../utils/frame_visualizer/vis_" + datetime.today().strftime('%Y%m%d') + ".P", "ab+") as f:
            pickle.dump([title,
                         self.gnb.frame, self.enb.frame,
                         0.0,
                         {"allocated": [], "unallocated": []},
                         {"allocated": [], "unallocated": []},
                         {"allocated": [], "unallocated": []}],
                        f)
