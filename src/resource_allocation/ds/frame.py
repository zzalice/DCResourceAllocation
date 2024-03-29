from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple, TYPE_CHECKING, Union

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

    def to_json(self) -> Dict[str, Any]:
        frame: Dict[str, Any] = {
            'frame_freq': self.frame_freq,
            'frame_time': self.frame_time,
            'max_layer': self.max_layer,
            'layer': []}
        for layer in self.layer:
            frame['layer'].append(layer.to_json())
        return frame


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

    @Undo.undo_func_decorator
    def allocate_resource_block(self, offset_i: int, offset_j: int, ue: UserEquipment) -> Optional[ResourceBlock]:
        # RB type
        tmp_numerology: Numerology = ue.numerology_in_use
        if self.nodeb.nb_type == NodeBType.E and ue.ue_type == UEType.D:
            ue.numerology_in_use = LTEResourceBlock.E  # TODO: refactor or redesign

        # assert
        assert offset_i + ue.numerology_in_use.freq <= self.FREQ and offset_j + ue.numerology_in_use.time <= self.TIME, "The RB is not in the legal domain of the frame."
        if self.nodeb.nb_type == NodeBType.E:
            assert offset_j % LTEResourceBlock.E.time == 0, "The RB in LTE frame should be aligned by slot."

        # check if the new RB will overlap with the UE itself
        for i in range(ue.numerology_in_use.freq):
            for j in range(ue.numerology_in_use.time):
                bu: BaseUnit = self.bu[offset_i + i][offset_j + j]
                if ue in bu.overlapped_ue:
                    return None

        # main
        result: ResourceBlock = self._allocate_resource_block(offset_i, offset_j, ue)

        # restore RB type
        ue.numerology_in_use = tmp_numerology

        return result

    def _allocate_resource_block(self, offset_i: int, offset_j: int, ue: UserEquipment) -> Optional[ResourceBlock]:
        nb_info: Union[GNBInfo, ENBInfo] = ue.gnb_info if self.nodeb.nb_type == NodeBType.G else ue.enb_info
        resource_block: ResourceBlock = ResourceBlock(self, offset_i, offset_j, ue)
        for i in range(ue.numerology_in_use.freq):
            for j in range(ue.numerology_in_use.time):
                bu: BaseUnit = self.bu[offset_i + i][offset_j + j]
                if i == j == 0:
                    bu.is_upper_left = True
                bu.set_up(resource_block)
                self.append_undo(lambda b=bu: b.undo(), lambda b=bu: b.purge_undo())
        nb_info.rb.append(resource_block)
        self.append_undo(lambda: nb_info.rb.remove(resource_block))
        return resource_block

    def allocate_zone(self, zone: Zone, offset: Optional[int] = None, virtual: bool = False) -> bool:
        is_allocatable: bool = self.available_bandwidth >= zone.zone_freq
        if is_allocatable:
            bu_i: int = self._available_frequent_offset if offset is None else offset
            bu_j: int = 0
            for ue in zone.ue_list:
                for idx_ue_rb in range(
                        (G_MCS if self.nodeb.nb_type == NodeBType.G else E_MCS).get_worst().calc_required_rb_count(
                            ue.request_data_rate)):
                    if not virtual:
                        self.allocate_resource_block(bu_i, bu_j, ue)
                    if bu_j + zone.numerology.time < self.nodeb.frame.frame_time:
                        bu_j += zone.numerology.time
                    elif bu_j + zone.numerology.time == self.nodeb.frame.frame_time:
                        bu_i += zone.numerology.freq
                        bu_j: int = 0
                    else:
                        raise Exception("RB allocate error: index increase error")
            if offset is None:
                self._available_frequent_offset += zone.zone_freq
            else:
                self._available_frequent_offset = offset + zone.zone_freq
            assert (bu_i if bu_j == 0 else bu_i + zone.numerology.freq) == self._available_frequent_offset, \
                "index increase error"
        return is_allocatable

    @property
    def available_frequent_offset(self) -> int:
        return self._available_frequent_offset

    def reset_available_frequent_offset(self):
        self._available_frequent_offset: int = 0

    @property
    def available_bandwidth(self) -> int:
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

    def to_json(self) -> Dict[str, Any]:
        layer: Dict[str, Any] = {
            'bu_status': self.bu_status,
            'bu': [[] for _ in range(self.FREQ)]
        }
        for i in range(self.FREQ):
            for j in range(self.TIME):
                layer['bu'][i].append(self.bu[i][j].to_json())
        return layer


