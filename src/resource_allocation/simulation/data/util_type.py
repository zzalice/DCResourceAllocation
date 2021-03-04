from typing import List, Tuple

from src.resource_allocation.ds.eutran import ENodeB
from src.resource_allocation.ds.ngran import GNodeB
from src.resource_allocation.ds.util_enum import UEType
from src.resource_allocation.ds.util_type import Coordinate


class HotSpot:
    def __init__(self, coordinate: Coordinate, radius: float, count: int):
        assert count > 0
        assert radius > 0.0
        self.coordinate: Coordinate = coordinate
        self.radius: float = radius
        self.count: int = count


class UECoordinate:
    def __init__(self, ue_type: UEType, count: int, e_nb: ENodeB, g_nb: GNodeB, hot_spots: Tuple[HotSpot, ...] = ()):
        assert Coordinate.calc_distance(e_nb.coordinate, g_nb.coordinate) < (e_nb.radius + g_nb.radius)
        if ue_type == UEType.E:
            for hot_spot in hot_spots:
                assert Coordinate.calc_distance(e_nb.coordinate, hot_spot.coordinate) + hot_spot.radius <= e_nb.radius, "The hot spot area isn't in the area of BS."
                assert Coordinate.calc_distance(g_nb.coordinate, hot_spot.coordinate) - hot_spot.radius > g_nb.radius, "A single connection UE shouldn't be in the area of another BS."
            self.main_nb: ENodeB = e_nb
            self.second_nb: GNodeB = g_nb
        elif ue_type == UEType.G:
            for hot_spot in hot_spots:
                assert Coordinate.calc_distance(g_nb.coordinate, hot_spot.coordinate) + hot_spot.radius <= g_nb.radius, "The hot spot area isn't in the area of BS."
                assert Coordinate.calc_distance(e_nb.coordinate, hot_spot.coordinate) - hot_spot.radius > e_nb.radius, "A single connection UE shouldn't be in the area of another BS."
            self.main_nb: GNodeB = g_nb
            self.second_nb: ENodeB = e_nb
        elif ue_type == UEType.D:
            for hot_spot in hot_spots:
                assert (Coordinate.calc_distance(e_nb.coordinate, hot_spot.coordinate) + hot_spot.radius <= e_nb.radius
                        ) and (
                        Coordinate.calc_distance(g_nb.coordinate, hot_spot.coordinate) + hot_spot.radius <= g_nb.radius
                        ), "The hot spot area isn't in the overlapped area of BSs."
            self.main_nb: ENodeB = e_nb
            self.second_nb: GNodeB = g_nb
        else:
            raise AssertionError

        self.ue_type: UEType = ue_type
        self.count: int = count
        self.hot_spots: Tuple[HotSpot, ...] = hot_spots

    def generate(self) -> Tuple[Coordinate, ...]:
        coordinates: List[Coordinate] = []
        count_not_in_hot_spot: int = self.count
        for hot_spot in self.hot_spots:
            count_not_in_hot_spot -= hot_spot.count
            assert count_not_in_hot_spot > -1, "The number of UEs in hot spots are more than expected amount."
            for _ in range(hot_spot.count):
                coordinates.append(Coordinate.random_gen_coordinate((hot_spot,)))
        if self.ue_type == UEType.D:
            for _ in range(count_not_in_hot_spot):
                coordinates.append(Coordinate.random_gen_coordinate((self.main_nb, self.second_nb), self.hot_spots))
        else:
            for _ in range(count_not_in_hot_spot):
                coordinates.append(
                    Coordinate.random_gen_coordinate((self.main_nb,), self.hot_spots + (self.second_nb,)))

        return tuple(coordinates)
