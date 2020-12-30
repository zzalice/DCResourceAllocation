from __future__ import annotations

from typing import List, Optional, Tuple, TYPE_CHECKING, Union

from .rb import ResourceBlock
from .util_enum import E_MCS, G_MCS, LTEPhysicalResourceBlock, NodeBType, Numerology, UEType

if TYPE_CHECKING:
    from .eutran import ENodeB
    from .ngran import GNodeB
    from .nodeb import NodeB
    from .ue import UserEquipment
    from .zone import Zone


class Frame:
    def __init__(self, freq: int, time: int, max_layer: int, nodeb: NodeB):
        # i.e., one_bu = frame.layer[layer(l|MAX_LAYER)].bu[freq(i|HEIGHT)][time(j|WIDTH)]
        self.layer: Tuple[Layer, ...] = tuple(Layer(i, freq, time, nodeb) for i in range(max_layer))
        self._max_layer: int = max_layer
        self._cochannel_offset: int = 0

    @property
    def frame_freq(self) -> int:
        return self.layer[0].FREQ

    @property
    def frame_time(self) -> int:
        return self.layer[0].TIME

    @property
    def max_layer(self) -> int:
        return self._max_layer

    @property
    def cochannel_offset(self) -> int:
        return self._cochannel_offset

    @cochannel_offset.setter
    def cochannel_offset(self, value):
        self._cochannel_offset = value


class Layer:
    def __init__(self, layer_index: int, freq: int, time: int, nodeb: NodeB):
        # i.e., BU[frequency(i|HEIGHT)][time(j|WIDTH)]
        self.layer_index: int = layer_index
        self.FREQ: int = freq
        self.TIME: int = time
        self.nodeb: NodeB = nodeb
        self.bu: Tuple[Tuple[BaseUnit, ...], ...] = tuple(
            tuple(BaseUnit(i, j, self) for j in range(time)) for i in range(freq))

        self._available_frequent_offset: int = 0
        self._cache_is_valid: bool = False  # valid bit (for _available_block)
        self._bu_status: Tuple[Tuple[bool, ...], ...] = tuple()

    def allocate_resource_block(self, offset_i: int, offset_j: int, ue: UserEquipment) -> Optional[ResourceBlock]:
        tmp_numerology: Numerology = ue.numerology_in_use
        if self.nodeb.nb_type == NodeBType.E and ue.ue_type == UEType.D:
            ue.numerology_in_use = LTEPhysicalResourceBlock.E  # TODO: refactor or redesign

        assert offset_i + ue.numerology_in_use.freq <= self.FREQ and offset_j + ue.numerology_in_use.time <= self.TIME, "The RB is not in the legal domain of the frame."

        resource_block: ResourceBlock = ResourceBlock(self, offset_i, offset_j, ue)
        for i in range(ue.numerology_in_use.freq):
            for j in range(ue.numerology_in_use.time):
                bu: BaseUnit = self.bu[offset_i + i][offset_j + j]
                for overlapped_rb in bu.overlapped_rb:
                    if overlapped_rb.ue is ue:  # The new RB will overlap with the UE itself
                        return None
                    else:
                        overlapped_rb.ue.is_to_recalculate_mcs = True   # mark the effected UEs to recalculate

                bu.set_up_bu(i, j, resource_block)
        (ue.gnb_info if self.nodeb.nb_type == NodeBType.G else ue.enb_info).rb.append(resource_block)

        if not ue.is_allocated:
            ue.is_allocated = True

        self._cache_is_valid: bool = False  # set cache as invalid (for _available_block)

        ue.numerology_in_use = tmp_numerology  # restore
        return resource_block

    def allocate_zone(self, zone: Zone) -> bool:
        is_allocatable: bool = self.available_bandwidth >= zone.zone_freq
        if is_allocatable:
            bu_i: int = self._available_frequent_offset
            bu_j: int = 0
            for ue in zone.ue_list:
                for idx_ue_rb in range(
                        (G_MCS if self.nodeb.nb_type == NodeBType.G else E_MCS).get_worst().calc_required_rb_count(
                            ue.request_data_rate)):
                    self.allocate_resource_block(bu_i, bu_j, ue)
                    if bu_j + zone.numerology.time < self.nodeb.frame.frame_time:
                        bu_j += zone.numerology.time
                    elif bu_j + zone.numerology.time == self.nodeb.frame.frame_time:
                        bu_i += zone.numerology.freq
                        bu_j: int = 0
                    else:
                        raise Exception("RB allocate error: index increase error")
            self._available_frequent_offset += zone.zone_freq
            assert (bu_i if bu_j == 0 else bu_i + zone.numerology.freq) == self._available_frequent_offset, \
                "index increase error"
        return is_allocatable

    @property
    def available_bandwidth(self):
        """
        restrict: used only when zones/RBs are allocated from the smaller frequency domain,
        i.e. the BUs after self._available_frequent_offset are not allocated.
        """
        assert (self.FREQ - self._available_frequent_offset) >= 0
        if self.nodeb.nb_type == NodeBType.E:
            # Don't allocate the RBs overlap with gNB on eframe in phase 2
            return self.nodeb.frame.cochannel_offset - self._available_frequent_offset
        return self.FREQ - self._available_frequent_offset

    @property
    def bu_status(self) -> Tuple[Tuple[bool, ...], ...]:
        if not self._cache_is_valid:
            self._bu_status = tuple(tuple(column.is_used for column in row) for row in self.bu)
            self._cache_is_valid: bool = True
        return self._bu_status


