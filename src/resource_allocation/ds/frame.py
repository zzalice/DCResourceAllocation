from __future__ import annotations

from typing import List, Optional, Tuple, TYPE_CHECKING

from .rb import ResourceBlock
from .util_enum import LTEPhysicalResourceBlock, NodeBType, Numerology, UEType

if TYPE_CHECKING:
    from .nodeb import NodeB
    from .ue import UserEquipment


class Frame:
    def __init__(self, freq: int, time: int, max_layer: int, nodeb: NodeB):
        # i.e., one_bu = frame.layer[layer(l|MAX_LAYER)].bu[freq(i|HEIGHT)][time(j|WIDTH)]
        self.layer: Tuple[Layer, ...] = tuple(Layer(freq, time, nodeb) for _ in range(max_layer))

        self._max_layer: int = max_layer

    @property
    def frame_freq(self) -> int:
        return self.layer[0].FREQ

    @property
    def frame_time(self) -> int:
        return self.layer[0].TIME


class Layer:
    def __init__(self, freq: int, time: int, nodeb: NodeB):
        # i.e., BU[frequency(i|HEIGHT)][time(j|WIDTH)]
        self.FREQ: int = freq
        self.TIME: int = time
        self.nodeb: NodeB = nodeb
        self.bu: Tuple[Tuple[_BaseUnit, ...], ...] = tuple(tuple(_BaseUnit() for _ in range(time)) for _ in range(freq))
        self.rb: List[ResourceBlock] = list()

        self._available_frequent_offset: int = 0
        self._cache_is_valid: bool = False  # valid bit (for _available_block)
        self._bu_status: Tuple[Tuple[bool, ...], ...] = tuple()

    def allocate_resource_block(self, offset_i: int, offset_j: int, ue: UserEquipment):
        tmp_numerology: Numerology = ue.numerology_in_use
        if self.nodeb.nb_type == NodeBType.E and ue.ue_type == UEType.D:
            ue.numerology_in_use = LTEPhysicalResourceBlock.E  # TODO: refactor or redesign

        self._available_frequent_offset = offset_i + ue.numerology_in_use.freq
        assert self._available_frequent_offset <= self.FREQ and offset_j + ue.numerology_in_use.time <= self.TIME
        self._cache_is_valid: bool = False  # set cache as invalid (for _available_block)
        resource_block: ResourceBlock = ResourceBlock(self, offset_i, offset_j, ue)
        self.rb.append(resource_block)

        for i in range(ue.numerology_in_use.freq):
            for j in range(ue.numerology_in_use.time):
                self.bu[offset_i + i][offset_j + j].set_up_bu(i, j, resource_block)

        ue.numerology_in_use = tmp_numerology  # restore

    @property
    def available_bandwidth(self):
        return self.FREQ - self._available_frequent_offset

    @property
    def bu_status(self) -> Tuple[Tuple[bool, ...], ...]:
        if not self._cache_is_valid:
            self._bu_status = tuple(tuple(column.is_used for column in row) for row in self.bu)
            self._cache_is_valid: bool = True
        return self._bu_status

    @property
    def available_blocks(self):
        raise NotImplementedError  # TODO: not decided how to implement yet


class _BaseUnit:
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
