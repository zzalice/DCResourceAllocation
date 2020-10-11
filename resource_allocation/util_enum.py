from __future__ import annotations

import math

from enum import Enum
from typing import Tuple


class Generation(Enum):
    E = '4G'
    G = '5G'


class UEType(Enum):
    D = Generation.E.value + '+' + Generation.G.value
    E = Generation.E.value
    G = Generation.G.value


class NodeBType(Enum):
    E = Generation.E.value
    G = Generation.G.value


class Numerology(Enum):
    # case for area = 16
    N0 = {'HEIGHT': 1, 'WIDTH': 16}
    N1 = {'HEIGHT': 2, 'WIDTH': 8}
    N2 = {'HEIGHT': 4, 'WIDTH': 4}
    N3 = {'HEIGHT': 8, 'WIDTH': 2}
    N4 = {'HEIGHT': 16, 'WIDTH': 1}

    def to_mu(self) -> int:
        return int(self.name[-1:])

    @property
    def height(self) -> int:
        return self.value['HEIGHT']

    @property
    def width(self) -> int:
        return self.value['WIDTH']

    @staticmethod
    def gen_candidate_set(exclude: Tuple[Numerology] = tuple()) -> Tuple[Numerology]:
        # TODO: fix tuple type annotation issue (3 places)
        return tuple({n for n in Numerology}.difference(exclude))


class MCSUtil(Enum):
    @classmethod
    def _missing_(cls, value):
        raise NotImplementedError

    def calc_required_rb_count(self, request_data_rate: float):
        # TODO!!: check if (the order of magnitude) is correct
        return math.ceil(request_data_rate / self.value)


class MCS_E(MCSUtil):
    WORST = 0.1  # TODO!!: to be announced

    @classmethod
    def _missing_(cls, value):
        return MCS_E.WORST  # the worst one  # TODO!: remember to change when MCS_E is determined


class MCS_G(MCSUtil):  # quantifier: kbps
    QPSK_1 = 19.90
    QPSK_2 = 30.48
    QPSK_3 = 49.02
    QPSK_4 = 78.22
    QPSK_5 = 114.03
    QPSK_6 = 152.89
    QAM16_7 = 192.00
    QAM16_8 = 248.89
    QAM16_9 = 312.89
    QAM16_10 = 355.05
    QAM16_11 = 432.00
    QAM16_12 = 507.43
    QAM16_13 = 588.19
    QAM16_14 = 667.43
    QAM16_15 = 722.29

    @classmethod
    def _missing_(cls, value):
        return MCS_G.QPSK_1  # the worst one
