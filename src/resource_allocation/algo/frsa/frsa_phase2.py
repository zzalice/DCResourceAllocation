from copy import deepcopy
from typing import Dict, List, Optional, Tuple, Union

from src.resource_allocation.ds.frame import Layer
from src.resource_allocation.ds.ngran import GNodeB
from src.resource_allocation.ds.util_enum import Numerology
from src.resource_allocation.ds.zone import Zone


class ConcatenateZone:
    def __init__(self, zone: Zone):
        self.zone: List[Zone] = [zone]
        self._numerology: Numerology = zone.numerology

    @property
    def bandwidth(self) -> int:
        bw: int = 0
        for z in self.zone:
            bw += z.zone_freq
        return bw

    @property
    def numerology(self) -> Numerology:
        return self._numerology

    def allocate(self, layer: Layer, offset: Optional[int]):
        is_first: bool = True
        for zone in self.zone:
            if is_first:
                is_first: bool = False
            else:
                offset = None
            layer.allocate_zone(zone, offset)


class PreallocateCZ:
    def __init__(self, layer: int, freq: int):
        self.layer: int = layer
        self.frame_freq: int = freq  # gNB BW
        self.cz_list: List[Dict[str, Union[
            int, ConcatenateZone]]] = []  # In the order of offset. [{'offset': int, 'cz': ConcatenateZone}, {}, ...]

    def append_cz(self, cz: ConcatenateZone, offset: Optional[int] = None):
        if offset is None:
            offset: int = self.cz_list[-1]['offset'] + self.cz_list[-1]['cz'].bandwidth
        self.cz_list.append({'offset': offset, 'cz': cz})
        self.check_out_of_bound(-1)

    def check_out_of_bound(self, index: int):
        while True:
            self.assert_cz_list()
            edge: int = self.cz_list[index]['offset'] + self.cz_list[index]['cz'].bandwidth - 1
            if edge > self.frame_freq:
                self.shift(index)
            else:
                return True

    def shift(self, index: int):
        assert index > 0 or (index == 0 and self.cz_list[0]['offset'] > 0), 'Can not shift.'

        # shift
        self.cz_list[index]['offset'] -= 1

        # check invalid overlapped
        edge_of_last_cz: int = self.cz_list[index - 1]['offset'] + self.cz_list[index - 1]['cz'].bandwidth - 1
        if self.cz_list[index]['offset'] <= edge_of_last_cz:  # lapped
            self.shift(index - 1)
        else:
            return True

    def assert_cz_list(self):
        assert self.cz_list[0]['offset'] >= 0
        for i, cz in enumerate(self.cz_list[1:]):
            last_cz: Dict[str, Union[int, ConcatenateZone]] = self.cz_list[i]
            assert cz['offset'] > last_cz['offset'] + last_cz['cz'].bandwidth - 1


Dissimilarity = Dict[int, List[Union[Numerology, float]]]  # {layer: [Numerology, 0.0]}
LayerZone = Tuple[Dict[str, Union[int, List[Union[Zone, ConcatenateZone]]]], ...
]  # ({'layer': int, 'residual': int, 'zones': List[Zone/ConcatenateZone]},...) The Dict is in the order of layer index


