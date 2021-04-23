import dataclasses
import math
from typing import List, Tuple, Union

from src.resource_allocation.ds.eutran import ENodeB
from src.resource_allocation.ds.ngran import GNodeB
from src.resource_allocation.ds.util_enum import UEType
from src.resource_allocation.ds.util_type import CandidateSet, Coordinate


class HotSpot:
    def __init__(self, coordinate: Coordinate, radius: float, count: int):
        assert count > 0
        assert radius > 0.0
        self.coordinate: Coordinate = coordinate
        self.radius: float = radius
        self.count: int = count


class UECoordinate:
    def __init__(self, ue_type: UEType, total_ue: int, e_nb: ENodeB, g_nb: GNodeB,
                 hotspots: Tuple[Tuple[float, float, float, float]] = ()):
        assert Coordinate.calc_distance(e_nb.coordinate, g_nb.coordinate) < (e_nb.radius + g_nb.radius)

        self.ue_type: UEType = ue_type

        # number of UE in each spot
        self.total_ue: int = total_ue
        self.ue_not_in_hotspot, hotspots = self.calc_ue_num(total_ue, hotspots)
        self.hotspots: Tuple[HotSpot, ...] = tuple([HotSpot(Coordinate(i[0], i[1]), i[2], i[3]) for i in hotspots])

        # major and secondary NB
        if ue_type == UEType.E:
            for hotspot in self.hotspots:
                assert Coordinate.calc_distance(e_nb.coordinate,
                                                hotspot.coordinate) + hotspot.radius <= e_nb.radius, "The hot spot area isn't in the area of BS."
                assert Coordinate.calc_distance(g_nb.coordinate,
                                                hotspot.coordinate) - hotspot.radius > g_nb.radius, "A single connection UE shouldn't be in the area of another BS."
            self.main_nb: ENodeB = e_nb
            self.second_nb: GNodeB = g_nb
        elif ue_type == UEType.G:
            for hotspot in self.hotspots:
                assert Coordinate.calc_distance(g_nb.coordinate,
                                                hotspot.coordinate) + hotspot.radius <= g_nb.radius, "The hot spot area isn't in the area of BS."
                assert Coordinate.calc_distance(e_nb.coordinate,
                                                hotspot.coordinate) - hotspot.radius > e_nb.radius, "A single connection UE shouldn't be in the area of another BS."
            self.main_nb: GNodeB = g_nb
            self.second_nb: ENodeB = e_nb
        elif ue_type == UEType.D:
            for hotspot in self.hotspots:
                assert (Coordinate.calc_distance(e_nb.coordinate, hotspot.coordinate) + hotspot.radius <= e_nb.radius
                        ) and (
                               Coordinate.calc_distance(g_nb.coordinate,
                                                        hotspot.coordinate) + hotspot.radius <= g_nb.radius
                       ), "The hot spot area isn't in the overlapped area of BSs."
            self.main_nb: ENodeB = e_nb
            self.second_nb: GNodeB = g_nb
        else:
            raise AssertionError

    @staticmethod
    def calc_ue_num(total_ue: int, hotspots: Tuple[Tuple[float, float, float, float]]
                    ) -> Tuple[int, List[List[Union[float, int]]]]:
        ue_in_hotspots: int = 0
        hotspots_with_num_ue: List[List[Union[float, int]]] = []    # List[List[float, float, float, int]]
        for hotspot in hotspots:
            hotspot: List[Union[float, int]] = list(hotspot)

            ue_proportion: float = hotspot[3]
            hotspot[3]: int = math.floor(total_ue * ue_proportion)
            assert hotspot[3] > 0, 'The value of hotspot proportion or total ue are too low.'

            ue_in_hotspots += hotspot[3]
            hotspots_with_num_ue.append(hotspot)
        assert 0 <= ue_in_hotspots <= total_ue, 'The proportion of UE in hotspot are too high.'
        return (total_ue - ue_in_hotspots), hotspots_with_num_ue

    def generate(self) -> Tuple[Coordinate, ...]:
        coordinates: List[Coordinate] = []
        for hotspot in self.hotspots:
            for _ in range(hotspot.count):
                coordinates.append(Coordinate.random_gen_coordinate((hotspot,)))
        if self.ue_type == UEType.D:
            for _ in range(self.ue_not_in_hotspot):
                coordinates.append(Coordinate.random_gen_coordinate((self.main_nb, self.second_nb), self.hotspots))
        else:
            for _ in range(self.ue_not_in_hotspot):
                coordinates.append(
                    Coordinate.random_gen_coordinate((self.main_nb,), self.hotspots + (self.second_nb,)))

        return tuple(coordinates)


@dataclasses.dataclass
class UEProfiles:
    count: int
    request_data_rate_list: Tuple[int, ...]
    candidate_set_list: Tuple[CandidateSet, ...]
    coordinate_list: Tuple[Coordinate, ...]

    def __iter__(self):
        single_data = dataclasses.make_dataclass('UEProfile', (
            ('request_data_rate', int), ('candidate_set', CandidateSet), ('coordinate', Coordinate)))
        for i in range(self.count):
            yield single_data(self.request_data_rate_list[i], self.candidate_set_list[i], self.coordinate_list[i])
