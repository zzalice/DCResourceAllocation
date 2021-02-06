import math
from typing import List, Tuple, Union

from src.resource_allocation.ds.eutran import ENodeB
from src.resource_allocation.ds.ngran import GNodeB
from src.resource_allocation.ds.util_enum import NodeBType
from src.resource_allocation.ds.zone import Zone, ZoneGroup


class Phase2:
    def __init__(self, nodeb: Union[GNodeB, ENodeB]):
        self.nodeb: Union[GNodeB, ENodeB] = nodeb

    def calc_layer_using(self, zone_wide: Tuple[Zone, ...]) -> int:
        layer_using: int = min(
            math.ceil(sum(zone.zone_freq for zone in zone_wide) / self.nodeb.frame.frame_freq),
            len(self.nodeb.frame.layer))
        return layer_using

    @staticmethod
    def form_group(zone_wide: Tuple[Zone, ...], layer_using: int) -> Tuple[ZoneGroup, ...]:
        zone_groups: List[ZoneGroup] = list()
        zone_wide: List[Zone] = sorted(zone_wide, key=lambda x: x.zone_freq, reverse=True)
        for zone in zone_wide:
            is_grouped: bool = False
            for zone_group in filter(lambda x: x.numerology == zone.numerology, zone_groups):
                for bin_ in zone_group.bin:
                    if is_grouped := bin_.append_zone(zone):
                        break
                if is_grouped:
                    break
            if not is_grouped:
                zone_groups.append(ZoneGroup(zone, layer_using))
        return tuple(zone_groups)

    @staticmethod
    def calc_residual_degree(zone_groups: Tuple[ZoneGroup, ...]) -> Tuple[ZoneGroup, ...]:
        for zone_group in zone_groups:
            residual_degree: int = 0
            for idx_layer, bin_ in enumerate(zone_group.bin[1:]):
                residual_degree += 1 / (idx_layer + 1) * bin_.remaining_space
            zone_group.set_priority(residual_degree)
        return zone_groups

    def allocate_zone_group(self, zone_groups: Tuple[ZoneGroup, ...]) -> Tuple[List[List[Zone]], Tuple[Zone, ...]]:
        # the idea of first allocate by degree then by BW
        zone_groups: List[ZoneGroup] = sorted(zone_groups, key=lambda x: x.bin[0].zone[0].zone_freq, reverse=True)
        zone_groups: List[ZoneGroup] = sorted(zone_groups, key=lambda x: x.priority, reverse=False)

        zone_allocated: List[List[Zone]] = [[], [], []]
        zone_unallocated: List[Zone] = []
        for zone_group in zone_groups:
            if self.nodeb.frame.layer[0].available_bandwidth >= zone_group.bin[0].capacity:
                for layer, bin_ in enumerate(zone_group.bin):
                    for zone in bin_.zone:
                        self.nodeb.frame.layer[layer].allocate_zone(zone)
                    zone_allocated[layer].extend(bin_.zone)
            else:
                # collect the zones not allocated
                for bin_ in zone_group.bin:
                    zone_unallocated.extend(bin_.zone)

        for layer in self.nodeb.frame.layer:
            layer.purge_undo()
        return zone_allocated, tuple(zone_unallocated)

    def allocate_zone_to_layer(self, nb_type: NodeBType, zone_allocated: List[List[Zone]],
                               zone_unallocated: Tuple[Zone, ...]) -> List[List[Zone]]:
        zone_unallocated: List[Zone] = sorted(zone_unallocated, key=lambda x: x.zone_freq, reverse=True)
        if nb_type == NodeBType.E:
            zone_unallocated: List[Zone] = self.calc_residual_degree_enb(zone_unallocated)
            zone_unallocated.sort(key=lambda x: x.priority)

        for zone in zone_unallocated:
            for layer in self.nodeb.frame.layer:
                if layer.allocate_zone(zone):
                    zone_allocated[layer.layer_index].append(zone)
                    break

        for layer in self.nodeb.frame.layer:
            layer.purge_undo()
        return zone_allocated

    @staticmethod
    def calc_residual_degree_enb(zone_unallocated: List[Zone]) -> List[Zone]:
        for zone in zone_unallocated:
            zone.priority = zone.last_row_remaining_time / (zone.zone_freq * zone.zone_time)
        return zone_unallocated
