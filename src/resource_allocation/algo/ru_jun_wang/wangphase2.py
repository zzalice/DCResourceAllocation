from typing import Dict, List, Tuple

from src.resource_allocation.ds.ngran import GNodeB
from src.resource_allocation.ds.util_enum import Numerology
from src.resource_allocation.ds.zone import Zone


class WangPhase2:
    def __init__(self, nodeb: GNodeB, zones_in_layers: Tuple[List[Zone], ...]):
        self.nb: GNodeB = nodeb
        self.zones_in_layers: Tuple[List[Zone], ...] = zones_in_layers
        self.total_freq_space: List[Dict[Numerology, int]] = [
            {numerology: 0 for numerology in Numerology.gen_candidate_set()} for _ in
            range(self.nb.frame.max_layer)]
        self.dissimilarity: List[Dict[Numerology, int]] = [
            {numerology: 0 for numerology in Numerology.gen_candidate_set()} for _ in
            range(self.nb.frame.max_layer)]

    def calc_total_freq_space(self):
        for layer, zones in enumerate(self.zones_in_layers):
            for numerology in self.total_freq_space[layer]:
                for zone in filter(lambda z: z.numerology == numerology, zones):
                    self.total_freq_space[layer][numerology] += zone.zone_freq

    def calc_dissimilarity(self):
        for layer in range(self.nb.frame.max_layer):
            for numerology in self.total_freq_space[layer]:
                for other_layer in filter(lambda x: x != layer, range(self.nb.frame.max_layer)):


