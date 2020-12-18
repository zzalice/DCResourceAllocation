from __future__ import annotations

from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from .nodeb import ENBInfo, GNBInfo
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
        self.numerology_in_use: Optional[Numerology] = None
        self.enb_info: ENBInfo = ENBInfo(request_data_rate)
        self.gnb_info: GNBInfo = GNBInfo(request_data_rate)
        self.is_allocated: bool = False
        self.is_to_recalculate_mcs: bool = True
        self.throughput: float = 0.0

    def set_numerology(self, numerology: Numerology):
        assert numerology in self.candidate_set
        self.numerology_in_use: Numerology = numerology

    def register_nb(self, e_nb: ENodeB, g_nb: GNodeB):
        self.coordinate.calc_distance_to_nb(e_nb)
        self.coordinate.calc_distance_to_nb(g_nb)
        if hasattr(self, 'enb_info'):
            self.enb_info.nb = e_nb
            assert self.coordinate.distance_enb <= e_nb.radius
        if hasattr(self, 'gnb_info'):
            self.gnb_info.nb = g_nb
            assert self.coordinate.distance_gnb <= g_nb.radius
