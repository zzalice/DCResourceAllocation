from resource_allocation.nodeb import NodeB
from resource_allocation.ue import UserEquipment
from resource_allocation.util_enum import MCS_E, NodeBType, UEType


class ENodeB(NodeB):
    def __init__(self):
        super().__init__()
        self.nb_type = NodeBType.E


class EUserEquipment(UserEquipment):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ue_type = UEType.E
        del self.gnb_info

    def assign_mcs(self, mcs: MCS_E):
        self.enb_info.mcs = mcs
