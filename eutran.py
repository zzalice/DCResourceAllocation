from nodeb import NodeB
from ue import UserEquipment
from util_enum import UEType, NodeBType


class ENodeB(NodeB):
    def __init__(self):
        super().__init__()
        self.nb_type = NodeBType.E


class EUserEquipment(UserEquipment):
    def __init__(self):
        super().__init__()
        self.ue_type = UEType.E
