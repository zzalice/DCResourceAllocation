import math
import random
from typing import Dict, List, Tuple

from src.resource_allocation.ds.util_type import CircularRegion, Coordinate


class Deploy:
    @staticmethod
    def random(total_ue: int, in_area: Tuple[CircularRegion, ...]
               ) -> Tuple[Tuple[Tuple[Coordinate, ...]], Tuple[Coordinate, ...]]:
        """
        Uniformly deploy UE in the areas.
        :param total_ue: The number of UE to deploy in the areas.
        :param in_area: The areas to deploy UE. Can't be more than two.
        :return: The coordinate of UE in each area and in overlapped area.
        """
        assert 0 < len(in_area) <= 2
        # random coordinate
        bound: Dict[str, float] = Deploy.union_bound(in_area)
        sc_coordinates: List[List[Coordinate]] = [[] for _ in range(len(in_area))]
        dc_coordinates: List[Coordinate] = []
        for i in range(total_ue):
            while True:
                tmp_coordinate: Coordinate = Coordinate(x=random.uniform(bound['left'], bound['right']),
                                                        y=random.uniform(bound['down'], bound['up']))
                under_coverage: List[int] = []
                for j, area in enumerate(in_area):
                    if area.in_region(tmp_coordinate):
                        under_coverage.append(j)
                if len(under_coverage) == 1:
                    sc_coordinates[under_coverage[0]].append(tmp_coordinate)
                    break
                elif len(under_coverage) > 1:
                    dc_coordinates.append(tmp_coordinate)
                    break
        sc_coordinates: Tuple[Tuple[Coordinate, ...]] = tuple(tuple(coordinates) for coordinates in sc_coordinates)
        return sc_coordinates, tuple(dc_coordinates)

    @staticmethod
    def cell_edge(total_ue: int, in_area: Tuple[CircularRegion, ...],
                  proportion_cell_center: float = 0.85, proportion_of_ue_in_edge: float = 0.4):
        # assert 面積比要低於proportion, 'Proportion of UE in cell edge is too low.'
        pass

    @staticmethod
    def hotspots(total_ue: int, in_area: Tuple[CircularRegion, ...],
                 hotspots: Tuple[Tuple[CircularRegion, float], ...]):
        # assert , 'A hotspot is not in the BS area.'
        pass

    @staticmethod
    def dc_proportion(total_ue: int, in_area: Tuple[CircularRegion, ...], proportion_in_overlapped_area: float):
        pass

    @staticmethod
    def random_in_overlapped(in_area: Tuple[CircularRegion, ...],
                             not_in_area: Tuple[CircularRegion, ...] = ()) -> Coordinate:
        """
        Deployed UE must be in the areas.
        :param in_area: Must be in all of these areas.
        :param not_in_area: Must not be in any of these areas.
        :return: The final coordination.
        """
        tmp_x: float = random.uniform(in_area[0].x - in_area[0].radius, in_area[0].x + in_area[0].radius)
        tmp_y_range: float = math.sqrt(in_area[0].radius ** 2 - (tmp_x - in_area[0].x) ** 2)
        tmp_y: float = random.uniform(in_area[0].y - tmp_y_range, in_area[0].y + tmp_y_range)
        assert (in_area[0].x - tmp_x) ** 2 + (in_area[0].y - tmp_y) ** 2 <= in_area[0].radius ** 2
        tmp_coordinate: Coordinate = Coordinate(tmp_x, tmp_y)

        for area in in_area[1:]:
            while Coordinate.calc_distance(area, tmp_coordinate) > area.radius:
                tmp_coordinate = Deploy.random_gen_coordinate(in_area, not_in_area)
        for area in not_in_area:
            while Coordinate.calc_distance(area, tmp_coordinate) < area.radius:
                tmp_coordinate = Deploy.random_gen_coordinate(in_area, not_in_area)

        return tmp_coordinate

    @staticmethod
    def union_bound(areas: Tuple[CircularRegion, ...]) -> Dict[str, float]:
        assert areas
        bound: Dict[str, float] = {
            'left': areas[0].x - areas[0].radius,
            'right': areas[0].x + areas[0].radius,
            'up': areas[0].y + areas[0].radius,
            'down': areas[0].y - areas[0].radius
        }
        for area in areas[1:]:
            tmp_left: float = area.x - area.radius
            tmp_right: float = area.x + area.radius
            tmp_up: float = area.y + area.radius
            tmp_down: float = area.y - area.radius
            if tmp_left < bound['left']:
                bound['left'] = tmp_left
            if tmp_right > bound['right']:
                bound['right'] = tmp_right
            if tmp_up > bound['up']:
                bound['up'] = tmp_up
            if tmp_down < bound['down']:
                bound['down'] = tmp_down
        return bound
