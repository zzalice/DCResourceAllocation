from __future__ import annotations

from typing import Any, Dict, List, Optional, TYPE_CHECKING, Union

from .frame import Frame
from .util_enum import E_MCS, G_MCS, NodeBType

if TYPE_CHECKING:
    from .rb import ResourceBlock
    from .util_type import CircularRegion


class NodeB:
    def __init__(self, region: CircularRegion, power_tx: int, frame_freq: int, frame_time: int,
                 frame_max_layer: int):
        self.region: CircularRegion = region
        self.power_tx: int = power_tx  # dBm
        self.frame: Frame = Frame(frame_freq, frame_time, frame_max_layer, self)
        # the number of BUs in frequency and time domain and the number of NOMA layers in a frame

        self.nb_type: Optional[NodeBType] = None

    def to_json(self) -> Dict[str, Any]:
        nb: Dict[str, Any] = {
            'x': self.region.x,
            'y': self.region.y,
            'radius': self.region.radius,
            'frame': self.frame.to_json()
        }
        return nb


class _NBInfoWithinUE:
    def __init__(self):
        self.nb: Optional[NodeB] = None
        self.mcs: Optional[Union[E_MCS, G_MCS]] = None
        self.rb: List[ResourceBlock] = list()

    @property
    def nb_type(self) -> NodeBType:
        assert self.nb is not None
        return self.nb.nb_type

    def update_mcs(self):
        if self.rb:
            self.mcs = min(self.rb, key=lambda b: b.mcs.value).mcs
        else:
            self.mcs = None

    def highest_frequency_rb(self) -> Optional[ResourceBlock]:
        if self.rb:
            self.rb.sort(key=lambda x: x.j_start)  # sort by time
            self.rb.sort(key=lambda x: x.i_start)  # sort by freq
            return self.rb[-1]
        else:
            return None

    def to_json(self) -> Dict[str, Any]:
        nb_info: Dict[str, Any] = {
            'mcs': self.mcs.index if self.mcs else None,
            'rb': [rb.to_json() for rb in self.rb]
        }
        return nb_info


class ENBInfo(_NBInfoWithinUE):
    def __init__(self):
        super().__init__()


class GNBInfo(_NBInfoWithinUE):
    def __init__(self):
        super().__init__()
