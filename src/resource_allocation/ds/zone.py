from __future__ import annotations

from typing import List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .enum import Numerology
    from .ue import UserEquipment


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


class ZoneGroup:
    def __init__(self, initial_zone: Zone, num_of_bins: int):
        self.bin_capacity: int = initial_zone.bandwidth
        self.bin: Tuple[List[Zone], ...] = tuple(list() for i in range(num_of_bins))
        self.priority: float = float('-inf')

        self.bin[0].append(initial_zone)

    def append_zone(self, zone: Zone, target_bin: int):
        assert target_bin > 0
        self.bin[target_bin].append(zone)

    def set_priority(self, priority: float):
        assert self.priority == float('-inf')  # should be set once ONLY
        self.priority: float = priority
