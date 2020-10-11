from typing import List, Tuple

from ue import UserEquipment
from util_enum import Numerology


class Zone:
    def __init__(self, user_equipments: Tuple[UserEquipment], bandwidth: int):
        assert len({ue.numerology_in_use for ue in user_equipments}) == 1  # make sure all UEs use the same numerology

        self.ue_list: List[UserEquipment] = list(user_equipments)
        self.numerology: Numerology = user_equipments[0].numerology_in_use
        self.bandwidth: int = bandwidth


class ZoneGroup:
    def __init__(self, initial_zone: Zone, num_of_bins: int):
        self.bin_capacity: int = initial_zone.bandwidth
        self.bin: List[List[Zone]] = [[] for i in range(num_of_bins)]
        self.priority: float = float('-inf')

        self.bin[0].append(initial_zone)

    def set_priority(self, priority: float):
        assert self.priority == float('-inf')  # should be set once ONLY
        self.priority = priority
