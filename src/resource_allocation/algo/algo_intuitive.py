from typing import List, Optional, Set, Tuple, Union

from src.channel_model.sinr import ChannelModel
from src.resource_allocation.algo.new_ue import AllocateUEList
from src.resource_allocation.algo.utils import sort_by_channel_quality
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.frame import BaseUnit
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.resource_allocation.ds.rb import ResourceBlock
from src.resource_allocation.ds.space import empty_space, Space
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
        # find the last occupied BU
        last_layer, last_freq_up_bound, last_time = self.find_row_last_bu()

        if last_layer == last_freq_up_bound == last_time == -1:  # empty NB
            spaces: List[Space] = [Space(layer, 0, 0, self.nb.frame.frame_freq - 1, self.nb.frame.frame_time - 1) for
                                   layer in self.nb.frame.layer]
            for space in spaces:
                space.assert_is_empty()
            return tuple(spaces)

        last_freq_low_bound: int = self.find_row_lower_bound(last_layer, last_freq_up_bound, last_time)

        # find a small space to continue to allocate
        if space_para := self.find_next_space_start_bu(last_layer, last_freq_up_bound, last_time, last_freq_low_bound):
            bu_layer: int = space_para[0]
            bu_freq: int = space_para[1]
            bu_time: int = space_para[2]
            if bu_time != 0:
                first_space: Space = Space(
                    self.nb.frame.layer[bu_layer], bu_freq, bu_time, last_freq_low_bound, self.nb.frame.frame_time - 1)
                first_space.assert_is_empty()
                spaces: List[Space] = [first_space]
            else:
                spaces: List[Space] = []
        else:  # run out of space
            return tuple()
        assert (len(spaces) == 1 and spaces[0].width < self.nb.frame.frame_time) or (
                len(spaces) == 0), 'Should be a space smaller than frame time.'

        # find other large spaces
        assert 0 <= bu_layer < self.nb.frame.max_layer
        for l in range(bu_layer, self.nb.frame.max_layer):
            new_spaces: Tuple[Space, ...] = empty_space(self.nb.frame.layer[l])

            # find a space at the end of the frame
            space_at_bottom: Optional[Space] = next(
                (s for s in new_spaces if (
                        s.width == self.nb.frame.frame_time) and (s.ending_i == self.nb.frame.frame_freq - 1)),
                None)
            if space_at_bottom:
                if l == bu_layer and spaces:  # found a small space earlier
                    assert space_at_bottom.starting_i - 1 == spaces[0].ending_i, 'Algorithm error'
                elif l != bu_layer:
                    assert space_at_bottom.starting_i == space_at_bottom.starting_j == 0, 'Algorithm error'
                spaces.append(space_at_bottom)
        return tuple(spaces)

    def find_next_space_start_bu(self, last_layer: int, last_freq: int, last_time: int, last_freq_low_bound: int
                                 ) -> Optional[Tuple[int, int, int]]:
        assert 0 <= last_layer < self.nb.frame.max_layer
        assert 0 <= last_freq <= last_freq_low_bound < self.nb.frame.frame_freq
        assert 0 <= last_time < self.nb.frame.frame_time
        first_bu_layer: int = last_layer
        first_bu_freq: int = last_freq
        first_bu_time: int = last_time + 1
        if first_bu_time >= self.nb.frame.frame_time:
            # next row
            first_bu_time: int = 0
            first_bu_freq += last_freq_low_bound
            if first_bu_freq >= self.nb.frame.frame_freq:
                first_bu_layer += 1
                first_bu_freq: int = 0
                first_bu_time: int = 0
                if first_bu_layer >= self.nb.frame.max_layer:
                    return None  # run out of space
        return first_bu_layer, first_bu_freq, first_bu_time

    def find_row_last_bu(self) -> Tuple[int, int, int]:
        layer, freq, time = self.find_latest_bu()
        if layer == freq == time == -1:
            # empty NB
            return -1, -1, -1

        last_rb: ResourceBlock = self.nb.frame.layer[layer].bu[freq][time].within_rb
        assert last_rb, 'A unused BU.'

        last_numerology: Union[Numerology, LTEResourceBlock] = last_rb.numerology
        row_start: int = freq - last_numerology.freq + 1
        assert self.nb.frame.layer[layer].bu_status[row_start][time], 'Algorithm error.'
        col_end: int = time
        for t in range(time + 1, self.nb.frame.frame_time):
            if self.nb.frame.layer[layer].bu_status[row_start][t] is True:
                col_end: int = t
        assert self.nb.frame.layer[layer].bu_status[row_start][col_end], 'Algorithm error.'
        return layer, row_start, col_end

    def find_latest_bu(self) -> Tuple[int, int, int]:
        for l in range(self.nb.frame.max_layer - 1, -1, -1):
            for f in range(self.nb.frame.frame_freq - 1, -1, -1):
                for t in range(self.nb.frame.frame_time - 1, -1, -1):
                    if self.nb.frame.layer[l].bu_status[f][t] is True:
                        return l, f, t
        return -1, -1, -1   # empty NB

    def find_row_lower_bound(self, layer: int, freq: int, time: int):
        assert self.nb.frame.layer[layer].bu_status[freq][time], 'Input a unused BU.'
        assert time == self.nb.frame.frame_time - 1 or self.nb.frame.layer[layer].bu_status[freq][
            time + 1] is False, 'No the last BU.'

        if self.nb.nb_type == NodeBType.E:
            return freq + LTEResourceBlock.E.freq - 1

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
        assert len(numerology_set) <= is_upper_left, 'Input BU is not the start of a row of RB.'

        # find the longest RB
        longest_freq: int = -1
        for numerology in numerology_set:
            if numerology.freq > longest_freq:
                longest_freq: int = numerology.freq
        assert longest_freq > 0, 'Algorithm error.'
        return freq + longest_freq - 1
