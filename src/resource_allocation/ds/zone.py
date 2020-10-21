from __future__ import annotations

from typing import List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .ue import UserEquipment
    from .util_enum import Numerology


class Zone:
    def __init__(self, user_equipments: Tuple[UserEquipment, ...], bandwidth: int, duration: int, frame_time: int):
        assert len({ue.numerology_in_use for ue in user_equipments}) == 1  # make sure all UEs use the same numerology
        self.ue_list: List[UserEquipment] = list(user_equipments)
        self.bandwidth: int = bandwidth
        self.duration: int = duration  # TODO!!: should be calculated with UE info (how about 4G vs. 5G?)
        self.frame_time: int = frame_time

    @property
    def numerology(self) -> Numerology:
        return self.ue_list[0].numerology_in_use

    @property
    def is_full(self) -> bool:
        raise NotImplementedError  # TODO!: should be implemented


class _Bin:
    def __init__(self, capacity: int):
        self.capacity: int = capacity  # max size of a bin (equals to bandwidth of first zone)
        self.usage: int = 0
        self.zone: List[Zone] = list()

    def append_zone(self, zone: Zone) -> bool:
        is_appendable: bool = self.capacity - self.usage >= zone.bandwidth
        if is_appendable:
            self.zone.append(zone)
            self.usage += zone.bandwidth
        return is_appendable


class ZoneGroup:
    def __init__(self, initial_zone: Zone, num_of_bins: int):
        self.bin: Tuple[_Bin, ...] = tuple(_Bin(initial_zone.bandwidth) for i in range(num_of_bins))
        self.priority: float = float('-inf')
        self.bin[0].append_zone(initial_zone)

    def append_zone(self, zone: Zone, target_bin: int) -> bool:
        assert target_bin > 0
        return self.bin[target_bin].append_zone(zone)  # return True when append succeed

    def set_priority(self, priority: float):
        assert self.priority == float('-inf')  # should be set once ONLY
        self.priority: float = priority
