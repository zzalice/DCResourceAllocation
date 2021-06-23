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

    @property
    def count_bu(self) -> int:
        return self.value[0] * self.value[1]

    @staticmethod
    def gen_candidate_set():
        raise NotImplementedError


class Numerology(_Numerology):
    # immutable Numerology Size (FREQ/HEIGHT, TIME/WIDTH), case where num_of_symbols is 8
    N0 = (2 ** 0, 2 ** 3)  # F: 1, T: 8
    N1 = (2 ** 1, 2 ** 2)  # F: 2, T: 4
    N2 = (2 ** 2, 2 ** 1)  # F: 4, T: 2
    N3 = (2 ** 3, 2 ** 0)  # F: 8, T: 1

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
    E = (1, 4)  # F: 1, T: 4

    @staticmethod
    def gen_candidate_set() -> CandidateSet:
        return tuple((LTEResourceBlock.E,))


class _MCS(Enum):
    @property
    def index(self) -> int:
        return int(self.name.replace('CQI', ''))

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


class _SINRtoMCS:
    """
    ref: https://www.mathworks.com/help/5g/ug/5g-nr-cqi-reporting.html
         https://www.researchgate.net/figure/CQI-MCS-and-SNR-mapping-for-3GPP-NR_tbl2_335395546
    """
    CQI1 = -9.478  # SINR in dB
    CQI2 = -6.658
    CQI3 = -4.098
    CQI4 = -1.798
    CQI5 = 0.399
    CQI6 = 2.424
    CQI7 = 4.489
    CQI8 = 6.367
    CQI9 = 8.456
    CQI10 = 10.266
    CQI11 = 12.218
    CQI12 = 14.122
    CQI13 = 15.849
    CQI14 = 17.786
    CQI15 = 19.809

    @staticmethod
    def sinr_to_mcs(sinr: float, nb_type: NodeBType) -> Union[E_MCS, G_MCS, Boolean]:
        if sinr < _SINRtoMCS.CQI1:  # SINR out of range
            return G_MCS.CQI0 if nb_type == NodeBType.G else E_MCS.CQI0
        elif _SINRtoMCS.CQI1 <= sinr < _SINRtoMCS.CQI2:
            return G_MCS.CQI1 if nb_type == NodeBType.G else E_MCS.CQI1
        elif _SINRtoMCS.CQI2 <= sinr < _SINRtoMCS.CQI3:
            return G_MCS.CQI2 if nb_type == NodeBType.G else E_MCS.CQI2
        elif _SINRtoMCS.CQI3 <= sinr < _SINRtoMCS.CQI4:
            return G_MCS.CQI3 if nb_type == NodeBType.G else E_MCS.CQI3
        elif _SINRtoMCS.CQI4 <= sinr < _SINRtoMCS.CQI5:
            return G_MCS.CQI4 if nb_type == NodeBType.G else E_MCS.CQI4
        elif _SINRtoMCS.CQI5 <= sinr < _SINRtoMCS.CQI6:
            return G_MCS.CQI5 if nb_type == NodeBType.G else E_MCS.CQI5
        elif _SINRtoMCS.CQI6 <= sinr < _SINRtoMCS.CQI7:
            return G_MCS.CQI6 if nb_type == NodeBType.G else E_MCS.CQI6
        elif _SINRtoMCS.CQI7 <= sinr < _SINRtoMCS.CQI8:
            return G_MCS.CQI7 if nb_type == NodeBType.G else E_MCS.CQI7
        elif _SINRtoMCS.CQI8 <= sinr < _SINRtoMCS.CQI9:
            return G_MCS.CQI8 if nb_type == NodeBType.G else E_MCS.CQI8
        elif _SINRtoMCS.CQI9 <= sinr < _SINRtoMCS.CQI10:
            return G_MCS.CQI9 if nb_type == NodeBType.G else E_MCS.CQI9
        elif _SINRtoMCS.CQI10 <= sinr < _SINRtoMCS.CQI11:
            return G_MCS.CQI10 if nb_type == NodeBType.G else E_MCS.CQI10
        elif _SINRtoMCS.CQI11 <= sinr < _SINRtoMCS.CQI12:
            return G_MCS.CQI11 if nb_type == NodeBType.G else E_MCS.CQI11
        elif _SINRtoMCS.CQI12 <= sinr < _SINRtoMCS.CQI13:
            return G_MCS.CQI12 if nb_type == NodeBType.G else E_MCS.CQI12
        elif _SINRtoMCS.CQI13 <= sinr < _SINRtoMCS.CQI14:
            return G_MCS.CQI13 if nb_type == NodeBType.G else E_MCS.CQI13
        elif _SINRtoMCS.CQI14 <= sinr < _SINRtoMCS.CQI15:
            return G_MCS.CQI14 if nb_type == NodeBType.G else E_MCS.CQI14
        elif _SINRtoMCS.CQI15 <= sinr:
            return G_MCS.CQI15 if nb_type == NodeBType.G else E_MCS.CQI15


