from typing import List, Tuple, Union

from src.channel_model.adjust_mcs import AdjustMCS
from src.channel_model.sinr import ChannelModel
from src.resource_allocation.algo.new_resource_allocation import AllocateUE
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.resource_allocation.ds.space import empty_space, Space
from src.resource_allocation.ds.ue import UserEquipment
from src.resource_allocation.ds.undo import Undo

UE = Union[UserEquipment, GUserEquipment, EUserEquipment, DUserEquipment]


class AllocateUEList(Undo):
    def __init__(self, nb: Union[GNodeB, ENodeB], ue_to_allocate: Tuple[UE], allocated_ue: Tuple[UE],
                 channel_model: ChannelModel):
        super().__init__()
        self.nb: Union[GNodeB, ENodeB] = nb
        self.ue_to_allocate: List[UE] = list(ue_to_allocate)
        self.allocated_ue: List[UE] = list(allocated_ue)  # including UEs in another BS(for co-channel area adjustment)
        self.channel_model: ChannelModel = channel_model

    def allocate(self, allow_lower_mcs: bool = True, allow_lower_than_cqi0: bool = True):
        spaces: Tuple[Space] = self.update_empty_space()
        while self.ue_to_allocate:
            ue: UE = self.ue_to_allocate.pop()
            for space in spaces:
                # from tests.assertion import check_undo_copy
                # copy_ue = check_undo_copy([ue] + self.gue_allocated + self.due_allocated + self.eue_allocated)
                is_allocated: bool = self._allocate(ue, (space,), allow_lower_mcs, allow_lower_than_cqi0)
                if is_allocated:
                    self.allocated_ue.append(ue)
                    spaces: Tuple[Space] = self.update_empty_space()
                    self.purge_undo()
                    break
                else:
                    self.undo()
                    # from tests.assertion import check_undo_compare
                    # check_undo_compare([ue] + self.gue_allocated + self.due_allocated + self.eue_allocated, copy_ue)
                # from tests.assertion import assert_is_empty
                # assert_is_empty(spaces, ue, is_allocated)

    @Undo.undo_func_decorator
    def _allocate(self, ue, spaces: Tuple[Space, ...], allow_lower_mcs, allow_lower_than_cqi0) -> bool:
        # allocate new ue
        allocate_ue: AllocateUE = AllocateUE(ue, spaces, self.channel_model)
        is_allocated: bool = allocate_ue.allocate()
        self.append_undo(lambda a_u=allocate_ue: a_u.undo(), lambda a_u=allocate_ue: a_u.purge_undo())

        # the effected UEs
        if is_allocated:
            has_positive_effect: bool = self.adjust_mcs_allocated_ues([ue] + self.allocated_ue,
                                                                      allow_lower_mcs, allow_lower_than_cqi0)
            if not has_positive_effect:
                is_allocated: bool = False
        return is_allocated

    def update_empty_space(self) -> Tuple[Space]:
        tmp_spaces: List[Space] = []
        for layer in self.nb.frame.layer:
            new_spaces: Tuple[Space] = empty_space(layer)
            tmp_spaces.extend(new_spaces)

            # break if there is a complete layer in tmp_space
            if len(new_spaces) == 1 and (
                    new_spaces[0].width == self.nb.frame.frame_time and new_spaces[0].height == self.nb.frame.frame_freq):
                break

        return tuple(tmp_spaces)

    def adjust_mcs_allocated_ues(self, allocated_ue: List[UE], allow_lower_mcs, allow_lower_than_cqi0) -> bool:
        self.assert_undo_function()
        while True:
            is_all_adjusted: bool = True
            for ue in allocated_ue:
                if ue.is_to_recalculate_mcs:
                    is_all_adjusted: bool = False
                    self.channel_model.sinr_ue(ue)
                    self.append_undo(lambda: self.channel_model.undo(), lambda: self.channel_model.purge_undo())

                    adjust_mcs: AdjustMCS = AdjustMCS()
                    if not allow_lower_mcs:
                        has_positive_effect: bool = adjust_mcs.remove_worst_rb(ue, allow_lower_mcs=False)
                    elif not allow_lower_than_cqi0:
                        has_positive_effect: bool = adjust_mcs.remove_worst_rb(ue, allow_lower_than_cqi0=False,
                                                                               channel_model=self.channel_model)
                    else:
                        has_positive_effect: bool = adjust_mcs.remove_worst_rb(ue)  # ue can be removed
                    self.append_undo(lambda a_m=adjust_mcs: a_m.undo(), lambda a_m=adjust_mcs: a_m.purge_undo())

                    if not has_positive_effect:
                        # the mcs of the ue is lowered down by another UE.
                        return False
            if is_all_adjusted:
                return True
