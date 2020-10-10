from nodeb import NodeB
from ue import UserEquipment
from util_enum import NodeBType, UEType


class GNodeB(NodeB):
    def __init__(self):
        super().__init__()
        self.nb_type = NodeBType.G


class GUserEquipment(UserEquipment):
    def __init__(self):
        super().__init__()
        self.ue_type = UEType.G


class DUserEquipment(UserEquipment):
    def __init__(self):
        super().__init__()
        self.ue_type = UEType.D
