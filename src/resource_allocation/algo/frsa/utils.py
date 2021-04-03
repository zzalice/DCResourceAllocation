from dataclasses import dataclass
from typing import Dict, List, Optional, Union

from src.resource_allocation.ds.frame import Layer
from src.resource_allocation.ds.util_enum import Numerology
from src.resource_allocation.ds.zone import Zone


class LayerZone:
    def __init__(self, layer: int, frame_freq: int):
        self._layer: int = layer
        self._residual: int = frame_freq
        self._zone: List[Union[Zone, ConcatenateZone]] = []
        self._frequency_span: Dict[Numerology, int] = {n: 0 for n in Numerology}

    def add_zone(self, zone: Zone):
        self._zone.append(zone)
        self._residual -= zone.zone_freq
        assert self._residual >= 0
        self._frequency_span[zone.numerology] += zone.zone_freq

    def remove_zone(self, zone: Zone):
        self._zone.remove(zone)
        self._residual += zone.zone_freq
        self._frequency_span[zone.numerology] -= zone.zone_freq

    def form_concatenate_zone(self):
        if not self.zone:  # if is empty
            return True
        self.zone.sort(key=lambda x: x.numerology.mu)
        concatenate: List[ConcatenateZone] = [ConcatenateZone(self.zone.pop())]
        while self.zone:
            zone: Zone = self.zone.pop()
            if zone.numerology == concatenate[-1].numerology:
                concatenate[-1].zone.append(zone)
            else:
                concatenate.append(ConcatenateZone(zone))
        self._zone: List[ConcatenateZone] = concatenate
        return True

    @property
    def layer(self) -> int:
        return self._layer

    @property
    def residual(self) -> int:
        return self._residual

    @property
    def zone(self) -> List[Zone]:
        return self._zone

    @property
    def frequency_span(self) -> Dict[Numerology, int]:
        return self._frequency_span


class ConcatenateZone:
    def __init__(self, zone: Zone):
        self.zone: List[Zone] = [zone]
        self._numerology: Numerology = zone.numerology
        self._offset: Optional[int] = None
        self.is_preallocate: bool = False

    @property
    def bandwidth(self) -> int:
        bw: int = 0
        for z in self.zone:
            bw += z.zone_freq
        return bw

    @property
    def numerology(self) -> Numerology:
        return self._numerology

    def allocate(self, layer: Layer):
        is_first: bool = True
        for zone in self.zone:
            if is_first:
                is_first: bool = False
                offset: int = self.offset
            else:
                offset: Optional[int] = None
            layer.allocate_zone(zone, offset)

    @property
    def offset(self) -> int:
        return self._offset

    @offset.setter
    def offset(self, value: int):
        assert value >= 0
        self._offset: int = value


class PreallocateCZ:
    def __init__(self, layer: int, freq: int):
        self.layer: int = layer
        self.frame_freq: int = freq  # gNB BW
        self.cz_list: List[ConcatenateZone] = []  # In the order of offset.

    def append_cz(self, cz: ConcatenateZone, offset: Optional[int] = None):
        if offset is None:
            if self.cz_list:
                offset: int = self.cz_list[-1].offset + self.cz_list[-1].bandwidth
            else:
                offset: int = 0
        elif self.cz_list and offset < self.cz_list[-1].offset + self.cz_list[-1].bandwidth:
            offset: int = self.cz_list[-1].offset + self.cz_list[-1].bandwidth

        cz.offset = offset
        self.cz_list.append(cz)
        self.check_out_of_bound(-1)
        self.check_lapped(-1)
        self.assert_cz_list()

    def check_out_of_bound(self, cz_idx: int):
        while True:
            edge: int = self.cz_list[cz_idx].offset + self.cz_list[cz_idx].bandwidth - 1
            if edge >= self.frame_freq:
                self.shift(cz_idx)
            else:
                return True

    def check_lapped(self, cz_idx: int):
        # check invalid overlapped
        for idx_below in range(cz_idx, -len(self.cz_list) - 1, -1):
            for idx_above in range(idx_below - 1, -len(self.cz_list) - 1, -1):
                while self.cz_list[idx_below].offset <= (
                        self.cz_list[idx_above].offset + self.cz_list[idx_above].bandwidth - 1):
                    self.shift(idx_above)

    def shift(self, cz_idx: int):
        assert self.cz_list[cz_idx].offset > 0, 'No space to shift.'

        # shift
        self.cz_list[cz_idx].offset -= 1

    def assert_cz_list(self):
        assert self.cz_list[0].offset >= 0
        for i, cz in enumerate(self.cz_list[1:]):
            last_cz: ConcatenateZone = self.cz_list[i]
            assert cz.offset > last_cz.offset + last_cz.bandwidth - 1
        assert self.cz_list[-1].offset + self.cz_list[-1].bandwidth <= self.frame_freq


@dataclass
class Dissimilarity:
    layer: int
    numerology: Numerology
    dissimilarity: float
