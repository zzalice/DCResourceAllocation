from __future__ import annotations

from typing import Any, Dict, List, Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from utils.assertion import ThroughputError
from .nodeb import ENBInfo, GNBInfo
from .rb import ResourceBlock
from .util_enum import Numerology, UEType
from .util_type import CandidateSet

if TYPE_CHECKING:
    from .eutran import ENodeB
    from .ngran import GNodeB
    from .util_type import Coordinate


class UserEquipment:
    def __init__(self, request_data_rate: int, candidate_set: CandidateSet, coordinate: Coordinate):
        self.uuid: UUID = uuid4()
        self.request_data_rate: int = request_data_rate  # quantifier: bit per frame
        self.candidate_set: CandidateSet = candidate_set
        self.coordinate: Coordinate = coordinate

        # properties to be configured at runtime
        self.ue_type: Optional[UEType] = None
        self.enb_info: ENBInfo = ENBInfo()
        self.gnb_info: GNBInfo = GNBInfo()
        self.numerology_in_use: Optional[Numerology] = None
        self._is_to_recalculate_mcs: bool = False
        self._throughput: float = 0.0

    def set_numerology(self, numerology: Numerology):
        assert numerology in self.candidate_set
        self.numerology_in_use: Numerology = numerology

    def register_nb(self, e_nb: ENodeB, g_nb: GNodeB):
        self.coordinate.calc_distance_to_nb(e_nb)
        self.coordinate.calc_distance_to_nb(g_nb)
        if hasattr(self, 'enb_info'):
            self.enb_info.nb = e_nb
            assert self.coordinate.distance_enb <= e_nb.region.radius
        if hasattr(self, 'gnb_info'):
            self.gnb_info.nb = g_nb
            assert self.coordinate.distance_gnb <= g_nb.region.radius

    def remove_ue(self):
        self.throughput: float = 0.0

        # empty the allocated RBs & MCS
        if hasattr(self, 'enb_info'):
            self.enb_info.mcs = None
            while self.enb_info.rb:
                self.enb_info.rb[0].remove_rb()
            assert not self.enb_info.rb, "The RB remove failed."
        if hasattr(self, 'gnb_info'):
            self.gnb_info.mcs = None
            while self.gnb_info.rb:
                self.gnb_info.rb[0].remove_rb()
            assert not self.gnb_info.rb, "The RB remove failed."
        self.is_to_recalculate_mcs = False

    def highest_frequency_rb(self) -> Optional[ResourceBlock]:
        last_rb: List[ResourceBlock] = []
        if hasattr(self, 'gnb_info'):
            if rb := self.gnb_info.highest_frequency_rb():
                last_rb.append(rb)
        if hasattr(self, 'enb_info'):
            if rb := self.enb_info.highest_frequency_rb():
                last_rb.append(rb)
        if last_rb:
            last_rb.sort(key=lambda x: x.j_start)  # sort by time
            last_rb.sort(key=lambda x: x.i_start)  # sort by freq
            return last_rb[-1]
        else:
            return None

    def update_throughput(self):
        # !! Don't forget to update MCS before calling this method !!
        if hasattr(self, 'gnb_info'):
            if self.gnb_info.mcs:
                assert self.gnb_info.rb, "There is MCS but no RB(s)"
                for rb in self.gnb_info.rb:
                    assert self.gnb_info.mcs.value <= rb.mcs.value
            else:
                assert self.gnb_info.mcs is None and not self.gnb_info.rb, "The MCS is not up-to-date."
        if hasattr(self, 'enb_info'):
            if self.enb_info.mcs:
                assert self.enb_info.rb, "There is MCS but no RB(s)"
                for rb in self.enb_info.rb:
                    assert self.enb_info.mcs.value <= rb.mcs.value
            else:
                assert self.enb_info.mcs is None and not self.enb_info.rb, "The MCS is not up-to-date."

        self._throughput = self.calc_throughput()
        if self._throughput < self.request_data_rate:
            raise ThroughputError

    def calc_throughput(self) -> float:
        """ Won't change any value in UserEquipment. """
        tmp_throughput: float = 0.0
        if hasattr(self, 'gnb_info') and self.gnb_info.rb:
            tmp_throughput += min(self.gnb_info.rb, key=lambda rb: rb.mcs.value).mcs.value * len(self.gnb_info.rb)
        if hasattr(self, 'enb_info') and self.enb_info.rb:
            tmp_throughput += min(self.enb_info.rb, key=lambda rb: rb.mcs.value).mcs.value * len(self.enb_info.rb)
        return tmp_throughput

    @property
    def throughput(self):
        return self._throughput

    @throughput.setter
    def throughput(self, value: float):
        # for undo process
        self._throughput: float = value

    @property
    def is_allocated(self) -> bool:
        if hasattr(self, 'enb_info') and self.enb_info.rb:
            return True
        if hasattr(self, 'gnb_info') and self.gnb_info.rb:
            return True
        return False

    @property
    def is_to_recalculate_mcs(self) -> bool:
        return self._is_to_recalculate_mcs

    @is_to_recalculate_mcs.setter
    def is_to_recalculate_mcs(self, value: bool):
        self._is_to_recalculate_mcs: bool = value

    def to_json(self) -> Dict[str, Any]:
        ue: Dict[str, Any] = {
            'uuid': self.uuid.hex,
            'request_data_rate': self.request_data_rate,
            'x': self.coordinate.x,
            'y': self.coordinate.y,
            'distance_gnb': self.coordinate.distance_gnb,
            'distance_enb': self.coordinate.distance_enb,
            'ue_type': self.ue_type.name,
            'numerology_in_use': self.numerology_in_use.name,
            'throughput': self.throughput,
            'is_allocated': self.is_allocated}

        if hasattr(self, 'enb_info'):
            ue['enb_info'] = self.enb_info.to_json()
        if hasattr(self, 'gnb_info'):
            ue['gnb_info'] = self.gnb_info.to_json()
        if hasattr(self, 'cross_nb'):
            ue['cross_nb'] = self.cross_nb

        return ue
