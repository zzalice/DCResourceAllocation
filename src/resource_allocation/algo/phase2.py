import math
from typing import List, Tuple, Union

from src.resource_allocation.ds.eutran import EUserEquipment
from src.resource_allocation.ds.frame import Layer
from src.resource_allocation.ds.ngran import DUserEquipment, GUserEquipment
from src.resource_allocation.ds.util_enum import NodeBType, UEType
from src.resource_allocation.ds.zone import Zone, ZoneGroup


class Phase2:
    def __init__(self, nodeb: Union[NodeBType.G, NodeBType.E]):
        self.nodeb: NodeBType = nodeb

    def _allocate_zone(self, layer: Layer, zone: Zone):
        bu_i: int = layer.available_frequent_offset
        bu_j: int = 0
        for ue in zone.ue_list:
            for idx_ue_rb in range((ue.gnb_info if self.nodeb.nb_type == NodeBType.G else ue.enb_info).num_of_rb):
                layer.allocate_resource_block(bu_i, bu_j, ue)
                if bu_j + zone.numerology.time < self.nodeb.frame.frame_time:
                    bu_j += zone.numerology.time  # TODO: is the numerology correct in 4G?
                elif bu_j + zone.numerology.time == self.nodeb.frame.frame_time:
                    bu_i += zone.numerology.freq  # TODO: is the numerology correct in 4G?
                    bu_j: int = 0
                else:
                    raise Exception("RB allocate error: index increase error")

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

    def allocate_zone_group(self, zone_groups: Tuple[ZoneGroup, ...]) -> Tuple[Zone, ...]:
        # the idea of first allocate by degree then by BW
        zone_groups: List[ZoneGroup] = sorted(zone_groups, key=lambda x: x.bin[0].zone[0].zone_freq, reverse=True)
        zone_groups: List[ZoneGroup] = sorted(zone_groups, key=lambda x: x.priority, reverse=False)

        idx_unallocated_zone_group: int = 0
        for idx, zone_group in enumerate(zone_groups):
            if self.nodeb.frame.layer[0].available_bandwidth < zone_group.bin[0].capacity:
                idx_unallocated_zone_group = idx
                break
            for layer, bin_ in enumerate(zone_group.bin):
                for zone in bin_.zone:
                    self._allocate_zone(self.nodeb.frame.layer[layer], zone)

        # collect the zones not allocated
        zone_unallocated: List[Zone, ...] = list()
        for zone_group in zone_groups[idx_unallocated_zone_group:]:
            for bin_ in zone_group.bin:
                zone_unallocated.extend(bin_.zone)
        return tuple(zone_unallocated)

    def allocate_zone_to_layer(self, zone_set: Tuple[Zone, ...]) -> Tuple[
                                Tuple[Union[GUserEquipment, EUserEquipment], ...], Tuple[DUserEquipment, ...]]:
        zone_set = sorted(zone_set, key=lambda x: x.zone_freq, reverse=True)
        single_connection_ue_list_unallocated: List[Union[GUserEquipment, EUserEquipment]] = list()
        d_ue_list_unallocated: List[DUserEquipment] = list()
        for zone in zone_set:
            is_allocated: bool = False
            for layer in self.nodeb.frame.layer:
                # TODO: is done in _allocate_zone(). If _allocate_zone returns true...
                if layer.available_bandwidth > zone.zone_freq:
                    self._allocate_zone(layer, zone)
                    is_allocated: bool = True

            # collect the UEs not allocated    # TODO: do this in data structure
            if not is_allocated:
                for ue in zone.ue_list:
                    if ue.ue_type == UEType.D:
                        ue: DUserEquipment
                        d_ue_list_unallocated.append(ue)
                    else:
                        ue: Union[GUserEquipment, EUserEquipment]
                        single_connection_ue_list_unallocated.append(ue)
        return tuple(single_connection_ue_list_unallocated), tuple(d_ue_list_unallocated)

    @staticmethod
    def collect_unallocated_ue(zone_narrow: Tuple[Zone, ...],
                               single_connection_ue_list_unallocated: Tuple[Union[GUserEquipment, EUserEquipment], ...],
                               d_ue_list_unallocated: Tuple[DUserEquipment, ...]) -> Tuple[
                               Tuple[Union[GUserEquipment, DUserEquipment], ...], Tuple[DUserEquipment, ...]]:
        # TODO: do this in data structure
        single_connection_ue_list_unallocated = list(single_connection_ue_list_unallocated)
        d_ue_list_unallocated = list(d_ue_list_unallocated)
        for zone in zone_narrow:
            for ue in zone.ue_list:
                if isinstance(ue, (GUserEquipment, EUserEquipment)):
                    single_connection_ue_list_unallocated.append(ue)
                elif isinstance(ue, DUserEquipment):
                    d_ue_list_unallocated.append(ue)
        return tuple(single_connection_ue_list_unallocated), tuple(d_ue_list_unallocated)
