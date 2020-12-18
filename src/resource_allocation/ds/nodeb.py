from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING, Union

from .frame import Frame
from .util_enum import E_MCS, G_MCS, NodeBType

if TYPE_CHECKING:
    from .rb import ResourceBlock
    from .util_type import Coordinate


class NodeB:
    def __init__(self, coordinate: Coordinate, radius: float, power_tx: int, frame_freq: int, frame_time: int,
                 frame_max_layer: int):
        self.coordinate: Coordinate = coordinate
        self.radius: float = radius  # km
        self.power_tx: int = power_tx  # dBm
        self.frame: Frame = Frame(frame_freq, frame_time, frame_max_layer, self)
        # the number of BUs in frequency and time domain and the number of NOMA layers in a frame

        self.nb_type: Optional[NodeBType] = None


class _NBInfoWithinUE:
    def __init__(self, request_data_rate: int):
        self.request_data_rate: int = request_data_rate

        self.nb: Optional[NodeB] = None
        self.mcs: Optional[Union[E_MCS, G_MCS]] = None
        self.rb: List[ResourceBlock] = list()
        self._num_of_rb_determined_by_mcs: int = 0

    @property
    def num_of_rb(self) -> int:
        return self.mcs.calc_required_rb_count(self.request_data_rate)

    @property
    def nb_type(self) -> NodeBType:
        assert self.nb is not None
        return self.nb.nb_type

    def update_mcs(self, mcs: Union[E_MCS, G_MCS]):
        self.mcs: Union[E_MCS, G_MCS] = mcs


class ENBInfo(_NBInfoWithinUE):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update_mcs(E_MCS.get_worst())

    def update_mcs(self, mcs: E_MCS):
        super().update_mcs(mcs)


class GNBInfo(_NBInfoWithinUE):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update_mcs(G_MCS.get_worst())

    def update_mcs(self, mcs: G_MCS):
        super().update_mcs(mcs)
