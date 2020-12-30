from __future__ import annotations

import dataclasses
from copy import deepcopy
from typing import List, Optional, Tuple
from uuid import UUID, uuid4

from src.resource_allocation.ds.frame import Layer
from src.resource_allocation.ds.nodeb import NodeB
from src.resource_allocation.ds.util_enum import LTEPhysicalResourceBlock, NodeBType, Numerology


class Space:
    def __init__(self, layer: Layer, starting_i: int, starting_j: int, ending_i: int, ending_j: int):
        self.uuid: UUID = uuid4()
        self.nb: NodeB = layer.nodeb
        self.layer: Layer = layer
        self.starting_i: int = starting_i
        self.starting_j: int = starting_j
        self.ending_i: int = ending_i
        self.ending_j: int = ending_j
        self._numerology: List[Tuple[Numerology, int]] = self.possible_numerology()

    def next_rb(self, bu_i: int, bu_j: int, numerology: Numerology) -> Optional[Tuple[int, int]]:
        if self.nb.nb_type == NodeBType.E:
            numerology = LTEPhysicalResourceBlock.E  # TODO: refactor or redesign

        end_i: int = bu_i + numerology.freq - 1
        end_j: int = bu_j + numerology.time - 1

        # the coordination of next RB
        if end_j + numerology.time <= self.ending_j:
            # The width of the space can contain another RB.
            bu_j += numerology.time
            return bu_i, bu_j
        elif end_i + numerology.freq < self.ending_i:
            # new row
            bu_i += numerology.freq
            bu_j = self.starting_j
            return bu_i, bu_j
        else:
            # running out of space
            return None

    def possible_numerology(self) -> List[Tuple[Numerology, int]]:
        available_numerology: List[Tuple[Numerology, int]] = []
        #                    Tuple[the type of numerology that fits this space, the number of RBs can be placed in here]
        for numerology in Numerology:
            num_rb_freq: int = self.height // numerology.freq
            num_rb_time: int = self.width // numerology.time
            num_rb: int = num_rb_freq * num_rb_time
            if num_rb:
                available_numerology.append((numerology, num_rb))
        return available_numerology

    def num_of_rb(self, numerology: Numerology) -> int:
        for n in self._numerology:
            if numerology is n[0]:
                return n[1]

    @property
    def numerology(self) -> List[Numerology]:
        numerology: List[Numerology] = []
        for n in self._numerology:
            numerology.append(n[0])
        return numerology

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
    """https://hackmd.io/HaKC3jR5Q4KOcumGo8RvKQ?view"""
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
        other_spaces: List[SimpleSpace] = deepcopy(spaces)
        while other_spaces:
            other_space: SimpleSpace = other_spaces.pop(0)
            if (other_space.i_start == space.i_end + 1) and (other_space.j_start == space.j_start) and (
                    other_space.width == space.width):  # merge continuous and same width space
                space.i_end = other_space.i_end  # merge
                spaces.remove(other_space)  # remove the merged space
        merged_spaces.append(space)

    return merged_spaces
