from __future__ import annotations

import dataclasses
import math
import random
from typing import NewType, Optional, Tuple, TYPE_CHECKING

from .util_enum import _Numerology, NodeBType, UEType

if TYPE_CHECKING:
    from .eutran import ENodeB
    from .ngran import GNodeB
    from .nodeb import NodeB

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
    def random_gen_coordinate(ue_type: UEType, e_nb: ENodeB, g_nb: GNodeB) -> Coordinate:
        nb_first: NodeB = g_nb if ue_type == UEType.G else e_nb
        nb_second: Optional[NodeB] = g_nb if ue_type == UEType.D else None

        tmp_x: float = random.uniform(nb_first.coordinate.x - nb_first.radius, nb_first.coordinate.x + nb_first.radius)
        tmp_y_range: float = math.sqrt(nb_first.radius ** 2 - (tmp_x - nb_first.coordinate.x) ** 2)
        tmp_y: float = random.uniform(nb_first.coordinate.y - tmp_y_range, nb_first.coordinate.y + tmp_y_range)
        assert (nb_first.coordinate.x - tmp_x) ** 2 + (nb_first.coordinate.y - tmp_y) ** 2 <= nb_first.radius ** 2
        tmp_coordinate: Coordinate = Coordinate(tmp_x, tmp_y)

        if nb_second is not None:
            assert Coordinate.calc_distance(nb_first.coordinate, nb_second.coordinate) < (
                    nb_first.radius + nb_second.radius)
            while ((nb_second.coordinate.x - tmp_coordinate.x) ** 2 + (nb_second.coordinate.y - tmp_coordinate.y) ** 2
                   > nb_second.radius ** 2):
                tmp_coordinate = Coordinate.random_gen_coordinate(ue_type, e_nb, g_nb)

        return tmp_coordinate
