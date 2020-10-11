from typing import Union

from nodeb import NodeB
from ue import UserEquipment
from util_enum import MCS_E, MCS_G, NodeBType, UEType


class GNodeB(NodeB):
    def __init__(self):
        super().__init__()
        self.nb_type = NodeBType.G


class GUserEquipment(UserEquipment):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ue_type = UEType.G
        del self.enb_info

    def assign_mcs(self, mcs: MCS_G):
        self.gnb_info.mcs = mcs


class DUserEquipment(UserEquipment):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ue_type = UEType.D

    def assign_mcs(self, mcs: Union[MCS_E, MCS_G]):
        if isinstance(mcs, MCS_E):
            self.enb_info.mcs = mcs
        elif isinstance(mcs, MCS_G):
            self.gnb_info.mcs = mcs
