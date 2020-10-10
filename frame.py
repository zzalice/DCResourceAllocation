from typing import List, Optional

from ue import UserEquipment
from util_enum import Numerology


class Frame:
    def __init__(self, freq: int = 80, time: int = 32, max_layer: int = 1):
        # i.e., one_bu = frame.layer[layer(max_layer, l)].bu[freq(height, i)][time(width, j)]
        self.layer: list[Layer] = [Layer(freq, time) for l in range(max_layer)]


class Layer:
    def __init__(self, freq: int, time: int):
        # i.e., BU[frequency(height, i)][time(width, j)]
        self.bu: List[List[BaseUnit]] = [[BaseUnit() for j in range(time)] for i in range(freq)]

    def allocate_resource_block(self, offset_i: int, offset_j: int, ue: UserEquipment):
        resource_block = ResourceBlock(self, offset_i, offset_j, ue)
        rb_numerology = resource_block.ue.numerology_in_use.value
        for i in range(0, rb_numerology['HEIGHT']):
            for j in range(0, rb_numerology['WIDTH']):
                self.bu[offset_i + i][offset_j + j].set_up_bu(i, j, resource_block)


class ResourceBlock:
    def __init__(self, layer: Layer, starting_i: int, starting_j: int, ue: UserEquipment):
        self.layer: Layer = layer
        # starting position of this RB withing a Layer
        self.starting_i: int = starting_i
        self.starting_j: int = starting_j
        self.ue: UserEquipment = ue
        self.numerology: Numerology = ue.numerology_in_use


class BaseUnit:
    def __init__(self):
        self.relative_i: Optional[int] = None
        self.relative_j: Optional[int] = None
        self.rb: Optional[ResourceBlock] = None

    @property
    def is_used(self) -> bool:
        return self.rb is not None

    @property
    def is_at_upper_left(self) -> bool:
        # return True if this BU is at the upper left corner of the RB it belongs to
        return self.relative_i == 0 and self.relative_j == 0

    def set_up_bu(self, relative_i: int, relative_j: int, resource_block: ResourceBlock):
        # relative position of this BU withing a RB
        self.relative_i, self.relative_j = relative_i, relative_j

        assert not self.is_used
        self.rb = resource_block

    def clear_up_bu(self):
        self.relative_i = self.relative_j = self.rb = None
