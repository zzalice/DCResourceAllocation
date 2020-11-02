from .nodeb import NodeB
from .ue import UserEquipment
from .util_enum import E_MCS, LTEPhysicalResourceBlock, NodeBType, UEType
from .util_type import CandidateSet


class ENodeB(NodeB):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.nb_type: NodeBType = NodeBType.E


class EUserEquipment(UserEquipment):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ue_type: UEType = UEType.E
        del self.gnb_info

        self.candidate_set: CandidateSet = (LTEPhysicalResourceBlock.E,)
        self.numerology_in_use: LTEPhysicalResourceBlock = LTEPhysicalResourceBlock.E

    def assign_mcs(self, mcs: E_MCS):
        self.enb_info.mcs = mcs
