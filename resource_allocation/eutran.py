from resource_allocation.enum import E_MCS, NodeBType, UEType
from resource_allocation.nodeb import NodeB
from resource_allocation.ue import UserEquipment


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
