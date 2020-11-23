from __future__ import annotations

import math
from typing import List, Tuple, TYPE_CHECKING, Union

from .eutran import ENodeB
from .ngran import GNodeB
from .util_enum import LTEPhysicalResourceBlock, NodeBType

if TYPE_CHECKING:
    from .ue import UserEquipment
    from .util_enum import Numerology


class Zone:
    def __init__(self, ue_list: Tuple[UserEquipment, ...], nodeb: Union[ENodeB, GNodeB]):
        assert len({ue.numerology_in_use for ue in ue_list}) == 1  # make sure all UEs use the same numerology
        self.ue_list: Tuple[UserEquipment] = ue_list

        self._numerology = LTEPhysicalResourceBlock.E if nodeb.nb_type == NodeBType.E else ue_list[0].numerology_in_use
        # TODO: refactor or redesign

        num_of_bu_time: int = sum([(ue.gnb_info if nodeb.nb_type == NodeBType.G else ue.enb_info).num_of_rb
                                   * ue.numerology_in_use.time for ue in ue_list])
        self.zone_freq: int = (
                math.ceil(num_of_bu_time / nodeb.frame.frame_time) * self.numerology.freq)  # numbers of BU
        self.zone_time: int = nodeb.frame.frame_time  # numbers of BU
        self.last_row_duration: int = num_of_bu_time % self.zone_time or self.zone_time  # = zone_time when % == 0

    def merge(self, zone_to_merge: Zone) -> bool:
        is_mergeable: bool = zone_to_merge.last_row_duration <= self.last_row_remaining_time
        if is_mergeable:
            self.ue_list += zone_to_merge.ue_list
            self.last_row_duration += zone_to_merge.last_row_duration
        return is_mergeable

    @property
    def numerology(self) -> Numerology:
        return self._numerology

    @property
    def is_fit(self) -> bool:
        return self.zone_freq > self.numerology.freq or self.zone_time == self.last_row_duration

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
