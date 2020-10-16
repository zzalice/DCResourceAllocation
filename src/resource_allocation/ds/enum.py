from __future__ import annotations

import math
from enum import Enum
from typing import Tuple


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


class Numerology(Enum):
    # immutable Numerology Size (HEIGHT, WIDTH), case where num_of_symbols is 16
    N0 = (2 ** 0, 2 ** 4)  # H:0, W: 16
    N1 = (2 ** 1, 2 ** 3)  # H:1, W: 8
    N2 = (2 ** 2, 2 ** 2)  # H:4, W: 4
    N3 = (2 ** 3, 2 ** 1)  # H:8, W: 2
    N4 = (2 ** 4, 2 ** 0)  # H:16, W: 1

    @property
    def mu(self) -> int:
        return int(self.name[-1])

    @property
    def height(self) -> int:
        return self.value[0]

    @property
    def width(self) -> int:
        return self.value[1]

    @staticmethod
    def gen_candidate_set(exclude: Tuple[Numerology, ...] = tuple()) -> Tuple[Numerology, ...]:
        return tuple({n for n in Numerology}.difference(exclude))


class _MCS(Enum):
    @classmethod
    def _missing_(cls, value):
        raise NotImplementedError

    def calc_required_rb_count(self, request_data_rate: float) -> int:
        # TODO!!: check if (the order of magnitude) is correct
        return math.ceil(request_data_rate / self.value)


# noinspection PyPep8Naming
class E_MCS(_MCS):
    WORST = 0.1  # TODO!!: to be announced

    @classmethod
    def _missing_(cls, value):
        return E_MCS.WORST  # the worst one  # TODO!: remember to change when MCS_E is determined


# noinspection PyPep8Naming, SpellCheckingInspection
class G_MCS(_MCS):  # quantifier: kbps
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
        return G_MCS.QPSK_1  # return the worst one when miss (e.g., G_MCS(None))
