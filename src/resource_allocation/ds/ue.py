from __future__ import annotations

from typing import Optional, Set, TYPE_CHECKING, Union
from uuid import UUID, uuid4

from .nodeb import _NBInfoWithinUE, ENBInfo, GNBInfo, NodeB
from .util_enum import E_MCS, G_MCS, NodeBType, Numerology, UEType
from .util_type import CandidateSet, DistanceRange

if TYPE_CHECKING:
    from .eutran import ENodeB
    from .ngran import GNodeB


class UserEquipment:
    def __init__(self, request_data_rate: int, candidate_set: CandidateSet):
        self.uuid: UUID = uuid4()
        self.request_data_rate: int = request_data_rate
        self.candidate_set: Set[Numerology] = set(candidate_set)

        # properties to be configured at runtime
        self.ue_type: Optional[UEType] = None
        self.numerology_in_use: Optional[Numerology] = None
        self.enb_info: ENBInfo = ENBInfo(request_data_rate)
        self.gnb_info: GNBInfo = GNBInfo(request_data_rate)

    def set_numerology(self, numerology: Numerology):
        assert numerology in self.candidate_set
        self.numerology_in_use: Numerology = numerology

    def register_nb(self, target_nb: NodeB, distance: float):
        nb_info: _NBInfoWithinUE = (self.enb_info if target_nb.nb_type == NodeBType.E else self.gnb_info)
        nb_info.nb = target_nb
        nb_info.distance = distance

    def assign_mcs(self, mcs: Union[E_MCS, G_MCS]):
        raise NotImplementedError

    @staticmethod
    def calc_distance_range(e_nb: ENodeB, g_nb: GNodeB, nb_distance: float) -> DistanceRange:
        assert 0 <= nb_distance <= e_nb.radius + g_nb.radius
        return DistanceRange(max(0.0, nb_distance - g_nb.radius), min(e_nb.radius, nb_distance + g_nb.radius),
                             max(0.0, nb_distance - e_nb.radius), g_nb.radius, nb_distance)
