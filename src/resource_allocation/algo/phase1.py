from typing import Dict, List, Tuple, Union

from ..ds.eutran import ENodeB
from ..ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from ..ds.util_enum import Numerology, UEType
from ..ds.zone import Zone


class Phase1:
    def __init__(self, ue_list: Tuple[Union[GUserEquipment, DUserEquipment], ...]):
        self.ue_list: Tuple[Union[GUserEquipment, DUserEquipment], ...] = ue_list

    def calc_inr(self, d_ue_discount: float) -> Dict[Numerology, float]:
        inr: Dict[Numerology, float] = {numerology: 0.0 for numerology in Numerology.gen_candidate_set()}
        for ue in self.ue_list:
            for numerology in ue.candidate_set:
                pass  # TODO # e.g., inr[numerology] = 1.0
        raise NotImplementedError  # TODO: this algo is not implemented yet
        return inr

    def form_zones(self, nodeb: Union[GNodeB, ENodeB]) -> Tuple[Tuple[Zone, ...], Tuple[Zone, ...]]:
        zone_fit: List[Zone] = list()
        zone_undersized: List[Zone] = list()

        for ue in self.ue_list:
            if ue.ue_type in (UEType.G, UEType.D):
                zone: Zone = Zone((ue,), nodeb)
                (zone_fit if zone.is_fit else zone_undersized).append(zone)
        return tuple(zone_fit), tuple(sorted(zone_undersized, key=lambda x: x.last_row_duration, reverse=True))