# noinspection PyPep8Naming
class E_MCS(_MCS):
    """
    e.g. CQI1_QPSK = 12.796875
         data rate(Mbps) = ((1 / 0.0005) * (78/1024) * LOG(4,2) * 12 * 7) / 1000
         data rate(bit per RB) = data rate in Mbps * 0.0005 * 1000
    ref: [Resource Allocation for Multi-Carrier Cellular Networks](https://ieeexplore.ieee.org/abstract/document/8376971)
    """
    CQI0 = 0.0
    CQI1 = 12.796875  # bit per 0.5ms(RB)
    CQI2 = 19.6875
    CQI3 = 31.6640625
    CQI4 = 50.53125
    CQI5 = 73.6640625
    CQI6 = 98.765625
    CQI7 = 124.03125
    CQI8 = 160.78125
    CQI9 = 202.125
    CQI10 = 229.359375
    CQI11 = 279.0703125
    CQI12 = 327.796875
    CQI13 = 379.96875
    CQI14 = 429.6796875
    CQI15 = 466.59375

    @property
    def efficiency(self) -> float:
        return self.value / 4

    @staticmethod
    def sinr_to_mcs(sinr: float) -> E_MCS:
        worst_mcs: E_MCS = E_MCS.get_worst()
        best_mcs: E_MCS = E_MCS.get_best()
        if sinr < getattr(_SINRtoMCS, worst_mcs.name):
            return E_MCS.CQI0
        elif sinr > getattr(_SINRtoMCS, best_mcs.name):
            return best_mcs
        else:
            return _SINRtoMCS.sinr_to_mcs(sinr, NodeBType.E)

    @staticmethod
    def get_worst() -> E_MCS:
        return E_MCS.CQI1  # <-- change

    @staticmethod
    def get_best() -> E_MCS:
        return E_MCS.CQI7  # <-- change


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
    CQI1 = 22.010625  # bit per ms(RB)
    CQI2 = 33.8625
    CQI3 = 54.4621875
    CQI4 = 86.91375
    CQI5 = 126.7021875
    CQI6 = 169.876875
    CQI7 = 213.33375
    CQI8 = 276.54375
    CQI9 = 347.655
    CQI10 = 394.498125
    CQI11 = 480.0009375
    CQI12 = 563.810625
    CQI13 = 653.54625
    CQI14 = 739.0490625
    CQI15 = 802.54125

    @property
    def efficiency(self) -> float:
        return self.value / 8

    @staticmethod
    def sinr_to_mcs(sinr: float) -> G_MCS:
        worst_mcs: G_MCS = G_MCS.get_worst()
        best_mcs: G_MCS = G_MCS.get_best()
        if sinr < getattr(_SINRtoMCS, worst_mcs.name):
            return G_MCS.CQI0
        elif sinr > getattr(_SINRtoMCS, best_mcs.name):
            return best_mcs
        else:
            return _SINRtoMCS.sinr_to_mcs(sinr, NodeBType.G)

    @staticmethod
    def get_worst() -> G_MCS:
        return G_MCS.CQI1  # <-- change

    @staticmethod
    def get_best() -> G_MCS:
        return G_MCS.CQI7  # <-- change
