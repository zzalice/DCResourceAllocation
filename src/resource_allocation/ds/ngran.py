from typing import Union

from .enum import E_MCS, G_MCS, NodeBType, UEType
from .nodeb import NodeB
from .ue import UserEquipment


class GNodeB(NodeB):
    def __init__(self):
        super().__init__()
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

    def assign_mcs(self, mcs: Union[E_MCS, G_MCS]):
        if isinstance(mcs, E_MCS):
            self.enb_info.mcs = mcs
        elif isinstance(mcs, G_MCS):
            self.gnb_info.mcs = mcs
