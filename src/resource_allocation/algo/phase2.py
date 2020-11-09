import math
from typing import List, Tuple, Union

from src.resource_allocation.ds.eutran import EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.resource_allocation.ds.util_enum import UEType
from src.resource_allocation.ds.zone import Zone, ZoneGroup


class Phase2:
    def __init__(self, nodeb):
        self.nodeb = nodeb
        self._layer_using: int = 0

    def _allocate_zone(self, layer: int, offset_i: int, zone: Zone):
        bu_i = offset_i
        bu_j = 0
        for ue in zone.ue_list:
            for idx_ue_rb in range((ue.gnb_info if isinstance(self.nodeb, GNodeB) else ue.enb_info).num_of_rb):
                # check if the space is empty
                self.nodeb.frame.layer[layer].allocate_resource_block(bu_i, bu_j, ue)
                if bu_j + zone.numerology.time < self.nodeb.frame.frame_time:
                    bu_j += zone.numerology.time  # TODO: is the numerology correct in 4G?
                elif bu_j + zone.numerology.time == self.nodeb.frame.frame_time:
                    bu_i += zone.numerology.freq  # TODO: is the numerology correct in 4G?
                    bu_j = 0
                else:
                    raise Exception("RB allocate error: index increase error")

        # check if the allocated zone is in the expected range
        if bu_j == 0:
            bu_j = self.nodeb.frame.frame_time
        else:
            bu_i += zone.numerology.freq  # TODO: is the numerology correct in 4G?
        assert bu_i - offset_i == zone.zone_freq  # the allocated zone is in the expected bandwidth
        assert bu_j == zone.last_row_duration  # the allocated zone has the expected remaining space

    def calc_layer_using(self, zone_wide: Tuple[Zone, ...]):
        self._layer_using: int = min(
            math.ceil(sum(zone.zone_freq for zone in zone_wide) / self.nodeb.frame.frame_freq),
            len(self.nodeb.frame.layer))

    def form_group(self, zone_wide: Tuple[Zone, ...]) -> Tuple[ZoneGroup, ...]:
        zone_groups: List[ZoneGroup, ...] = list()
        zone_wide = sorted(zone_wide, key=lambda x: x.zone_freq, reverse=True)
        for zone in zone_wide:
            is_grouped: bool = False
            for zone_group in filter(lambda x: x.numerology == zone.numerology, zone_groups):
                for bin_ in zone_group.bin:
                    if is_grouped := bin_.append_zone(zone):
                        break
                if is_grouped:
                    break
            if not is_grouped:
                zone_groups.append(ZoneGroup(zone, self._layer_using))
        return tuple(zone_groups)

    @staticmethod
    def calc_residual_degree(zone_groups: Tuple[ZoneGroup, ...]) -> Tuple[ZoneGroup, ...]:
        for zone_group in zone_groups:
            residual_degree: int = 0
            for idx, bin_ in enumerate(zone_group.bin[1:]):
                residual_degree += 1 / (idx + 1) * bin_.remaining_space
            zone_group.set_priority(residual_degree)
        # the idea of first allocate by degree then by BW
        zone_groups = sorted(zone_groups, key=lambda x: x.bin[0].zone[0].zone_freq, reverse=True)
        zone_groups = sorted(zone_groups, key=lambda x: x.priority, reverse=False)
        return tuple(zone_groups)

    def allocate_zone_group(self, zone_groups: Tuple[ZoneGroup, ...]) -> Tuple[Zone, ...]:
        # TODO assert sorted zone_groups
        idx_unallocated_zone_group: int = 0
        for idx, zone_group in enumerate(zone_groups):
            if self.nodeb.frame.layer[0].available_bandwidth < zone_group.bin[0].capacity:
                idx_unallocated_zone_group = idx
                break
            for layer, bin_ in enumerate(zone_group.bin):
                for zone in bin_.zone:
                    self._allocate_zone(layer, self.nodeb.frame.layer[layer].available_frequent_offset, zone)

        # collect the zones not allocated
        zone_unallocated: List[Zone, ...] = list()
        for zone_group in zone_groups[idx_unallocated_zone_group:]:
            for bin_ in zone_group.bin:
                zone_unallocated.extend(bin_.zone)
        return tuple(zone_unallocated)

    def allocate_zone_to_layers(self, zone_set: Tuple[Zone, ...]) -> Tuple[
        Tuple[Union[GUserEquipment, EUserEquipment], ...], Tuple[DUserEquipment, ...]]:
        zone_set = sorted(zone_set, key=lambda x: x.zone_freq, reverse=True)
        single_connection_ue_list_unallocated: List[Union[GUserEquipment, EUserEquipment], ...] = list()
        d_ue_list_unallocated: List[DUserEquipment, ...] = list()
        for zone in zone_set:
            is_allocated: bool = False
            for idx_layer, layer in enumerate(self.nodeb.frame.layer):
                if layer.available_bandwidth > zone.zone_freq:
                    self._allocate_zone(idx_layer, layer.available_frequent_offset, zone)
                    is_allocated: bool = True

            # collect the UEs not allocated
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
        single_connection_ue_list_unallocated = list(single_connection_ue_list_unallocated)
        d_ue_list_unallocated = list(d_ue_list_unallocated)
        for zone in zone_narrow:
            for ue in zone.ue_list:
                if isinstance(ue, (GUserEquipment, EUserEquipment)):
                    single_connection_ue_list_unallocated.append(ue)
                elif isinstance(ue, DUserEquipment):
                    d_ue_list_unallocated.append(ue)
        return tuple(single_connection_ue_list_unallocated), tuple(d_ue_list_unallocated)
