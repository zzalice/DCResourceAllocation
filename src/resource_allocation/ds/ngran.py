from typing import Union

from .nodeb import NodeB
from .ue import UserEquipment
from .util_enum import E_MCS, G_MCS, NodeBType, UEType
from .util_type import Coordinate


class GNodeB(NodeB):
    def __init__(self, coordinate: Coordinate, radius: float = 1.0, power_tx: int = 46,
                 frame_freq: int = 216, frame_time: int = 16, frame_max_layer: int = 3):
        # default: 1.0km, 46 dBm, 40MHz * 1ms * 3layers
        super().__init__(coordinate, radius, power_tx, frame_freq, frame_time, frame_max_layer)
        self.nb_type: NodeBType = NodeBType.G


class GUserEquipment(UserEquipment):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ue_type: UEType = UEType.G
        del self.enb_info

    def assign_mcs(self, mcs: G_MCS):
        self.gnb_info.mcs = mcs


class DUserEquipment(UserEquipment):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ue_type: UEType = UEType.D
        self.enb_info.request_data_rate = 0  # let gNodeB deal with the data_rate requested by dUE first (phase2)

    def assign_mcs(self, mcs: Union[E_MCS, G_MCS]):
        if isinstance(mcs, E_MCS):
            self.enb_info.mcs = mcs
        elif isinstance(mcs, G_MCS):
            self.gnb_info.mcs = mcs