class FRSAPhase2:
    def __init__(self, nodeb: GNodeB, zones_in_layers: LayerZone):
        self.nb: GNodeB = nodeb
        self.zones_in_layers: LayerZone = zones_in_layers
        self.freq_span: List[Dict[Numerology, int]] = []

    def zd(self):
        if self.nb.frame.max_layer < 2:
            return True
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
            for i in range(2):  # pick two concatenate zone with largest dissimilarity FIXME: 假設A_1,mu包含z1, z2, z3，A_3,mu包含z4, z5，A_1,mu > A_3,mu，z1先看能不能跟z4換，如果空間不夠換，再看z1跟z5，z2跟z4，z2跟z5 ....
                cn.append(max_dissimilarity.popitem())
                k.append(self.freq_span[cn[-1][0]][cn[-1][1][0]])  # layer = cn[-1][0], numerology = cn[-1][1][0]
                assert self.zones_in_layers[cn[-1][0]]['layer'] == cn[-1][0]
                residual.append(self.zones_in_layers[cn[-1][0]]['residual'])
            if k[0] <= k[1] + residual[1] and k[1] <= k[0] + residual[0]:
                origin_ld: float = self.calc_layer_dissimilarity(self.freq_span)
                freq_span = self.displace_zone(cn)
                new_ld: float = self.calc_layer_dissimilarity(freq_span)
                if new_ld < origin_ld:
                    self.update_zones_in_layers(cn)
                    assert False not in [self.freq_span[i][j] == freq_span[i][j] for i, d in enumerate(self.freq_span)
                                         for j in d]
                    is_improved: bool = True

    def calc_total_freq_span(self):
        self.freq_span: List[Dict[Numerology, int]] = [
            {numerology: 0 for numerology in Numerology.gen_candidate_set()} for _ in
            range(self.nb.frame.max_layer)]
        for l, zone_in_l in enumerate(self.zones_in_layers):
            assert self.zones_in_layers[l]['layer'] == l
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
        assert self.zones_in_layers[cn_1_layer]['layer'] == cn_1_layer
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
        assert self.zones_in_layers[cn_2_layer]['layer'] == cn_2_layer
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

    def za(self):
        # base layer
        base_layer: Dict[str, Union[int, List[Zone]]] = min(self.zones_in_layers, key=lambda x: len(x['zones']))
        self.form_concatenate_zone()
        bl_offset: Dict[Numerology, int] = self.allocate_by_bandwidth(base_layer)

        # other layers
        for l in range(self.nb.frame.max_layer):
            assert self.zones_in_layers[l]['layer'] == l
            if l == base_layer['layer']:
                continue

            pre: PreallocateCZ = PreallocateCZ(l, self.nb.frame.frame_freq)
            for bl_numerology in bl_offset:
                for cz in filter(lambda x: x.numerology == bl_numerology, self.zones_in_layers[l]['zones']):  # only one
                    pre.append_cz(cz, bl_offset[bl_numerology])  # allocate by aligning
                    self.zones_in_layers[l]['zones'].remove(cz)
            for cz in self.zones_in_layers[l]['zones']:
                pre.append_cz(cz)  # allocate by squeezing
            self.allocate_preallocate_cz(pre)

    def form_concatenate_zone(self):
        for zones_in_layer in self.zones_in_layers:
            if not zones_in_layer['zones']:  # if is empty
                continue
            zones_in_layer['zones'].sort(key=lambda x: x.numerology.mu)
            concatenate: List[ConcatenateZone] = [ConcatenateZone(zones_in_layer['zones'].pop())]
            while zones_in_layer['zones']:
                zone: Zone = zones_in_layer['zones'].pop()
                if zone.numerology == concatenate[-1].numerology:
                    concatenate[-1].zone.append(zone)
                else:
                    concatenate.append(ConcatenateZone(zone))
            zones_in_layer['zones'] = concatenate

    def allocate_by_bandwidth(self, base_layer: Dict[str, Union[int, List[ConcatenateZone]]]) -> Dict[Numerology, int]:
        layer: Layer = self.nb.frame.layer[base_layer['layer']]
        base_layer['zones'].sort(key=lambda x: x.bandwidth)
        numerology_offset = {}
        while base_layer['zones']:
            cz: ConcatenateZone = base_layer['zones'].pop()
            numerology_offset[cz.numerology] = layer.available_frequent_offset
            cz.allocate(layer, None)  # allocate from large bandwidth concatenate zone
        return numerology_offset

    def allocate_preallocate_cz(self, pre: PreallocateCZ):
        layer: Layer = self.nb.frame.layer[pre.layer]
        for cz_dict in pre.cz_list:
            cz_dict['cz'].allocate(layer, cz_dict['offset'])
