from __future__ import annotations

from typing import List, Optional, Tuple, TYPE_CHECKING

from .rb import ResourceBlock

if TYPE_CHECKING:
    from .ue import UserEquipment


class Frame:
    def __init__(self, freq: int = 80, time: int = 32, max_layer: int = 1):
        # i.e., one_bu = frame.layer[layer(l|MAX_LAYER)].bu[freq(i|HEIGHT)][time(j|WIDTH)]
        self.layer: Tuple[Layer, ...] = tuple(Layer(freq, time) for l in range(max_layer))


class Layer:
    def __init__(self, freq: int, time: int):
        # i.e., BU[frequency(i|HEIGHT)][time(j|WIDTH)]
        self.bu: Tuple[Tuple[BaseUnit, ...], ...] = tuple(tuple(BaseUnit() for j in range(time)) for i in range(freq))
        self.rb: List[ResourceBlock] = list()

    def allocate_resource_block(self, offset_i: int, offset_j: int, ue: UserEquipment):
        resource_block: ResourceBlock = ResourceBlock(self, offset_i, offset_j, ue)
        self.rb.append(resource_block)
        for i in range(resource_block.ue.numerology_in_use.height):
            for j in range(resource_block.ue.numerology_in_use.width):
                self.bu[offset_i + i][offset_j + j].set_up_bu(i, j, resource_block)


class BaseUnit:
    def __init__(self):
        self.relative_i: Optional[int] = None
        self.relative_j: Optional[int] = None
        self.within_rb: Optional[ResourceBlock] = None

    @property
    def is_used(self) -> bool:
        return self.within_rb is not None

    @property
    def is_at_upper_left(self) -> bool:
        # return True if this BU is at the upper left corner of the RB it belongs to
        assert self.is_used
        return self.relative_i == 0 and self.relative_j == 0

    def set_up_bu(self, relative_i: int, relative_j: int, resource_block: ResourceBlock):
        # relative position of this BU withing a RB
        assert not self.is_used
        assert relative_i >= 0 and relative_j >= 0
        self.relative_i: int = relative_i
        self.relative_j: int = relative_j
        self.within_rb: ResourceBlock = resource_block

    def clear_up_bu(self):
        assert self.is_used
        self.relative_i = self.relative_j = self.within_rb = None
