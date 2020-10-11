from typing import List, Optional, Tuple

from resource_allocation.ue import UserEquipment
from resource_allocation.util_enum import Numerology


class Frame:
    def __init__(self, freq: int = 80, time: int = 32, max_layer: int = 1):
        # i.e., one_bu = frame.layer[layer(max_layer, l)].bu[freq(height, i)][time(width, j)]
        self.layer: list[Layer] = [Layer(freq, time) for l in range(max_layer)]


class Layer:
    def __init__(self, freq: int, time: int):
        # i.e., BU[frequency(height, i)][time(width, j)]
        self.bu: List[List[BaseUnit]] = [[BaseUnit() for j in range(time)] for i in range(freq)]
        self.rb: List[ResourceBlock] = list()

    def allocate_resource_block(self, offset_i: int, offset_j: int, ue: UserEquipment):
        resource_block = ResourceBlock(self, offset_i, offset_j, ue)
        self.rb.append(resource_block)
        rb_numerology = resource_block.ue.numerology_in_use
        for i in range(0, rb_numerology.height):
            for j in range(0, rb_numerology.width):
                self.bu[offset_i + i][offset_j + j].set_up_bu(i, j, resource_block)


class ResourceBlock:
    def __init__(self, layer: Layer, i_start: int, j_start: int, ue: UserEquipment):
        self.layer: Layer = layer
        self.ue: UserEquipment = ue
        self.numerology: Numerology = ue.numerology_in_use
        self.position: Tuple[Tuple[int, int], Tuple[int, int]] = self.update_position(i_start, j_start)

    def update_position(self, i_start: int, j_start: int) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        pos_start = (i_start, j_start)
        pos_end = (i_start + self.numerology.height - 1, j_start + self.numerology.width - 1)
        return pos_start, pos_end

    @property
    def i_start(self) -> int:
        return self.position[0][0]

    @property
    def i_end(self) -> int:
        return self.position[1][0]

    @property
    def j_start(self) -> int:
        return self.position[0][1]

    @property
    def j_end(self) -> int:
        return self.position[1][1]


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
