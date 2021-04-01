from typing import List

from .nodeb import NodeB
from .ue import UserEquipment
from .util_enum import NodeBType, UEType
from .util_type import Coordinate


class GNodeB(NodeB):
    def __init__(self, coordinate: Coordinate, radius: float = 0.3, power_tx: int = 30,
                 frame_freq: int = 216, frame_time: int = 80, frame_max_layer: int = 3):
        # default: 0.3km, 30 dBm, 40MHz * 10ms * 3layers
        super().__init__(coordinate, radius, power_tx, frame_freq, frame_time, frame_max_layer)
        self.nb_type: NodeBType = NodeBType.G


class GUserEquipment(UserEquipment):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ue_type: UEType = UEType.G
        del self.enb_info

        # for MCUP
        self.connection_preference: int = 1
        self.nb_preference: List[int] = [1]  # 0 represent eNB, 1 represent gNB.


class DUserEquipment(UserEquipment):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ue_type: UEType = UEType.D

        # for MCUP
        self.connection_preference: int = 2
        self.nb_preference: List[int] = [0, 1]  # 0 represent eNB, 1 represent gNB.

    @property
    def cross_nb(self) -> bool:
        return True if len(self.enb_info.rb) > 0 and len(self.gnb_info.rb) > 0 else False
