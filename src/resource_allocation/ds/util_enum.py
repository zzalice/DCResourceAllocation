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
    QPSK_1 = 19900  # TODO: remember to change as real data

    @staticmethod
    def get_worst() -> E_MCS:
        return E_MCS.QPSK_1  # TODO: remember to as the worst one


# noinspection PyPep8Naming, SpellCheckingInspection
class G_MCS(_MCS):
    QPSK_1 = 19900
    QPSK_2 = 30480
    QPSK_3 = 49020
    QPSK_4 = 78220
    QPSK_5 = 114030
    QPSK_6 = 152890
    QAM16_7 = 192000
    QAM16_8 = 248890
    QAM16_9 = 312890
    QAM16_10 = 355050
    QAM16_11 = 432000
    QAM16_12 = 507430
    QAM16_13 = 588190
    QAM16_14 = 667430
    QAM16_15 = 722290

    @staticmethod
    def get_worst() -> G_MCS:
        return G_MCS.QPSK_1
