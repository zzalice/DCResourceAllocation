from typing import Dict, List, Tuple, Union

from ..ds.eutran import ENodeB
from ..ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from ..ds.util_enum import Numerology, UEType
from ..ds.zone import Zone


class Phase1:
    def __init__(self, ue_list: Tuple[Union[GUserEquipment, DUserEquipment], ...]):
        self.flag_inr_is_calculated: bool = False
        self.inr: Dict[Numerology, float] = {numerology: 0.0 for numerology in Numerology.gen_candidate_set()}
        self.ue_list: Tuple[Union[GUserEquipment, DUserEquipment], ...] = ue_list

    def calc_inr(self, d_ue_discount: float):
        assert 0.0 < d_ue_discount <= 1.0
        assert not self.flag_inr_is_calculated
        self.flag_inr_is_calculated: bool = True
        for ue in self.ue_list:
            for numerology in ue.candidate_set:
                self.inr[numerology] += (len(Numerology) - len(ue.candidate_set)
                                         ) * (d_ue_discount if ue.ue_type == UEType.D else 1)

    def select_init_numerology(self):
        assert self.flag_inr_is_calculated
        for ue in self.ue_list:
            ue.numerology_in_use = ue.candidate_set[0]
            for numerology in ue.candidate_set[1:]:
                if self.inr[ue.numerology_in_use] < self.inr[numerology]:
                    ue.numerology_in_use = numerology

    def form_zones(self, nodeb: Union[GNodeB, ENodeB]) -> Tuple[Tuple[Zone, ...], Tuple[Zone, ...]]:
        zone_fit: List[Zone] = list()
        zone_undersized: List[Zone] = list()

        for ue in self.ue_list:
            if ue.ue_type in (UEType.G, UEType.D):
                zone: Zone = Zone((ue,), nodeb)
                (zone_fit if zone.is_fit else zone_undersized).append(zone)
        return tuple(zone_fit), tuple(sorted(zone_undersized, key=lambda x: x.last_row_duration, reverse=True))

    @staticmethod
    def merge_zone(zone_undersized: Tuple[Zone, ...]) -> Tuple[Zone, ...]:
        zone_merged: List[Zone] = list()

        for original_zone in zone_undersized:
            is_merged: bool = False
            for zone in [x for x in zone_merged if x.numerology == original_zone.numerology]:
                if original_zone.last_row_duration <= zone.last_row_remaining_time:
                    zone.merge(original_zone)
                    is_merged: bool = True
                    break
            if not is_merged:
                zone_merged.append(original_zone)
        return tuple(zone_merged)

    @staticmethod
    def categorize_zone(zone_fit: Tuple[Zone, ...], zone_merged: Tuple[Zone, ...]
                        ) -> Tuple[Tuple[Zone, ...], Tuple[Zone, ...]]:
        zone_wide: List[Zone] = list(zone_fit)
        zone_narrow: List[Zone] = list()

        for zone in zone_merged:
            (zone_wide if zone.last_row_duration >= zone.zone_time / 2 else zone_narrow).append(zone)
        return tuple(zone_wide), tuple(zone_narrow)
