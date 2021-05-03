from __future__ import annotations

import dataclasses
import math
from _ast import List
from typing import Dict, NewType, Optional, Tuple, TYPE_CHECKING, Union

from .util_enum import _Numerology, NodeBType, Numerology

if TYPE_CHECKING:
    from .nodeb import NodeB

CandidateSet = NewType('CandidateSet', Tuple[_Numerology, ...])


@dataclasses.dataclass
class CircularRegion:
    x: float
    y: float
    radius: float  # km

    def calc_area(self) -> float:
        return (self.radius ** 2) * math.pi

    def in_region(self, target: Coordinate) -> bool:
        return Coordinate.calc_distance(self, target) <= self.radius

    def include_area(self, target: CircularRegion) -> bool:
        included: bool = False
        target_edge: Dict[str, float] = {
            'left': target.x - target.radius, 'right': target.x + target.radius,
            'up': target.y + target.radius, 'down': target.y - target.radius
        }
        source_edge: Dict[str, float] = {
            'left': self.x - self.radius, 'right': self.x + self.radius,
            'up': self.y + self.radius, 'down': self.y - self.radius
        }
        if (target_edge['left'] >= source_edge['left']) and (target_edge['right'] <= source_edge['right']) and (
                target_edge['up'] <= source_edge['up']) and (target_edge['down'] >= source_edge['down']):
            included: bool = True
        return included


@dataclasses.dataclass
class Coordinate:
    x: float
    y: float
    distance_enb: Optional[float] = None  # km
    distance_gnb: Optional[float] = None  # km

    def calc_distance_to_nb(self, target_nb: NodeB):
        if target_nb.nb_type == NodeBType.E:
            self.distance_enb = Coordinate.calc_distance(self, target_nb.region)
        else:
            self.distance_gnb = Coordinate.calc_distance(self, target_nb.region)

    @staticmethod
    def calc_distance(source: Union[Coordinate, CircularRegion], target: Union[Coordinate, CircularRegion]) -> float:
        distance: float = math.sqrt((source.x - target.x) ** 2 + (source.y - target.y) ** 2)
        assert distance != 0.0, "The coordinate of the UE overlaps a BS."
        return distance


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
