from .nodeb import NodeB
from .ue import UserEquipment
from .util_enum import E_MCS, NodeBType, UEType


class ENodeB(NodeB):
    def __init__(self):
        super().__init__()
        self.nb_type: NodeBType = NodeBType.E


class EUserEquipment(UserEquipment):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ue_type: UEType = UEType.E
        del self.gnb_info

    def assign_mcs(self, mcs: E_MCS):
        self.enb_info.mcs = mcs
