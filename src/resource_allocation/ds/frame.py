from __future__ import annotations

from typing import List, Optional, Tuple, TYPE_CHECKING, Union

from .rb import ResourceBlock
from .undo import Undo
from .util_enum import E_MCS, G_MCS, LTEResourceBlock, NodeBType, Numerology, UEType

if TYPE_CHECKING:
    from .eutran import ENodeB
    from .ngran import GNodeB
    from .nodeb import ENBInfo, GNBInfo, NodeB
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


class Layer(Undo):
    def __init__(self, layer_index: int, freq: int, time: int, nodeb: NodeB):
        # i.e., BU[frequency(i|HEIGHT)][time(j|WIDTH)]
        super().__init__()
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
        # RB type
        tmp_numerology: Numerology = ue.numerology_in_use
        if self.nodeb.nb_type == NodeBType.E and ue.ue_type == UEType.D:
            ue.numerology_in_use = LTEResourceBlock.E  # TODO: refactor or redesign

        # assert
        assert offset_i + ue.numerology_in_use.freq <= self.FREQ and offset_j + ue.numerology_in_use.time <= self.TIME, "The RB is not in the legal domain of the frame."
        if self.nodeb.nb_type == NodeBType.E:
            assert offset_j % LTEResourceBlock.E.time == 0, "The RB in LTE frame should be aligned by slot."

        # main
        nb_info: Union[GNBInfo, ENBInfo] = ue.gnb_info if self.nodeb.nb_type == NodeBType.G else ue.enb_info

        resource_block: ResourceBlock = ResourceBlock(self, offset_i, offset_j, ue)
        for i in range(ue.numerology_in_use.freq):
            for j in range(ue.numerology_in_use.time):
                bu: BaseUnit = self.bu[offset_i + i][offset_j + j]
                for overlapped_rb in bu.overlapped_rb:
                    if overlapped_rb.ue is ue:  # The new RB will overlap with the UE itself
                        ue.numerology_in_use = tmp_numerology  # restore RB type
                        return None
                    else:
                        origin_bool: bool = overlapped_rb.ue.is_to_recalculate_mcs
                        overlapped_rb.ue.is_to_recalculate_mcs = True  # mark the effected UEs to recalculate
                        self.append_undo([lambda u=overlapped_rb.ue: setattr(u, 'is_to_recalculate_mcs', origin_bool)])

                bu.set_up(resource_block)
                self.append_undo([lambda b=bu: b.clear_up()])  # note the dummy parameter with a default value
        nb_info.rb.append(resource_block)
        self.append_undo([lambda: nb_info.rb.remove(resource_block)])

        # restore RB type
        ue.numerology_in_use = tmp_numerology
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

    @property
    def bu_status_cache_is_valid(self) -> bool:
        return self._cache_is_valid

    @bu_status_cache_is_valid.setter
    def bu_status_cache_is_valid(self, value: bool):
        assert value is False, "Only the property bu_status may update the bu status and set _cache_is_valid to True."
        self._cache_is_valid: bool = value


class BaseUnit:
    def __init__(self, absolute_i: int, absolute_j: int, layer: Layer):
        self._absolute_i: int = absolute_i
        self._absolute_j: int = absolute_j
        self._layer: Layer = layer
        self._is_cochannel: bool = False
        self._cochannel_nb: Optional[Union[ENodeB, GNodeB]] = None
        self._cochannel_absolute_i: Optional[int] = None

        # properties to be configured at runtime
        self.within_rb: Optional[ResourceBlock] = None
        self.sinr: float = float('-inf')

    def set_up(self, resource_block: ResourceBlock):
        # relative position of this BU withing a RB
        assert not self.is_used, f'BU({self.absolute_i}, {self.absolute_j}) in {self.layer.nodeb.nb_type} layer {self.layer.layer_index} is used by UE {self.within_rb.ue.uuid.hex[:4]}(uuid)'
        self.within_rb: ResourceBlock = resource_block

        self.layer.bu_status_cache_is_valid = False

    def clear_up(self):
        assert self.is_used
        self.within_rb = None
        self.sinr: float = float('-inf')

        self.layer.bu_status_cache_is_valid = False

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
