from typing import List, Optional, Tuple, Union

from src.channel_model.sinr import ChannelModel
from src.resource_allocation.algo.new_ue import AllocateUEList
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.resource_allocation.ds.space import empty_space, Space
from src.resource_allocation.ds.ue import UserEquipment
from src.resource_allocation.ds.util_enum import NodeBType

UE = Union[UserEquipment, GUserEquipment, DUserEquipment, EUserEquipment]


class Intuitive(AllocateUEList):
    def __init__(self, nb: Union[GNodeB, ENodeB], ue_to_allocate: Tuple[UE, ...], allocated_ue: Tuple[UE, ...],
                 channel_model: ChannelModel):
        # sort by channel quality
        if nb.nb_type == NodeBType.G:
            ue_to_allocate: List[UE] = sorted(ue_to_allocate, key=lambda x: x.coordinate.distance_gnb)
        elif nb.nb_type == NodeBType.E:
            ue_to_allocate: List[UE] = sorted(ue_to_allocate, key=lambda x: x.coordinate.distance_enb)
        else:
            raise AssertionError
        super().__init__(
            nb=nb, ue_to_allocate=tuple(ue_to_allocate), allocated_ue=allocated_ue, channel_model=channel_model)

    @staticmethod
    def update_empty_space(nb: Union[GNodeB, ENodeB]):
        spaces: List[Space] = []
        for layer in nb.frame.layer:
            new_spaces: Tuple[Space] = empty_space(layer)

            # break if there is a complete layer in tmp_space
            if len(new_spaces) == 1 and (
                    new_spaces[0].width == nb.frame.frame_time and new_spaces[0].height == nb.frame.frame_freq):
                spaces.extend(new_spaces)
                break

            # find a space at the end of the frame  FIXME: mark the row and column
            space_at_bottom: Optional[Space] = next(
                (s for s in new_spaces if (
                        s.width == nb.frame.frame_time) and (s.ending_i == nb.frame.frame_freq - 1)),
                None)

            if space_at_bottom:
                # find a space above space_at_bottom
                space_above_bottom: Optional[Space] = next(
                    (s for s in new_spaces if (
                            s.ending_j == nb.frame.frame_time - 1) and (
                                 s.ending_i == space_at_bottom.starting_i - 1)),
                    None)
            else:
                # find a space at the end of the frame
                space_above_bottom: Optional[Space] = next(
                    (s for s in new_spaces if (
                            s.ending_j == nb.frame.frame_time - 1) and (
                                 s.ending_i == nb.frame.frame_freq - 1)),
                    None)

            # gather the spaces
            spaces.append(space_above_bottom) if space_above_bottom else None
            spaces.append(space_at_bottom) if space_at_bottom else None
        return tuple(spaces)
