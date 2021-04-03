from typing import List, Optional, Tuple

from src.resource_allocation.algo.frsa.utils import ConcatenateZone, Dissimilarity, LayerZone, PreallocateCZ
from src.resource_allocation.ds.frame import Layer
from src.resource_allocation.ds.ngran import GNodeB
from src.resource_allocation.ds.util_enum import Numerology
from src.resource_allocation.ds.zone import Zone


class FRSAPhase2:
    def __init__(self, nodeb: GNodeB, zones_in_layers: Tuple[LayerZone]):
        self.nb: GNodeB = nodeb
        self.zones_in_layers: Tuple[LayerZone] = zones_in_layers

    def zd(self):
        if self.nb.frame.max_layer < 2:
            return True
        is_improved: bool = True
        while is_improved:
            is_improved: bool = False
            max_dissimilarity: List[Dissimilarity] = []
            for l in range(self.nb.frame.max_layer):
                tmp_dissimilarity: float = -1
                tmp_numerology: Optional[Numerology] = None
                for numerology in Numerology:
                    dissimilarity: float = self.calc_dissimilarity(l, numerology)
                    if dissimilarity > tmp_dissimilarity:
                        tmp_dissimilarity: float = dissimilarity
                        tmp_numerology: Numerology = numerology
                max_dissimilarity.append(Dissimilarity(l, tmp_numerology, tmp_dissimilarity))

            max_dissimilarity.sort(key=lambda x: x.dissimilarity)
            zone_set: List[Dissimilarity] = []
            zone_bandwidth: List[int] = []
            residual: List[int] = []
            for i in range(2):  # pick two concatenate zone with largest dissimilarity FIXME: 假設A_1,mu包含z1, z2, z3，A_3,mu包含z4, z5，A_1,mu > A_3,mu，z1先看能不能跟z4換，如果空間不夠換，再看z1跟z5，z2跟z4，z2跟z5 ....
                zone_set.append(max_dissimilarity.pop())
                assert self.zones_in_layers[zone_set[-1].layer].layer == zone_set[-1].layer
                zone_bandwidth.append(self.zones_in_layers[zone_set[-1].layer].frequency_span[zone_set[-1].numerology])
                residual.append(self.zones_in_layers[zone_set[-1].layer].residual)
            if (zone_bandwidth[0] <= zone_bandwidth[1] + residual[1]) and (
                    zone_bandwidth[1] <= zone_bandwidth[0] + residual[0]):
                origin_ld: float = self.calc_layer_dissimilarity()
                self.swap(zone_set)
                new_ld: float = self.calc_layer_dissimilarity()
                if new_ld < origin_ld:
                    is_improved: bool = True
                else:
                    self.swap(zone_set)  # undo FIXME wrong

    def calc_dissimilarity(self, layer: int, numerology: Numerology) -> float:
        dissimilarity: float = 0.0
        for l in range(self.nb.frame.max_layer):
            if l == layer:
                continue
            dissimilarity += abs(
                self.zones_in_layers[layer].frequency_span[numerology] - self.zones_in_layers[l].frequency_span[
                    numerology])
        return dissimilarity / self.nb.frame.max_layer

    def calc_layer_dissimilarity(self) -> float:
        ld: float = 0.0
        for numerology in Numerology:
            for layer in range(self.nb.frame.max_layer):
                ld += self.calc_dissimilarity(layer, numerology)
        return ld

    def swap(self, zone_set: List[Dissimilarity]):
        zone_set[0].dissimilarity = zone_set[1].dissimilarity = -1

        # back up zone_set 0
        tmp_zone: List[Zone] = []
        i: int = 0
        assert self.zones_in_layers[zone_set[0].layer].layer == zone_set[0].layer
        for zone in self.zones_in_layers[zone_set[0].layer].zone[i:]:
            if zone.numerology == zone_set[0].numerology:
                tmp_zone.append(zone)
                self.zones_in_layers[zone_set[0].layer].remove_zone(zone)
            else:
                i += 1

        # move zone_set 1 to zone_set 0
        i: int = 0
        assert self.zones_in_layers[zone_set[1].layer].layer == zone_set[1].layer
        for zone in self.zones_in_layers[zone_set[1].layer].zone[i:]:
            if zone.numerology == zone_set[1].numerology:
                self.zones_in_layers[zone_set[0].layer].add_zone(zone)
                self.zones_in_layers[zone_set[1].layer].remove_zone(zone)
            else:
                i += 1

        # move zone_set 0 to zone_set 1
        for zone in tmp_zone:
            self.zones_in_layers[zone_set[1].layer].add_zone(zone)

    def za(self):
        # base layer
        base_layer: LayerZone = min(self.zones_in_layers, key=lambda x: len(x.zone))
        self.form_concatenate_zone()
        bl_offset: List[ConcatenateZone] = self.allocate_by_bandwidth(base_layer)

        # other layers
        for l in range(self.nb.frame.max_layer):
            assert self.zones_in_layers[l].layer == l
            if l == base_layer.layer:
                continue

            pre: PreallocateCZ = PreallocateCZ(l, self.nb.frame.frame_freq)
            for bl_cz in bl_offset:
                for cz in filter(lambda x: x.numerology == bl_cz.numerology, self.zones_in_layers[l].zone):  # only one FIXME use next()
                    pre.append_cz(cz, bl_cz.offset)  # allocate by aligning
                    cz.is_preallocate = True
            for cz in filter(lambda x: not x.is_preallocate, self.zones_in_layers[l].zone):
                pre.append_cz(cz)  # allocate by squeezing
            self.allocate_preallocate_cz(pre)

    def form_concatenate_zone(self):
        for zones_in_layer in self.zones_in_layers:
            zones_in_layer.form_concatenate_zone()

    def allocate_by_bandwidth(self, base_layer: LayerZone) -> List[ConcatenateZone]:
        layer: Layer = self.nb.frame.layer[base_layer.layer]
        base_layer.zone.sort(key=lambda x: x.bandwidth)
        numerology_offset: List[ConcatenateZone] = []
        while base_layer.zone:
            cz: ConcatenateZone = base_layer.zone.pop()     # allocate from large bandwidth concatenate zone
            cz.offset = layer.available_frequent_offset
            numerology_offset.append(cz)
            cz.allocate(layer)
        return numerology_offset

    def allocate_preallocate_cz(self, pre: PreallocateCZ):
        layer: Layer = self.nb.frame.layer[pre.layer]
        for cz in pre.cz_list:
            cz.allocate(layer)
