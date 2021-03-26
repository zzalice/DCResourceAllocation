from __future__ import annotations

import math
from typing import List, Tuple, TYPE_CHECKING, Union

from .eutran import ENodeB
from .ngran import GNodeB
from .util_enum import E_MCS, G_MCS, LTEResourceBlock, NodeBType, UEType

if TYPE_CHECKING:
    from .ue import UserEquipment
    from .util_enum import Numerology


class Zone:
    def __init__(self, ue_list: Tuple[UserEquipment, ...], nodeb: Union[ENodeB, GNodeB]):
        # make sure all UEs use the same numerology
        if nodeb.nb_type == NodeBType.G:
            assert len({ue.numerology_in_use for ue in ue_list}) <= 1
        else:
            for ue in ue_list:
                assert ue.ue_type == UEType.D or ue.ue_type == UEType.E  # TODO: refactor or redesign

        self.nodeb: Union[ENodeB, GNodeB] = nodeb
        self.ue_list: Tuple[UserEquipment] = ue_list
        self._numerology = LTEResourceBlock.E if nodeb.nb_type == NodeBType.E else ue_list[0].numerology_in_use
        # TODO: refactor or redesign

        self.zone_freq: int = 0
        self.zone_time: int = 0
        self.last_row_duration: int = 0
        self.sum_request_data_rate: int = 0
        self.calc_zone_size()

        self.priority: float = float('inf')  # for eNB in phase 2

    def merge(self, zone_to_merge: Zone, row_limit: bool = True) -> bool:
        assert zone_to_merge.numerology == self.numerology, "The zone to merge doesn't have the same numerology."
        if row_limit:
            is_mergeable: bool = zone_to_merge.last_row_duration <= self.last_row_remaining_time
        else:
            is_mergeable: bool = True
        if is_mergeable:
            self.ue_list += zone_to_merge.ue_list
            self.calc_zone_size()
        return is_mergeable

    def calc_zone_size(self):
        # calculate the total number of BU in time domain if RBs are lined in a row
        num_of_bu_time: int = 0
        for ue in self.ue_list:
            self.sum_request_data_rate += ue.request_data_rate
            num_of_rb: int = (G_MCS if self.nodeb.nb_type == NodeBType.G else E_MCS).get_worst().calc_required_rb_count(
                ue.request_data_rate)
            num_of_bu_time += num_of_rb * self.numerology.time

        self.zone_freq: int = (
                math.ceil(num_of_bu_time / self.nodeb.frame.frame_time) * self.numerology.freq)  # numbers of BU
        self.zone_time: int = self.nodeb.frame.frame_time  # numbers of BU
        self.last_row_duration: int = num_of_bu_time % self.zone_time or self.zone_time  # = zone_time when % == 0

    @property
    def numerology(self) -> Numerology:
        return self._numerology

    @property
    def is_fit(self) -> bool:
        return self.zone_freq > self.numerology.freq or self.zone_time == self.last_row_duration

    @property
    def is_half(self) -> bool:
        if self.zone_freq > self.numerology.freq or (
                self.zone_freq == self.numerology.freq and self.last_row_duration >= self.zone_time / 2):
            return True
        else:
            return False

    @property
    def last_row_remaining_time(self) -> int:
        return self.zone_time - self.last_row_duration


class _Bin:
    def __init__(self, capacity: int):
        self.capacity: int = capacity  # max size of a bin (equals to freq of the first zone)
        self.usage: int = 0
        self.zone: List[Zone] = list()

    def append_zone(self, zone: Zone) -> bool:
        is_appendable: bool = self.remaining_space >= zone.zone_freq
        if is_appendable:
            self.zone.append(zone)
            self.usage += zone.zone_freq
        return is_appendable

    @property
    def remaining_space(self) -> int:
        return self.capacity - self.usage


class ZoneGroup:
    def __init__(self, initial_zone: Zone, num_of_bins: int):
        assert num_of_bins > 0
        self.bin: Tuple[_Bin, ...] = tuple(_Bin(initial_zone.zone_freq) for _ in range(num_of_bins))
        self.priority: float = float('-inf')
        self.bin[0].append_zone(initial_zone)

    def set_priority(self, priority: float):
        assert self.priority == float('-inf')  # should be set once ONLY
        self.priority: float = priority

    @property
    def numerology(self) -> Numerology:
        return self.bin[0].zone[0].numerology
