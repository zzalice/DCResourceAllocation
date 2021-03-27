from typing import Dict, List, Tuple, Union

from src.resource_allocation.algo.phase1 import Phase1
from src.resource_allocation.ds.ngran import GNodeB
from src.resource_allocation.ds.ue import UserEquipment
from src.resource_allocation.ds.util_enum import Numerology
from src.resource_allocation.ds.zone import Zone


class FRSAPhase1(Phase1):
    def __init__(self, nodeb: GNodeB, ue_list: Tuple[UserEquipment, ...]):
        super().__init__(ue_list)
        self.nodeb: GNodeB = nodeb
        self.inr: Dict[Numerology, float] = {numerology: 0.0 for numerology in Numerology.gen_candidate_set()}
        self.ue_list: Tuple[UserEquipment, ...] = ue_list

    def calc_inr(self, **kwargs):
        super().calc_inr(1.0)

    def form_and_categorize_zone(self):
        # form zone and categorize into (1/2)*T
        g_zone_fit, g_zone_undersized = super().form_zones(self.nodeb)
        g_zone_wide, g_zone_narrow = super().categorize_zone(g_zone_fit, g_zone_undersized)
        return g_zone_wide, g_zone_narrow

    @staticmethod
    def merge_zone_over_half(zone_undersized: Tuple[Zone, ...]) -> Tuple[Zone]:
        assert True not in [z.is_half for z in zone_undersized]
        zone_undersized: List[Zone] = list(zone_undersized)
        zone_merged: List[Zone] = []
        for numerology in Numerology:
            zones: List[Zone] = list(filter(lambda x: x.numerology == numerology, zone_undersized))
            while len(zones) >= 2:
                zone: Zone = zones.pop(0)
                zone_to_merge: Zone = zones.pop(0)
                zone.merge(zone_to_merge, row_limit=False)
                if zone.is_half:
                    zone_merged.append(zone)
                else:
                    zones.append(zone)
            zone_merged.extend(zones)
        return tuple(zone_merged)

    def virtual_allocate_zone(self, zone_unallocated: Tuple[Zone, ...]) -> Tuple[
                                Tuple[Dict[str, Union[int, List[Zone]]], ...], Tuple[Zone, ...]]:
        zone_allocated: List[Dict[str, Union[int, List[Zone]]]] = [{'residual': 0, 'zones': []} for _ in
                                                                   range(self.nodeb.frame.max_layer)]
        zone_unallocated: List[Zone] = list(zone_unallocated)
        zone_unallocated.sort(key=lambda x: x.sum_request_data_rate, reverse=True)
        for zone in zone_unallocated:
            for layer in self.nodeb.frame.layer:
                if layer.allocate_zone(zone, virtual=True):
                    zone_allocated[layer.layer_index]['zones'].append(zone)
                    break
        for layer in self.nodeb.frame.layer:
            zone_allocated[layer.layer_index]['residual'] = layer.available_bandwidth
        return tuple(zone_allocated), tuple(zone_unallocated)