class BaseUnit(Undo):
    def __init__(self, absolute_i: int, absolute_j: int, layer: Layer):
        super().__init__()
        self._absolute_i: int = absolute_i
        self._absolute_j: int = absolute_j
        self._layer: Layer = layer

        # properties to be configured at runtime
        self._is_cochannel: bool = False
        self._cochannel_nb: Optional[Union[ENodeB, GNodeB]] = None
        self._cochannel_absolute_i: Optional[int] = None
        self._within_rb: Optional[ResourceBlock] = None
        self.sinr: float = float('-inf')
        self._is_to_recalculate_sinr: bool = False
        self._lapped_cache_is_valid: bool = False
        self._overlapped_bu: Tuple[BaseUnit, ...] = ()
        self._overlapped_rb: Tuple[ResourceBlock, ...] = ()
        self._overlapped_ue: Tuple[UserEquipment, ...] = ()

        # for MSEMA
        self.is_upper_left: bool = False

    def set_noma_bu(self):
        """Execute once."""
        overlapped_bu: List[BaseUnit] = []
        for layer in self.layer.nodeb.frame.layer:
            if layer is not self.layer:
                overlapped_bu.append(layer.bu[self.absolute_i][self.absolute_j])
        self._overlapped_bu: Tuple[BaseUnit, ...] = tuple(overlapped_bu)

    @Undo.undo_func_decorator
    def set_up(self, resource_block: ResourceBlock):
        # relative position of this BU withing a RB
        assert not self.is_used, f'BU({self.absolute_i}, {self.absolute_j}) in {self.layer.nodeb.nb_type} layer {self.layer.layer_index} is used by UE {self.within_rb.ue.uuid.hex[:4]}(uuid)'
        self.append_undo(lambda rb=self._within_rb: setattr(self, "_within_rb", rb))
        self._within_rb: ResourceBlock = resource_block
        self.append_undo(lambda origin=self._is_to_recalculate_sinr: setattr(self, '_is_to_recalculate_sinr', origin))
        self._is_to_recalculate_sinr: bool = True

        self._effect_others()
        self.append_undo(lambda: setattr(self.layer, 'bu_status_cache_is_valid', False))
        self.layer.bu_status_cache_is_valid = False

        self.append_undo(lambda: setattr(self, 'is_upper_left', False))

    @Undo.undo_func_decorator
    def clear_up(self):
        assert self.is_used
        self.append_undo(lambda rb=self._within_rb: setattr(self, "_within_rb", rb))
        self._within_rb = None
        self.append_undo(lambda i=self.sinr: setattr(self, "sinr", i))
        self.sinr: float = float('-inf')
        self.append_undo(lambda origin=self._is_to_recalculate_sinr: setattr(self, '_is_to_recalculate_sinr', origin))
        self._is_to_recalculate_sinr: bool = False

        self._effect_others()
        self.append_undo(lambda: setattr(self.layer, 'bu_status_cache_is_valid', False))
        self.layer.bu_status_cache_is_valid = False

        self.append_undo(lambda origin=self.is_upper_left: setattr(self, 'is_upper_left', origin))
        self.is_upper_left: bool = False

    def _effect_others(self):
        self.assert_undo_function()
        for ue in self.overlapped_ue:
            self.append_undo(lambda u=ue, origin=ue.is_to_recalculate_mcs: setattr(u, "is_to_recalculate_mcs", origin))
            ue.is_to_recalculate_mcs = True
        for bu in self.overlapped_bu:
            self.append_undo(
                lambda b=bu, origin=bu._is_to_recalculate_sinr: setattr(b, "_is_to_recalculate_sinr", origin))
            self.append_undo(lambda b=bu: setattr(b, "overlapped_cache_is_valid", False))
            bu._is_to_recalculate_sinr = True
            bu.overlapped_cache_is_valid = False

    @property
    def lapped_is_upper_left(self) -> bool:
        for bu in self.overlapped_bu:
            if bu.is_upper_left:
                return True
        return False

    @property
    def lapped_numerology(self) -> Tuple[Union[Numerology, LTEResourceBlock], ...]:
        numerology: Set = set()
        numerology.add(self.within_rb.numerology) if self.within_rb else None
        for rb in self.overlapped_rb:
            numerology.add(rb.numerology)
        return tuple(numerology)

    @property
    def overlapped_bu(self) -> Tuple[BaseUnit, ...]:
        return self._overlapped_bu

    @property
    def overlapped_rb(self) -> Tuple[ResourceBlock]:
        if not self.overlapped_cache_is_valid:
            self._overlapped_element()
        return self._overlapped_rb

    @property
    def overlapped_ue(self) -> Tuple[UserEquipment]:
        if not self.overlapped_cache_is_valid:
            self._overlapped_element()
        return self._overlapped_ue

    def _overlapped_element(self):
        overlapped_rb: List[ResourceBlock] = []
        overlapped_ue = set()
        for bu in self.overlapped_bu:
            if rb := bu.within_rb:
                overlapped_rb.append(rb)
                overlapped_ue.add(rb.ue)

        self._overlapped_rb: Tuple[ResourceBlock, ...] = tuple(overlapped_rb)
        self._overlapped_ue: Tuple[UserEquipment, ...] = tuple(overlapped_ue)
        self._lapped_cache_is_valid: bool = True

    @property
    def overlapped_cache_is_valid(self) -> bool:
        return self._lapped_cache_is_valid

    @overlapped_cache_is_valid.setter
    def overlapped_cache_is_valid(self, value: bool):
        assert not value, "Only _overlapped_element() can change the status to True."
        self._lapped_cache_is_valid: bool = value

    def set_cochannel(self, nodeb: Union[ENodeB, GNodeB], absolute_i: int):
        self._is_cochannel: bool = True
        self._cochannel_nb: Union[ENodeB, GNodeB] = nodeb
        self._cochannel_absolute_i: int = absolute_i

        overlapped_bu: List[BaseUnit] = list(self._overlapped_bu)
        for layer in self.cochannel_nb.frame.layer:
            overlapped_bu.append(layer.bu[self.cochannel_bu_i][self.absolute_j])
        self._overlapped_bu: Tuple[BaseUnit, ...] = tuple(overlapped_bu)

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
    def is_to_recalculate_sinr(self) -> bool:
        return self._is_to_recalculate_sinr

    @is_to_recalculate_sinr.setter
    def is_to_recalculate_sinr(self, value: bool):
        assert not value, "Only SINR calculator will change the status of this bool from outside the BaseUnit object."
        self._is_to_recalculate_sinr: bool = value

    @property
    def within_rb(self) -> ResourceBlock:
        return self._within_rb

    @property
    def is_used(self) -> bool:
        return self.within_rb is not None

    @property
    def absolute_i(self) -> int:
        return self._absolute_i

    @property
    def absolute_j(self) -> int:
        return self._absolute_j

    @property
    def layer(self) -> Layer:
        return self._layer

    def to_json(self) -> Dict[str, Any]:
        bu: Dict[str, Any] = {
            'lapped_numerology': [n.name for n in self.lapped_numerology],
            'is_cochannel': self.is_cochannel,
            'is_used': self.is_used,
            'within_rb': self.within_rb.to_json() if self.within_rb else None
        }
        return bu
