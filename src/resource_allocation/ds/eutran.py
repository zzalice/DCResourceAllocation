from typing import List

from .nodeb import NodeB
from .ue import UserEquipment
from .util_enum import LTEResourceBlock, NodeBType, UEType
from .util_type import CandidateSet, Coordinate


class ENodeB(NodeB):
    def __init__(self, coordinate: Coordinate, radius: float = 0.5, power_tx: int = 46,
                 frame_freq: int = 100, frame_time: int = 80, frame_max_layer: int = 1):
        # default: 0.5km, 46 dBm, 20MHz * 10ms * 1layers
        super().__init__(coordinate, radius, power_tx, frame_freq, frame_time, frame_max_layer)
        self.nb_type: NodeBType = NodeBType.E


class EUserEquipment(UserEquipment):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ue_type: UEType = UEType.E
        del self.gnb_info

        self.candidate_set: CandidateSet = (LTEResourceBlock.E,)
        self.numerology_in_use: LTEResourceBlock = LTEResourceBlock.E

        # for MCUP
        self.connection_preference: int = 1
        self.nb_preference: List[int] = [0]  # 0 represent eNB, 1 represent gNB.
