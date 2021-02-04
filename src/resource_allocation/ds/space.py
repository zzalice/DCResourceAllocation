from __future__ import annotations

from typing import Dict, List, Optional, Tuple, Union
from uuid import UUID, uuid4

from src.resource_allocation.ds.frame import Layer
from src.resource_allocation.ds.util_enum import LTEResourceBlock, NodeBType, Numerology


class Space:
    def __init__(self, layer: Layer, starting_i: int, starting_j: int, ending_i: int, ending_j: int):
        assert ending_i >= starting_i and ending_j >= starting_j

        self.uuid: UUID = uuid4()
        self.layer: Layer = layer
        self.starting_i: int = starting_i
        self.starting_j: int = starting_j
        self.ending_i: int = ending_i
        self.ending_j: int = ending_j
        self._rb: Tuple[Tuple[Union[Numerology, LTEResourceBlock], int]] = self.possible_rb_type()

    def next_rb(self, bu_i: int, bu_j: int, rb_type: Union[Numerology, LTEResourceBlock]) -> Optional[Tuple[int, int]]:
        """
        Warning: LTE RBs are well aligned.
        If the RBs are properly placed one after another.
        It will naturally be aligned every 0.5 ms.
        """
        assert self.starting_i <= bu_i <= self.ending_i and self.starting_j <= bu_j <= self.ending_j
        return next_rb_in_space(bu_i, bu_j, rb_type, self.layer, self.starting_i, self.starting_j, self.ending_i,
                                self.ending_j)

    def possible_rb_type(self) -> Tuple[Tuple[Union[Numerology, LTEResourceBlock], int]]:
        available_rb_type: List[Tuple[Union[Numerology, LTEResourceBlock], int]] = []
        #                       Tuple[the type of RB that fits this space, the number of RBs can be placed in here]
        if self.layer.nodeb.nb_type == NodeBType.G:
            rb_types: List[Numerology] = [numerology for numerology in Numerology]
        else:
            rb_types: List[LTEResourceBlock] = [LTEResourceBlock.E]

        for rb_type in rb_types:
            num_rb_freq: int = self.height // rb_type.freq
            num_rb_time: int = self.width // rb_type.time
            num_rb: int = num_rb_freq * num_rb_time
            if num_rb:
                available_rb_type.append((rb_type, num_rb))

        return tuple(available_rb_type)

    def num_of_rb(self, rb_type: Union[Numerology, LTEResourceBlock]) -> int:
        for rb in self._rb:
            if rb_type is rb[0]:
                return rb[1]
        # TODO: return False

    @property
    def rb_type(self) -> List[Numerology]:
        rb_type: List[Numerology] = []
        for rb in self._rb:
            rb_type.append(rb[0])
        return rb_type

    @property
    def width(self) -> int:
        return self.ending_j - self.starting_j + 1

    @property
    def height(self) -> int:
        return self.ending_i - self.starting_i + 1

    def assert_is_empty(self):
        for i in range(self.starting_i, self.ending_i + 1):
            for j in range(self.starting_j, self.ending_j + 1):
                assert not self.layer.bu[i][j].is_used, "The space is not empty."


def empty_space(layer: Layer) -> Tuple[Space, ...]:
    # ref: https://hackmd.io/HaKC3jR5Q4KOcumGo8RvKQ?view
    spaces: List[Dict] = scan(layer)
    spaces: List[Dict] = merge(spaces)

    empty_spaces: List[Space] = []
    for space in spaces:
        s: Space = Space(layer, space['i_start'], space['j_start'], space['i_end'], space['j_end'])
        if not s.rb_type:   # if the space is too narrow to contain even one RB
            continue
        empty_spaces.append(s)
    return tuple(empty_spaces)


def scan(layer: Layer) -> List[Dict]:
    bu_status = layer.bu_status
    spaces: List[Dict] = []
    for i in range(layer.FREQ):
        tmp_space: Dict = {'i_start': i, 'j_start': -1, 'i_end': i, 'j_end': -1}
        for j in range(layer.TIME):
            if not bu_status[i][j]:  # is empty
                tmp_space['j_end'] = j
                if tmp_space['j_start'] == -1:
                    tmp_space['j_start'] = j
                if j == layer.TIME - 1:
                    spaces.append(tmp_space)
            elif tmp_space['j_start'] != -1:  # meet an allocated RB
                spaces.append(tmp_space)
                tmp_space: Dict = {'i_start': i, 'j_start': -1, 'i_end': i, 'j_end': -1}
    return spaces


def merge(spaces: List[Dict]) -> List[Dict]:
    merged_spaces: List[Dict] = []
    while spaces:
        space: Dict = spaces.pop(0)  # space to be merged
        i: int = 0
        while i < len(spaces):
            another_space: Dict = spaces[i]
            if (another_space['i_start'] == space['i_end'] + 1) and (another_space['j_start'] == space['j_start']) and (
                    another_space['j_end'] == space['j_end']):  # merge continuous and same width space
                space['i_end'] = another_space['i_end']  # merge
                spaces.remove(another_space)  # remove the merged space
            elif another_space['i_start'] > space['i_end'] + 1:
                # not possible to merge into a rectangle
                break
            else:
                i += 1
        merged_spaces.append(space)

    return merged_spaces


def next_rb_in_space(bu_starting_i: int, bu_starting_j: int, rb_type: Union[Numerology, LTEResourceBlock],
                     layer: Layer, space_starting_i: int, space_starting_j: int, space_ending_i: int,
                     space_ending_j: int
                     ) -> Optional[Tuple[int, int]]:
    assert 0 <= space_starting_i <= space_ending_i < layer.FREQ
    assert 0 <= space_starting_j <= space_ending_j < layer.TIME
    if layer.nodeb.nb_type == NodeBType.E:
        rb_type: LTEResourceBlock = LTEResourceBlock.E  # TODO: refactor or redesign

    # the position of next RB
    bu_starting_j += rb_type.time
    if bu_starting_j + rb_type.time - 1 > space_ending_j:
        # next row
        bu_starting_i += rb_type.freq
        bu_starting_j: int = space_starting_j
        if bu_starting_i + rb_type.freq - 1 > space_ending_i:
            return None  # running out of space

    # check if the space is empty
    for i in range(bu_starting_i, bu_starting_i + rb_type.freq):
        for j in range(bu_starting_j, bu_starting_j + rb_type.time):
            if layer.bu_status[i][j]:
                return None  # the space is occupied

    return bu_starting_i, bu_starting_j
