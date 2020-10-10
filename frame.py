from typing import List, Optional
from util_enum import Numerology
from ue import UserEquipment


class BaseUnit:
    def __init__(self):
        self.x: Optional[int] = None
        self.y: Optional[int] = None
        self.ue: Optional[UserEquipment] = None
        self.numerology: Optional[Numerology] = None

    @property
    def is_used(self) -> bool:
        return self.ue is not None

    @property
    def is_at_upper_left(self) -> bool:
        # return True if this BU is at the upper left corner of the RB it belongs to
        return self.x == 0 and self.y == 0

    def set_up_bu(self, x: int, y: int, ue: UserEquipment, numerology: Numerology):
        self.x, self.y = x, y  # relative position of this BU withing a RB
        self.ue = ue
        self.numerology = numerology

    def clear_up_bu(self):
        self.x = self.y = None
        self.ue = self.numerology = None


class Layer:
    def __init__(self, freq: int = 80, time: int = 32):
        # i.e., BU[frequency(height)][time(width)]
        self.bu_matrix: List[List[BaseUnit]] = [[BaseUnit() for j in range(time)] for i in range(freq)]


class Frame:
    def __init__(self, max_layer: int = 3):
        self.layer: list = [Layer() for l in range(max_layer)]  # i.e., BU[layer][freq][time]
