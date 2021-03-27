from copy import deepcopy
from typing import Dict, List, Tuple, Union

from src.resource_allocation.ds.ngran import GNodeB
from src.resource_allocation.ds.util_enum import Numerology
from src.resource_allocation.ds.zone import Zone

Dissimilarity = Dict[int, List[Union[Numerology, float]]]  # {layer: [Numerology, 0.0]}


class FRSAPhase2:
    def __init__(self, nodeb: GNodeB, zones_in_layers: Tuple[Dict[str, Union[int, List[Zone]]], ...]):
        self.nb: GNodeB = nodeb
        self.zones_in_layers: Tuple[Dict[str, Union[int, List[Zone]]], ...] = zones_in_layers
        self.freq_span: List[Dict[Numerology, int]] = []

    def zd(self):
        self.calc_total_freq_span()
        is_improved: bool = True
        while is_improved:
            is_improved: bool = False
            max_dissimilarity: Dissimilarity = {i: [None, -1] for i in range(self.nb.frame.max_layer)}
            for l in range(self.nb.frame.max_layer):
                for numerology in Numerology:
                    dissimilarity: float = self.calc_dissimilarity(l, numerology, self.freq_span)
                    if dissimilarity > max_dissimilarity[l][1]:
                        max_dissimilarity[l] = [numerology, dissimilarity]

            max_dissimilarity: Dissimilarity = dict(sorted(max_dissimilarity.items(), key=lambda item: item[1][1]))
            cn: List[Tuple[int, List[Union[Numerology, float]]]] = []
            k: List[int] = []
            residual: List[int] = []
            for i in range(2):  # pick two concatenate zone with largest dissimilarity TODO: is this correct?
                cn.append(max_dissimilarity.popitem())
                k.append(self.freq_span[cn[-1][0]][cn[-1][1][0]])  # layer = cn[-1][0], numerology = cn[-1][1][0]
                residual.append(self.zones_in_layers[cn[-1][0]]['residual'])
            if k[0] <= k[1] + residual[1] and k[1] <= k[0] + residual[0]:
                origin_ld: float = self.calc_layer_dissimilarity(self.freq_span)
                freq_span = self.displace_zone(cn)
                new_ld: float = self.calc_layer_dissimilarity(freq_span)
                if new_ld < origin_ld:
                    self.update_zones_in_layers(cn)
                    assert [self.freq_span[i][j] == freq_span[i][j] for i, d in enumerate(self.freq_span) for j in d]    # FIXME
                    is_improved: bool = True

    def za(self):
        # FIXME Concatenate zones
        base_layer: int = -1  # FIXME 挑zone個數最少的layer
        # FIXME 將base_layer裡的cz由BW大排到小 真的要擺上去了
        for l in range(self.nb.frame.max_layer):
            if l == base_layer:
                continue
            # FIXME 真的要擺上去了
            # 1. 對齊 2. 推擠

    def calc_total_freq_span(self):
        self.freq_span: List[Dict[Numerology, int]] = [
            {numerology: 0 for numerology in Numerology.gen_candidate_set()} for _ in
            range(self.nb.frame.max_layer)]
        for l, zone_in_l in enumerate(self.zones_in_layers):
            for zone in zone_in_l['zones']:
                self.freq_span[l][zone.numerology] += zone.zone_freq

    def calc_dissimilarity(self, layer: int, numerology: Numerology, freq_span: List[Dict[Numerology, int]]) -> float:
        dissimilarity: float = 0.0
        for l in range(self.nb.frame.max_layer):
            if l == layer:
                continue
            dissimilarity += abs(freq_span[layer][numerology] - freq_span[l][numerology])
        return dissimilarity / self.nb.frame.max_layer

    def calc_layer_dissimilarity(self, freq_span: List[Dict[Numerology, int]]) -> float:
        ld: float = 0.0
        for numerology in Numerology:
            for layer in range(self.nb.frame.max_layer):
                ld += self.calc_dissimilarity(layer, numerology, freq_span)
        return ld

    def displace_zone(self, cn: List[Tuple[int, List[Union[Numerology, float]]]]) -> List[Dict[Numerology, int]]:
        #                     (two cn)     layer    [Numerology, dissimilarity]
        freq_span: List[Dict[Numerology, int]] = deepcopy(self.freq_span)
        cn_1_layer: int = cn[0][0]
        cn_1_numerology: Numerology = cn[0][1][0]
        cn_2_layer: int = cn[1][0]
        cn_2_numerology: Numerology = cn[1][1][0]

        tmp_span: int = freq_span[cn_2_layer][cn_2_numerology]
        freq_span[cn_2_layer][cn_2_numerology] = freq_span[cn_1_layer][cn_1_numerology]
        freq_span[cn_1_layer][cn_1_numerology] = tmp_span
        return freq_span

    def update_zones_in_layers(self, cn: List[Tuple[int, List[Union[Numerology, float]]]]):
        cn_1_layer: int = cn[0][0]
        cn_1_numerology: Numerology = cn[0][1][0]
        tmp_zone: List[Zone] = []
        tmp_span: int = 0
        cn_2_layer: int = cn[1][0]
        cn_2_numerology: Numerology = cn[1][1][0]

        # back up cn 1
        i: int = 0
        for zone in self.zones_in_layers[cn_1_layer]['zones'][i:]:
            if zone.numerology == cn_1_numerology:
                tmp_zone.append(zone)
                tmp_span += zone.zone_freq
                self.zones_in_layers[cn_1_layer]['zones'].remove(zone)
                self.zones_in_layers[cn_1_layer]['residual'] += zone.zone_freq
            else:
                i += 1

        # move cn 2 to cn_1_layer
        i: int = 0
        for zone in self.zones_in_layers[cn_2_layer]['zones'][i:]:
            if zone.numerology == cn_2_numerology:
                self.zones_in_layers[cn_1_layer]['zones'].append(zone)
                self.zones_in_layers[cn_1_layer]['residual'] -= zone.zone_freq
                self.zones_in_layers[cn_2_layer]['zones'].remove(zone)
                self.zones_in_layers[cn_2_layer]['residual'] += zone.zone_freq
            else:
                i += 1

        # move cn 1 to cn 2
        self.zones_in_layers[cn_2_layer]['zones'].extend(tmp_zone)
        self.zones_in_layers[cn_2_layer]['residual'] -= tmp_span

        self.calc_total_freq_span()

