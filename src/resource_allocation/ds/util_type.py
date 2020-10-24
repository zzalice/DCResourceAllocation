import dataclasses
import random
from typing import NewType, Tuple

from .util_enum import Numerology

CandidateSet = NewType('CandidateSet', Tuple[Numerology, ...])


@dataclasses.dataclass
class DistanceRange:
    e_min: float
    e_max: float
    g_min: float
    g_max: float
    nb_distance: float

    @property
    def e_range(self) -> Tuple[float, float]:
        return self.e_min, self.e_max

    @property
    def g_range(self) -> Tuple[float, float]:
        return self.g_min, self.g_max

    @property
    def e_random(self) -> float:
        return random.uniform(self.e_min, self.e_max)

    @property
    def g_random(self) -> float:
        return random.uniform(self.g_min, self.g_max)
