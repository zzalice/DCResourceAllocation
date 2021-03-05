from __future__ import annotations

import dataclasses
import math
import random
from _ast import List
from typing import NewType, Optional, Tuple, TYPE_CHECKING, Union

from .util_enum import _Numerology, NodeBType, Numerology

if TYPE_CHECKING:
    from .nodeb import NodeB
    from src.simulation.data import HotSpot

CandidateSet = NewType('CandidateSet', Tuple[_Numerology, ...])


@dataclasses.dataclass
class Coordinate:
    x: float
    y: float
    distance_enb: Optional[float] = None
    distance_gnb: Optional[float] = None

    def calc_distance_to_nb(self, target_nb: NodeB):
        if target_nb.nb_type == NodeBType.E:
            self.distance_enb = Coordinate.calc_distance(self, target_nb.coordinate)
        else:
            self.distance_gnb = Coordinate.calc_distance(self, target_nb.coordinate)

    @staticmethod
    def calc_distance(source: Coordinate, target: Coordinate) -> float:
        distance: float = math.sqrt((source.x - target.x) ** 2 + (source.y - target.y) ** 2)
        assert distance != 0.0, "The coordinate of the UE overlaps a BS."
        return distance

    @staticmethod
    def random_gen_coordinate(in_area: Tuple[Union[NodeB, HotSpot], ...],
                              not_in_area: Tuple[Union[NodeB, HotSpot], ...] = ()) -> Coordinate:
        tmp_x: float = random.uniform(in_area[0].coordinate.x - in_area[0].radius,
                                      in_area[0].coordinate.x + in_area[0].radius)
        tmp_y_range: float = math.sqrt(in_area[0].radius ** 2 - (tmp_x - in_area[0].coordinate.x) ** 2)
        tmp_y: float = random.uniform(in_area[0].coordinate.y - tmp_y_range, in_area[0].coordinate.y + tmp_y_range)
        assert (in_area[0].coordinate.x - tmp_x) ** 2 + (in_area[0].coordinate.y - tmp_y) ** 2 <= in_area[0].radius ** 2
        tmp_coordinate: Coordinate = Coordinate(tmp_x, tmp_y)

        for area in in_area[1:]:
            while Coordinate.calc_distance(area.coordinate, tmp_coordinate) > area.radius:
                tmp_coordinate = Coordinate.random_gen_coordinate(in_area, not_in_area)
        for area in not_in_area:
            while Coordinate.calc_distance(area.coordinate, tmp_coordinate) < area.radius:
                tmp_coordinate = Coordinate.random_gen_coordinate(in_area, not_in_area)

        return tmp_coordinate


@dataclasses.dataclass
class LappingPosition:
    _position: [int, int]
    numerology: Numerology
    time: int = 1

    @property
    def i_start(self) -> int:
        return self._position[0]

    @property
    def j_start(self) -> int:
        return self._position[1]

    def overlapping(self):
        self.time += 1


class LappingPositionList(list):
    def exist(self, position: List[int, int, Numerology]) -> Union[int, None]:
        for i, p in enumerate(self):
            if p.i_start == position[0] and p.j_start == position[1] and p.numerology == position[2]:
                return i
        return None
