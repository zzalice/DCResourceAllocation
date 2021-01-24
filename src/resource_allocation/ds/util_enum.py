from __future__ import annotations

import math
import random
from enum import Enum
from typing import List, TYPE_CHECKING, Union
from xmlrpc.client import Boolean

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


class LTEResourceBlock(_Numerology):
    E = (1, 8)  # F: 1, T: 8

    @staticmethod
    def gen_candidate_set() -> CandidateSet:
        return tuple((LTEResourceBlock.E,))


class _MCS(Enum):
    def calc_required_rb_count(self, request_data_rate: float) -> int:
        if self.value == 0.0:
            return 0
        else:
            return math.ceil(request_data_rate / self.value)

    @staticmethod
    def get_worst() -> _MCS:
        raise NotImplementedError

    @property
    def efficiency(self) -> float:
        """
        The transmit efficiency of a LTE RB is always higher than NR RB.
        e.g. E_MCS.CQI1_QPSK * 2 > G_MCS.CQI1_QPSK
        In some cases, LTE RB is even one level higher than NR RB.
        e.g. E_MCS.CQI9_16QAM * 2 > G_MCS.CQI10_64QAM
        This is why we should calculate the efficiency of MCS.
        """
        raise NotImplementedError


# noinspection PyPep8Naming
class E_MCS(_MCS):
    """
    e.g. CQI1_QPSK = 12.796875
         data rate(Mbps) = ((1 / 0.0005) * (78/1024) * LOG(4,2) * 12 * 7) / 1000
         data rate(bit per RB) = data rate in Mbps * 0.0005 * 1000
    ref: [Resource Allocation for Multi-Carrier Cellular Networks](https://ieeexplore.ieee.org/abstract/document/8376971)
    """
    CQI0 = 0.0
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

    @property
    def efficiency(self) -> float:
        return self.value / 8


# noinspection PyPep8Naming, SpellCheckingInspection
class G_MCS(_MCS):
    """
    e.g. CQI1_QPSK = 22.010625
         data rate(Mbps) = 10^(-6) * 2 * 1 * (78/1024) * 216 * 12 / [10^(-3)/(14*2^0)] * (1 - 0.14)
         data rate(bit per RB) = (data rate in Mbps * 1000000) / (1000 * 216)
    ref: [TS 38.214 Table 5.1.3.1-1, 5.2.2.1-2](https://www.etsi.org/deliver/etsi_ts/138200_138299/138214/15.10.00_60/ts_138214v151000p.pdf)
         [TS 38.306 4.1.2](https://www.etsi.org/deliver/etsi_ts/138300_138399/138306/15.03.00_60/ts_138306v150300p.pdf)
         [5G NR Throughput calculator](https://5g-tools.com/5g-nr-throughput-calculator/)
    """
    CQI0 = 0.0
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

    @property
    def efficiency(self) -> float:
        return self.value / 16


class SINRtoMCS:
    """
    ref: https://www.mathworks.com/help/5g/ug/5g-nr-cqi-reporting.html
    """
    CQI1_QPSK = -1.889  # SINR in dB
    CQI2_QPSK = -0.817
    CQI3_QPSK = 0.954
    CQI4_QPSK = 2.948
    CQI5_QPSK = 4.899
    CQI6_QPSK = 7.39
    CQI7_16QAM = 8.898
    CQI8_16QAM = 11.02
    CQI9_16QAM = 13.3
    CQI10_64QAM = 14.68
    CQI11_64QAM = 16.62
    CQI12_64QAM = 18.91
    CQI13_64QAM = 21.58
    CQI14_64QAM = 24.88
    CQI15_64QAM = 29.32

    @staticmethod
    def sinr_to_mcs(sinr: float, nb_type: NodeBType) -> Union[E_MCS, G_MCS, Boolean]:
        if sinr < SINRtoMCS.CQI1_QPSK:  # SINR out of range
            return G_MCS.CQI0 if nb_type == NodeBType.G else E_MCS.CQI0
        elif SINRtoMCS.CQI1_QPSK <= sinr < SINRtoMCS.CQI2_QPSK:
            return G_MCS.CQI1_QPSK if nb_type == NodeBType.G else E_MCS.CQI1_QPSK
        elif SINRtoMCS.CQI2_QPSK <= sinr < SINRtoMCS.CQI3_QPSK:
            return G_MCS.CQI2_QPSK if nb_type == NodeBType.G else E_MCS.CQI2_QPSK
        elif SINRtoMCS.CQI3_QPSK <= sinr < SINRtoMCS.CQI4_QPSK:
            return G_MCS.CQI3_QPSK if nb_type == NodeBType.G else E_MCS.CQI3_QPSK
        elif SINRtoMCS.CQI4_QPSK <= sinr < SINRtoMCS.CQI5_QPSK:
            return G_MCS.CQI4_QPSK if nb_type == NodeBType.G else E_MCS.CQI4_QPSK
        elif SINRtoMCS.CQI5_QPSK <= sinr < SINRtoMCS.CQI6_QPSK:
            return G_MCS.CQI5_QPSK if nb_type == NodeBType.G else E_MCS.CQI5_QPSK
        elif SINRtoMCS.CQI6_QPSK <= sinr < SINRtoMCS.CQI7_16QAM:
            return G_MCS.CQI6_QPSK if nb_type == NodeBType.G else E_MCS.CQI6_QPSK
        elif SINRtoMCS.CQI7_16QAM <= sinr < SINRtoMCS.CQI8_16QAM:
            return G_MCS.CQI7_16QAM if nb_type == NodeBType.G else E_MCS.CQI7_16QAM
        elif SINRtoMCS.CQI8_16QAM <= sinr < SINRtoMCS.CQI9_16QAM:
            return G_MCS.CQI8_16QAM if nb_type == NodeBType.G else E_MCS.CQI8_16QAM
        elif SINRtoMCS.CQI9_16QAM <= sinr < SINRtoMCS.CQI10_64QAM:
            return G_MCS.CQI9_16QAM if nb_type == NodeBType.G else E_MCS.CQI9_16QAM
        elif SINRtoMCS.CQI10_64QAM <= sinr < SINRtoMCS.CQI11_64QAM:
            return G_MCS.CQI10_64QAM if nb_type == NodeBType.G else E_MCS.CQI10_64QAM
        elif SINRtoMCS.CQI11_64QAM <= sinr < SINRtoMCS.CQI12_64QAM:
            return G_MCS.CQI11_64QAM if nb_type == NodeBType.G else E_MCS.CQI11_64QAM
        elif SINRtoMCS.CQI12_64QAM <= sinr < SINRtoMCS.CQI13_64QAM:
            return G_MCS.CQI12_64QAM if nb_type == NodeBType.G else E_MCS.CQI12_64QAM
        elif SINRtoMCS.CQI13_64QAM <= sinr < SINRtoMCS.CQI14_64QAM:
            return G_MCS.CQI13_64QAM if nb_type == NodeBType.G else E_MCS.CQI13_64QAM
        elif SINRtoMCS.CQI14_64QAM <= sinr < SINRtoMCS.CQI15_64QAM:
            return G_MCS.CQI14_64QAM if nb_type == NodeBType.G else E_MCS.CQI14_64QAM
        elif SINRtoMCS.CQI15_64QAM <= sinr:
            return G_MCS.CQI15_64QAM if nb_type == NodeBType.G else E_MCS.CQI15_64QAM
