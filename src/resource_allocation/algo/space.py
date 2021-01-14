from __future__ import annotations

import dataclasses
from copy import deepcopy
from typing import List, Optional, Tuple, Union
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
        if self.layer.nodeb.nb_type == NodeBType.E:
            rb_type = LTEResourceBlock.E  # TODO: refactor or redesign

        bu_j += rb_type.time

        if bu_j + rb_type.time - 1 > self.ending_j:
            # next row
            bu_i += rb_type.freq
            bu_j: int = self.starting_j
            if bu_i + rb_type.freq - 1 > self.ending_i:
                return None     # running out of space

        return bu_i, bu_j

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


@dataclasses.dataclass(order=True, unsafe_hash=True)
class SimpleSpace:
    i_start: int
    j_start: int
    i_end: int
    j_end: int

    @property
    def width(self) -> int:
        return self.j_end - self.j_start

    @property
    def height(self) -> int:
        return self.i_end - self.i_start


def empty_space(layer: Layer) -> Tuple[Space, ...]:
    # ref: https://hackmd.io/HaKC3jR5Q4KOcumGo8RvKQ?view
    spaces: List[SimpleSpace] = scan(layer.bu_status)
    spaces: List[SimpleSpace] = merge(spaces)

    empty_spaces: List[Space] = []
    for space in spaces:
        empty_spaces.append(Space(layer, space.i_start, space.j_start, space.i_end, space.j_end))
    return tuple(empty_spaces)


def scan(bu_status: Tuple[Tuple[bool, ...], ...]) -> List[SimpleSpace]:
    spaces: List[SimpleSpace] = []
    for i in range(len(bu_status)):
        tmp_space: SimpleSpace = SimpleSpace(i, -1, i, -1)
        for j in range(len(bu_status[0])):
            if not bu_status[i][j]:  # is empty
                tmp_space.j_end = j
                if tmp_space.j_start == -1:
                    tmp_space.j_start = j
                if j == len(bu_status[0]) - 1:
                    spaces.append(tmp_space)
            elif tmp_space.j_start != -1:  # meet a allocated RB
                spaces.append(tmp_space)
                tmp_space: SimpleSpace = SimpleSpace(i, -1, i, -1)
    return spaces


def merge(spaces: List[SimpleSpace]) -> List[SimpleSpace]:
    merged_spaces: List[SimpleSpace] = []
    while spaces:
        space: SimpleSpace = spaces.pop(0)  # space to be merged
        other_spaces: List[SimpleSpace] = deepcopy(spaces)      # TODO: deepcopy is inefficient
        while other_spaces:
            other_space: SimpleSpace = other_spaces.pop(0)
            if (other_space.i_start == space.i_end + 1) and (other_space.j_start == space.j_start) and (
                    other_space.width == space.width):  # merge continuous and same width space
                space.i_end = other_space.i_end  # merge
                spaces.remove(other_space)  # remove the merged space
        merged_spaces.append(space)

    return merged_spaces