class BaseUnit:
    def __init__(self, absolute_i: int, absolute_j: int, layer: Layer):
        self._absolute_i: int = absolute_i
        self._absolute_j: int = absolute_j
        self._layer: Layer = layer
        self._is_cochannel: bool = False
        self._cochannel_nb: Optional[Union[ENodeB, GNodeB]] = None
        self._cochannel_absolute_i: Optional[int] = None

        # properties to be configured at runtime
        self.relative_i: Optional[int] = None
        self.relative_j: Optional[int] = None
        self.within_rb: Optional[ResourceBlock] = None
        self.sinr: float = float('-inf')

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

    @property
    def overlapped_rb(self) -> List[ResourceBlock]:
        rb_list: List[ResourceBlock] = []
        for layer in self.layer.nodeb.frame.layer:
            if layer is not self.layer:
                if rb := layer.bu[self.absolute_i][self.absolute_j].within_rb:
                    rb_list.append(rb)
        if self.is_cochannel:
            for layer in self.cochannel_nb.frame.layer:
                if rb := layer.bu[self.cochannel_bu_i][self.absolute_j].within_rb:
                    rb_list.append(rb)
        return rb_list

    @property
    def is_used(self) -> bool:
        return self.within_rb is not None

    @property
    def is_at_upper_left(self) -> bool:
        # return True if this BU is at the upper left corner of the RB it belongs to
        assert self.is_used
        return self.relative_i == 0 and self.relative_j == 0

    def set_cochannel(self, nodeb: Union[ENodeB, GNodeB], absolute_i: int):
        self._is_cochannel: bool = True
        self._cochannel_nb: Union[ENodeB, GNodeB] = nodeb
        self._cochannel_absolute_i: int = absolute_i

    @property
    def is_cochannel(self) -> bool:
        return self._is_cochannel

    @property
    def cochannel_nb(self) -> Union[ENodeB, GNodeB]:
        return self._cochannel_nb

    @property
    def cochannel_bu_i(self) -> int:
        return self._cochannel_absolute_i

    @property
    def absolute_i(self) -> int:
        return self._absolute_i

    @property
    def absolute_j(self) -> int:
        return self._absolute_j

    @property
    def layer(self) -> Layer:
        return self._layer
