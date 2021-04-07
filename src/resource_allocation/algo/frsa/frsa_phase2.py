from typing import List, Optional, Tuple

from src.resource_allocation.algo.frsa.utils import ConcatenateZone, Dissimilarity, LayerZone, PreallocateCZ
from src.resource_allocation.ds.frame import Layer
from src.resource_allocation.ds.ngran import GNodeB
from src.resource_allocation.ds.undo import Undo
from src.resource_allocation.ds.util_enum import Numerology
from src.resource_allocation.ds.zone import Zone


class FRSAPhase2(Undo):
    def __init__(self, nodeb: GNodeB, zones_in_layers: Tuple[LayerZone]):
        super().__init__()
        self.nb: GNodeB = nodeb
        self.zones_in_layers: Tuple[LayerZone] = zones_in_layers

    def zd(self):
        if self.nb.frame.max_layer < 2:
            return True
        is_improved: bool = True
        while is_improved:
            # calculate dissimilarity
            max_dissimilarity: List[Dissimilarity] = []
            for l in range(self.nb.frame.max_layer):
                tmp_dissimilarity: float = -1
                tmp_numerology: Optional[Numerology] = None
                for numerology in self.zones_in_layers[l].numerology_set:
                    dissimilarity: float = self.calc_dissimilarity(l, numerology)
                    if dissimilarity > tmp_dissimilarity:
                        tmp_dissimilarity: float = dissimilarity
                        tmp_numerology: Numerology = numerology
                max_dissimilarity.append(Dissimilarity(l, tmp_numerology, tmp_dissimilarity))
            assert len(max_dissimilarity) == self.nb.frame.max_layer

            # swap zones to lower down dissimilarity
            max_dissimilarity.sort(key=lambda x: x.dissimilarity)
            zone_set: List[Dissimilarity] = []
            for i in range(2):  # pick two group with largest dissimilarity
                zone_set.append(max_dissimilarity.pop())
                if zone_set[-1].numerology is None:  # empty layer
                    return True
                assert self.zones_in_layers[zone_set[-1].layer].layer == zone_set[-1].layer
            is_improved: bool = self.swap_zone_set(zone_set)

    def swap_zone_set(self, zone_set: List[Dissimilarity]) -> bool:
        """
        Swap two zones in different layers.
        :param zone_set: Two group of zones to swap.
        :return: If the dissimilarity of the frame is improved
        """
        assert zone_set[0].layer != zone_set[1].layer
        for z0 in filter(lambda x: x.numerology == zone_set[0].numerology,
                         self.zones_in_layers[zone_set[0].layer].zone):
            for z1 in filter(lambda x: x.numerology == zone_set[1].numerology,
                             self.zones_in_layers[zone_set[1].layer].zone):
                if (z0.zone_freq <= z1.zone_freq + self.zones_in_layers[zone_set[1].layer].residual) and (
                        z1.zone_freq <= z0.zone_freq + self.zones_in_layers[zone_set[0].layer].residual):
                    origin_ld: float = self.calc_layer_dissimilarity()
                    self.swap(zone_set[0], zone_set[1], z0, z1)
                    new_ld: float = self.calc_layer_dissimilarity()
                    if new_ld < origin_ld:
                        return True
                    else:
                        # undo
                        self.swap(zone_set[0], zone_set[1], z1, z0)
        return False

    def swap(self, zone_set_0: Dissimilarity, zone_set_1: Dissimilarity, z0: Zone, z1: Zone):
        self.zones_in_layers[zone_set_0.layer].remove_zone(z0)
        self.zones_in_layers[zone_set_1.layer].remove_zone(z1)
        self.zones_in_layers[zone_set_0.layer].add_zone(z1)
        self.zones_in_layers[zone_set_1.layer].add_zone(z0)

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
                cz: Optional[ConcatenateZone] = next(
                    (zone for zone in self.zones_in_layers[l].zone if zone.numerology == bl_cz.numerology), None)
                if cz:
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
            cz: ConcatenateZone = base_layer.zone.pop()  # allocate from large bandwidth concatenate zone
            cz.offset = layer.available_frequent_offset
            numerology_offset.append(cz)
            cz.allocate(layer)
        return numerology_offset

    def allocate_preallocate_cz(self, pre: PreallocateCZ):
        layer: Layer = self.nb.frame.layer[pre.layer]
        for cz in pre.cz_list:
            cz.allocate(layer)
