from typing import Dict, List, Tuple, Union

from src.channel_model.adjust_mcs import AdjustMCS
from src.channel_model.sinr import ChannelModel
from src.resource_allocation.algo.new_resource_allocation import AllocateUE
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.resource_allocation.ds.space import empty_space, Space
from src.resource_allocation.ds.ue import UserEquipment
from src.resource_allocation.ds.undo import Undo
from src.resource_allocation.ds.util_enum import NodeBType, UEType


class Intuitive(Undo):
    def __init__(self, gnb: GNodeB, enb: ENodeB, cochannel_index: Dict, gue: Tuple[GUserEquipment],
                 due: Tuple[DUserEquipment], eue: Tuple[EUserEquipment]):
        super().__init__()
        self.gnb: GNodeB = gnb
        self.enb: ENodeB = enb
        self.gues: List[GUserEquipment] = list(gue)
        self.dues: List[DUserEquipment] = list(due)
        self.eues: List[EUserEquipment] = list(eue)

        self.ue_gnb_to_allocate: List[Union[GUserEquipment, DUserEquipment]] = self.gues + self.dues
        self.ue_enb_to_allocate: List[Union[EUserEquipment, DUserEquipment]] = self.eues
        self.gue_allocated: List[GUserEquipment] = []
        self.due_allocated: List[DUserEquipment] = []
        self.eue_allocated: List[EUserEquipment] = []
        self.gue_fail: List[GUserEquipment] = []
        self.due_fail: List[DUserEquipment] = []
        self.eue_fail: List[EUserEquipment] = []

        self.channel_model: ChannelModel = ChannelModel(cochannel_index)

    def algorithm(self):
        # Do gNB allocation first, then eNB.
        self.resource_allocation(self.gnb.nb_type)
        self.ue_enb_to_allocate.extend(self.due_fail)
        self.due_fail: List[DUserEquipment] = []
        self.resource_allocation(self.enb.nb_type)

    def resource_allocation(self, nb_type: NodeBType):
        if nb_type == NodeBType.G:
            self.ue_gnb_to_allocate.sort(key=lambda x: x.coordinate.distance_gnb)
            ue_to_allocate: List[Union[GUserEquipment, DUserEquipment]] = self.ue_gnb_to_allocate
            nb: GNodeB = self.gnb
        else:
            self.ue_enb_to_allocate.sort(key=lambda x: x.coordinate.distance_enb)
            ue_to_allocate: List[Union[EUserEquipment, DUserEquipment]] = self.ue_enb_to_allocate
            nb: ENodeB = self.enb

        spaces: Tuple[Space] = self.update_empty_space(nb)

        while ue_to_allocate:
            ue: UserEquipment = ue_to_allocate.pop()
            is_allocated: bool = False
            for space in spaces:
                self.start_func_undo()
                # from tests.assertion import check_undo_copy
                # copy_ue = check_undo_copy([ue] + self.gue_allocated + self.due_allocated + self.eue_allocated)

                # allocate new ue
                allocate_ue: AllocateUE = AllocateUE(ue, (space,), self.channel_model)
                is_allocated: bool = allocate_ue.allocate()
                self.append_undo(lambda a_u=allocate_ue: a_u.undo(), lambda a_u=allocate_ue: a_u.purge_undo())

                # the effected UEs
                if is_allocated:
                    has_positive_effect: bool = self.adjust_mcs_allocated_ues(
                        [ue] + self.gue_allocated + self.due_allocated + self.eue_allocated, allow_lower_mcs=False)
                    if not has_positive_effect:
                        is_allocated: bool = False
                self.end_func_undo()

                if is_allocated:
                    spaces: Tuple[Space] = self.update_empty_space(nb)
                    self.purge_undo()
                    break
                else:
                    self.undo()
                    # from tests.assertion import check_undo_compare
                    # check_undo_compare([ue] + self.gue_allocated + self.due_allocated + self.eue_allocated, copy_ue)

                # from tests.assertion import assert_is_empty
                # assert_is_empty(spaces, ue, is_allocated)

            if ue.ue_type == UEType.G:
                (self.gue_allocated if is_allocated else self.gue_fail).append(ue)
            elif ue.ue_type == UEType.D:
                (self.due_allocated if is_allocated else self.due_fail).append(ue)
            elif ue.ue_type == UEType.E:
                (self.eue_allocated if is_allocated else self.eue_fail).append(ue)
            else:
                raise AssertionError

    @staticmethod
    def update_empty_space(nb: Union[GNodeB, ENodeB]) -> Tuple[Space]:
        tmp_spaces: List[Space] = []
        for layer in nb.frame.layer:
            new_spaces: Tuple[Space] = empty_space(layer)
            tmp_spaces.extend(new_spaces)

            # break if there is a complete layer in tmp_space
            if len(new_spaces) == 1 and (
                    new_spaces[0].width == nb.frame.frame_time and new_spaces[0].height == nb.frame.frame_freq):
                break

        return tuple(tmp_spaces)

    def adjust_mcs_allocated_ues(self, allocated_ue: List[UserEquipment], allow_lower_mcs) -> bool:
        self.assert_undo_function()
        while True:
            is_all_adjusted: bool = True
            for ue in allocated_ue:
                if ue.is_to_recalculate_mcs:
                    is_all_adjusted: bool = False
                    self.channel_model.sinr_ue(ue)
                    self.append_undo(lambda: self.channel_model.undo(), lambda: self.channel_model.purge_undo())
                    adjust_mcs: AdjustMCS = AdjustMCS()
                    has_positive_effect: bool = adjust_mcs.remove_worst_rb(ue, allow_lower_mcs)
                    self.append_undo(lambda a_m=adjust_mcs: a_m.undo(), lambda a_m=adjust_mcs: a_m.purge_undo())
                    if not has_positive_effect:
                        # the mcs of the ue is lowered down by another UE.
                        return False
            if is_all_adjusted:
                return True
