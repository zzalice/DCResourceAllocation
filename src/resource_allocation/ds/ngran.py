from typing import Union

from .nodeb import NodeB
from .ue import UserEquipment
from .util_enum import E_MCS, G_MCS, NodeBType, UEType


class GNodeB(NodeB):
    def __init__(self, radius=1.0, frame_freq=100, frame_max_layer=3, **kwargs):
        # default: 1.0km, 20MHz * 10ms * 3layers, TODO: check if 20MHz == 100BUs ??
        super().__init__(radius, frame_freq, frame_max_layer=frame_max_layer, **kwargs)
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
