from typing import List, Set, Tuple, Union

from src.channel_model.sinr import ChannelModel
from src.resource_allocation.algo.new_ue import AllocateUEList
from src.resource_allocation.algo.utils import sort_by_channel_quality
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.frame import BaseUnit
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.resource_allocation.ds.rb import ResourceBlock
from src.resource_allocation.ds.space import Space
from src.resource_allocation.ds.ue import UserEquipment
from src.resource_allocation.ds.util_enum import LTEResourceBlock, NodeBType, Numerology

UE = Union[UserEquipment, GUserEquipment, DUserEquipment, EUserEquipment]


class Intuitive(AllocateUEList):
    def __init__(self, nb: Union[GNodeB, ENodeB], ue_to_allocate: Tuple[UE, ...], allocated_ue: Tuple[UE, ...],
                 channel_model: ChannelModel):
        super().__init__(nb, (), allocated_ue, channel_model)
        self.ue_to_allocate: List[UE] = sort_by_channel_quality(list(ue_to_allocate), nb.nb_type)

    def allocate(self, allow_lower_mcs: bool = False, allow_lower_than_cqi0: bool = False):
        while self.ue_to_allocate:
            ue: UE = self.ue_to_allocate.pop(0)
            spaces: Tuple[Space, ...] = self.update_empty_space()
            is_allocated: bool = self._allocate(ue, spaces, allow_lower_mcs, allow_lower_than_cqi0)
            if is_allocated:
                self.allocated_ue.append(ue)
                self.purge_undo()
            else:
                self.undo()

    def update_empty_space(self) -> Tuple[Space, ...]:
        self.find_the_last_continuous_empty_bu()    # FIXME
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

    def find_the_last_continuous_empty_bu(self) -> Tuple[int, int, int]:
        # find the last occupied BU
        last_layer, last_freq, last_time = self.find_latest_bu()
        last_layer, last_freq, last_time = self.find_row_last_bu(last_layer, last_freq, last_time)
        last_freq_bound: int = self.find_row_end(last_layer, last_freq, last_time)

        # find the last continuous empty BU
        # FIXME
        return

    def find_latest_bu(self) -> Tuple[int, int, int]:
        last_layer: int = -1
        last_freq: int = -1
        last_time: int = -1
        for l in range(self.nb.frame.max_layer - 1, -1, -1):
            for f in range(self.nb.frame.frame_freq - 1, -1, -1):
                for t in range(self.nb.frame.frame_time - 1, -1, -1):
                    if self.nb.frame.layer[l].bu_status[f][t] is True:
                        last_layer: int = l
                        last_freq: int = f
                        last_time: int = t
                        break
        assert (0 <= last_layer < self.nb.frame.max_layer) and (0 <= last_freq < self.nb.frame.frame_freq) and (
                0 <= last_time < self.nb.frame.frame_time), 'Fail to find the last occupied BU.'
        return last_layer, last_freq, last_time

    def find_row_last_bu(self, layer: int, freq: int, time: int) -> Tuple[int, int, int]:
        last_rb: ResourceBlock = self.nb.frame.layer[layer].bu[freq][time].within_rb
        assert last_rb, 'Input a unused BU.'
        last_numerology: Union[Numerology, LTEResourceBlock] = last_rb.numerology
        row_start: int = freq - last_numerology.freq + 1
        assert self.nb.frame.layer[layer].bu_status[row_start][time], 'Algorithm error coming from input.'
        col_end: int = time
        for t in range(time + 1, self.nb.frame.frame_time):
            if self.nb.frame.layer[layer].bu_status[row_start][t] is True:
                col_end: int = t
        assert self.nb.frame.layer[layer].bu_status[row_start][col_end], 'Algorithm error.'
        return layer, row_start, col_end

    def find_row_end(self, layer: int, freq: int, time: int):
        assert self.nb.frame.layer[layer].bu_status[freq][time], 'Input a unused BU.'
        assert time == self.nb.frame.frame_time or self.nb.frame.layer[layer].bu_status[freq][
            time + 1] is False, 'No the last BU.'

        if self.nb.nb_type == NodeBType.E:
            return freq + LTEResourceBlock.freq - 1

        # collect the numerology of RBs in the same row.
        numerology_set: Set[Numerology] = set()
        is_upper_left: int = 0
        for t in range(time, -1, -1):
            bu: BaseUnit = self.nb.frame.layer[layer].bu[freq][t]
            assert bu.is_used, 'Algorithm error.'
            numerology_set.add(bu.within_rb.numerology)
            if bu.is_upper_left:
                is_upper_left += 1
        assert numerology_set, 'Algorithm error.'
        assert 0 < is_upper_left <= len(numerology_set), 'Input BU is not the start of a row of RB.'

        # find the longest RB
        longest_freq: int = -1
        for numerology in numerology_set:
            if numerology.freq > longest_freq:
                longest_freq: int = numerology.freq
        assert longest_freq > 0, 'Algorithm error.'
        return freq + longest_freq - 1
