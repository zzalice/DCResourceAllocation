from typing import Dict, List, Tuple, Union

from src.channel_model.adjust_mcs import AdjustMCS
from src.channel_model.sinr import ChannelModel
from src.resource_allocation.algo.new_ue_allocation import AllocateUE
from src.resource_allocation.ds.eutran import ENodeB
from src.resource_allocation.ds.ngran import GNodeB
from src.resource_allocation.ds.rb import ResourceBlock
from src.resource_allocation.ds.space import empty_space, Space
from src.resource_allocation.ds.ue import UserEquipment
from src.resource_allocation.ds.undo import Undo
from src.resource_allocation.ds.util_enum import NodeBType, Numerology
from src.resource_allocation.ds.util_type import LappingPosition, LappingPositionList
from src.resource_allocation.ds.zone import Zone


class Phase3(Undo):
    def __init__(self, channel_model: ChannelModel, gnb: GNodeB, enb: ENodeB):
        super().__init__()
        self.gnb: GNodeB = gnb
        self.enb: ENodeB = enb
        self.channel_model: ChannelModel = channel_model
        self.adjust_mcs = AdjustMCS()

    def phase2_ue_adjust_mcs(self, nb_type: NodeBType, zones: List[List[Zone]]):
        """
        Adjust the MCS of the allocated UEs in Phase 2.
        :param nb_type: Adjust the MCS of the UEs in this BS.
        :param zones: The zones in each layer.
        """
        position: Dict[Numerology, LappingPositionList] = {numerology: LappingPositionList() for numerology in
                                                           Numerology.gen_candidate_set()}

        # layer 0
        layer_index: int = 0
        for zone in zones[layer_index]:
            for ue in zone.ue_list:
                self.channel_model.sinr_ue(ue)
                self.adjust_mcs.from_highest_mcs(ue, ue.gnb_info.rb if nb_type == NodeBType.G else ue.enb_info.rb,
                                                 self.channel_model)
                if nb_type == NodeBType.G:
                    self.marking_occupied_position(ue.gnb_info.rb, position)

        # layers above 0. (For gFrame only.)
        layer_index += 1
        for zones_in_layer in zones[layer_index:]:
            for zone in zones_in_layer:
                for ue in zone.ue_list:
                    assert ue.gnb_info, "The UE isn't allocated to gNB."
                    self.channel_model.sinr_ue(ue)
                    self.adjust_mcs.from_lapped_rb(ue, position[ue.numerology_in_use], self.channel_model)
                    self.marking_occupied_position(ue.gnb_info.rb, position)

        # purge undo
        # TODO: some lambda isn't cleared. Might be in RBs. 把RB和BU的Undo都加入Layer, adjust_mcs, 或channelModel的purge stack
        for layer in (self.gnb if nb_type == NodeBType.G else self.enb).frame.layer:
            layer.purge_undo()
            for i in range(layer.FREQ):
                for j in range(layer.TIME):
                    layer.bu[i][j].purge_undo()
        self.channel_model.purge_undo()
        self.adjust_mcs.purge_undo()

    @staticmethod
    def marking_occupied_position(rb_list: List[ResourceBlock], position: Dict[Numerology, LappingPositionList]):
        for rb in rb_list:
            index = position[rb.numerology].exist([rb.i_start, rb.j_start, rb.numerology])
            if index is not None:
                position[rb.numerology][index].overlapping()
            else:
                position[rb.numerology].append(LappingPosition([rb.i_start, rb.j_start], rb.numerology))

    def allocate_new_ue(self, nb_type: NodeBType, ue_to_allocate: Tuple[UserEquipment],
                        ue_allocated: Tuple[UserEquipment]):
        nb: Union[GNodeB, ENodeB] = self.gnb if nb_type == NodeBType.G else self.enb
        ue_to_allocate: List[UserEquipment] = list(ue_to_allocate)
        ue_allocated: List[UserEquipment] = list(ue_allocated)

        spaces: List[Space] = self.update_empty_space(nb)

        while ue_to_allocate:
            ue: UserEquipment = ue_to_allocate.pop()
            ue_allocated.append(ue)
            is_allocated: bool = False
            for space in spaces:
                # allocate new ue
                allocate_ue: AllocateUE = AllocateUE(ue, ue.request_data_rate, (space,), self.channel_model)
                is_allocated: bool = allocate_ue.allocate()  # TODO: for dUE
                self.append_undo([lambda a_u=allocate_ue: a_u.undo(), lambda a_u=allocate_ue: a_u.purge_undo()])

                # the effected UEs
                if is_allocated:
                    is_allocated: bool = self.adjust_mcs_allocated_ues(ue_allocated)
                    self.append_undo([lambda: self.channel_model.undo(), lambda: self.channel_model.purge_undo()])
                    self.append_undo([lambda: self.adjust_mcs.undo(), lambda: self.adjust_mcs.purge_undo()])

                if is_allocated:
                    spaces: List[Space] = self.update_empty_space(nb)
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
                    is_fulfilled: bool = self.adjust_mcs.remove_worst_rb(ue, allow_lower_than_cqi0=False,
                                                                         channel_model=self.channel_model)
                    if not is_fulfilled:
                        # the mcs of the ue is lowered down by another UE.
                        return False
            if is_all_adjusted:
                return True

    @staticmethod
    def update_empty_space(nb: Union[GNodeB, ENodeB]) -> List[Space]:
        spaces: List[Space] = [space for layer in nb.frame.layer for space in empty_space(layer)]  # sort by layer
        spaces.sort(key=lambda s: s.starting_j)  # sort by time
        spaces.sort(key=lambda s: s.starting_i)  # sort by freq
        return spaces
