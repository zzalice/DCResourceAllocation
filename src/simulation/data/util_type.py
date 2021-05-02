import dataclasses
from typing import Tuple

from src.resource_allocation.ds.util_type import CandidateSet, Coordinate


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
