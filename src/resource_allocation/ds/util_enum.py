from __future__ import annotations

import math
import random
from enum import Enum
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .util_type import CandidateSet


class Generation(Enum):
    E = '4G'
    G = '5G'


class UEType(Enum):
    D = f'{Generation.E.value}+{Generation.G.value}'
    E = Generation.E.value
    G = Generation.G.value


class NodeBType(Enum):
    E = Generation.E.value
    G = Generation.G.value

    @property
    def to_mcs(self):
        return G_MCS if self == NodeBType.G else E_MCS


class _Numerology(Enum):
    @property
    def freq(self) -> int:
        return self.value[0]

    @property
    def time(self) -> int:
        return self.value[1]

    @staticmethod
    def gen_candidate_set():
        raise NotImplementedError


class Numerology(_Numerology):
    # immutable Numerology Size (FREQ/HEIGHT, TIME/WIDTH), case where num_of_symbols is 16
    N0 = (2 ** 0, 2 ** 4)  # F: 1, T: 16
    N1 = (2 ** 1, 2 ** 3)  # F: 2, T: 8
    N2 = (2 ** 2, 2 ** 2)  # F: 4, T: 4
    N3 = (2 ** 3, 2 ** 1)  # F: 8, T: 2
    N4 = (2 ** 4, 2 ** 0)  # F: 16, T: 1

    @property
    def mu(self) -> int:
        return int(self.name[-1])

    @staticmethod
    def gen_candidate_set(exclude: CandidateSet = tuple(), random_pick: bool = False) -> CandidateSet:
        candidate_set: List[Numerology] = list({n for n in Numerology}.difference(exclude))
        assert len(candidate_set) > 0
        if random_pick:
            candidate_set: List[Numerology] = random.sample(candidate_set, random.randint(1, len(candidate_set)))

        return tuple(sorted(candidate_set, key=lambda x: x.mu))


class LTEPhysicalResourceBlock(_Numerology):
    E = (1, 8)  # F: 1, T: 8

    @staticmethod
    def gen_candidate_set() -> CandidateSet:
        return tuple((LTEPhysicalResourceBlock.E,))


class _MCS(Enum):  # speed unit: bps per RB
    def calc_required_rb_count(self, request_data_rate: float) -> int:
        # TODO!!: check if (the order of magnitude) is correct
        return math.ceil(request_data_rate / self.value)

    @staticmethod
    def get_worst() -> _MCS:
        raise NotImplementedError


# noinspection PyPep8Naming
class E_MCS(_MCS):
    CQI1_QPSK = 12.796875  # bit per 0.5ms(RB)
    CQI2_QPSK = 19.6875
    CQI3_QPSK = 31.6640625
    CQI4_QPSK = 50.53125
    CQI5_QPSK = 73.6640625
    CQI6_QPSK = 98.765625
    CQI7_16QAM = 124.03125
    CQI8_16QAM = 160.78125
    CQI9_16QAM = 202.125
    CQI10_64QAM = 229.359375
    CQI11_64QAM = 279.0703125
    CQI12_64QAM = 327.796875
    CQI13_64QAM = 379.96875
    CQI14_64QAM = 429.6796875
    CQI15_64QAM = 466.59375

    @staticmethod
    def get_worst() -> E_MCS:
        return E_MCS.CQI1_QPSK


# noinspection PyPep8Naming, SpellCheckingInspection
class G_MCS(_MCS):
    CQI1_QPSK = 22.010625  # bit per ms(RB)
    CQI2_QPSK = 33.8625
    CQI3_QPSK = 54.4621875
    CQI4_QPSK = 86.91375
    CQI5_QPSK = 126.7021875
    CQI6_QPSK = 169.876875
    CQI7_16QAM = 213.33375
    CQI8_16QAM = 276.54375
    CQI9_16QAM = 347.655
    CQI10_64QAM = 394.498125
    CQI11_64QAM = 480.0009375
    CQI12_64QAM = 563.810625
    CQI13_64QAM = 653.54625
    CQI14_64QAM = 739.0490625
    CQI15_64QAM = 802.54125

    @staticmethod
    def get_worst() -> G_MCS:
        return G_MCS.CQI1_QPSK
