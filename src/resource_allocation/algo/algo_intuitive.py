from typing import List, Tuple, Union

from src.channel_model.sinr import ChannelModel
from src.resource_allocation.algo.utils import sort_by_channel_quality
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.resource_allocation.ds.space import Space
from src.resource_allocation.ds.ue import UserEquipment
from src.resource_allocation.ds.undo import Undo

UE = Union[UserEquipment, GUserEquipment, DUserEquipment, EUserEquipment]


class Intuitive(Undo):
    def __init__(self, nb: Union[GNodeB, ENodeB], ue_to_allocate: Tuple[UE, ...], allocated_ue: Tuple[UE, ...],
                 channel_model: ChannelModel):
        super().__init__()
        self.nb: Union[GNodeB, ENodeB] = nb
        self.ue_to_allocate: List[UE] = sort_by_channel_quality(list(ue_to_allocate), nb.nb_type)
        self.unallocated_ue: List[UE] = []
        self.allocated_ue: List[UE] = list(allocated_ue)
        self.channel_model: ChannelModel = channel_model

    def allocate(self, allow_lower_mcs: bool = False):
        while self.unallocated_ue:
            ue: UE = self.unallocated_ue.pop(0)
            spaces: Tuple[Space, ...] = self.update_empty_space()
            is_allocated: bool = self._allocate(ue, spaces, allow_lower_mcs)
            if is_allocated:
                self.allocated_ue.append(ue)
                self.purge_undo()
                break
            else:
                self.unallocated_ue.append(ue)
                self.undo()

    def _allocate(self, ue: UE, spaces: Tuple[Space, ...], allow_lower_mcs: bool) -> bool:
        pass

    def update_empty_space(self) -> Tuple[Space, ...]:
        pass
        # spaces: List[Space] = []
        # for layer in self.nb.frame.layer:
        #     new_spaces: Tuple[Space] = empty_space(layer)
        #
        #     # break if there is a complete layer in tmp_space
        #     if len(new_spaces) == 1 and (
        #             new_spaces[0].width == self.nb.frame.frame_time and new_spaces[0].height == self.nb.frame.frame_freq):
        #         spaces.extend(new_spaces)
        #         break
        #
        #     # find a space at the end of the frame  FIXME: mark the row and column
        #     space_at_bottom: Optional[Space] = next(
        #         (s for s in new_spaces if (
        #                 s.width == self.nb.frame.frame_time) and (s.ending_i == self.nb.frame.frame_freq - 1)),
        #         None)
        #
        #     if space_at_bottom:
        #         # find a space above space_at_bottom
        #         space_above_bottom: Optional[Space] = next(
        #             (s for s in new_spaces if (
        #                     s.ending_j == self.nb.frame.frame_time - 1) and (
        #                          s.ending_i == space_at_bottom.starting_i - 1)),
        #             None)
        #     else:
        #         # find a space at the end of the frame
        #         space_above_bottom: Optional[Space] = next(
        #             (s for s in new_spaces if (
        #                     s.ending_j == self.nb.frame.frame_time - 1) and (
        #                          s.ending_i == self.nb.frame.frame_freq - 1)),
        #             None)
        #
        #     # gather the spaces
        #     spaces.append(space_above_bottom) if space_above_bottom else None
        #     spaces.append(space_at_bottom) if space_at_bottom else None
        # return tuple(spaces)
