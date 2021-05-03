import dataclasses
import math
from typing import Tuple

from src.resource_allocation.ds.util_type import CandidateSet, CircularRegion, Coordinate


class HotSpot:
    def __repr__(self):
        return f'({self.region.x}, {self.region.y}, {self.region.radius}, {self.ue_proportion})'

    def __init__(self, x: float, y: float, radius: float, ue_proportion: float):
        assert radius > 0.0
        assert 0.0 <= ue_proportion <= 1.0, 'Proportion out of range.'
        self.region: CircularRegion = CircularRegion(x, y, radius)
        self.ue_proportion: float = ue_proportion
        self._num_ue: int = 0

    def calc_num_of_ue(self, total_ue: int):
        self._num_ue: int = math.floor(total_ue * self.ue_proportion)

    @property
    def num_ue(self) -> int:
        return self._num_ue


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
