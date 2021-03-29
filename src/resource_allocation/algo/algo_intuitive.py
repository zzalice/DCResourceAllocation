from typing import Tuple

from src.channel_model.sinr import ChannelModel
from src.resource_allocation.algo.new_ue import AllocateUEList
from src.resource_allocation.algo.utils import divide_ue
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.resource_allocation.ds.undo import Undo


class Intuitive(Undo):
    def __init__(self, gnb: GNodeB, enb: ENodeB, channel_model: ChannelModel,
                 gue: Tuple[GUserEquipment], due: Tuple[DUserEquipment], eue: Tuple[EUserEquipment]):
        super().__init__()
        self.gnb: GNodeB = gnb
        self.enb: ENodeB = enb
        self.gues: Tuple[GUserEquipment] = gue
        self.dues: Tuple[DUserEquipment] = due
        self.eues: Tuple[EUserEquipment] = eue
        self.channel_model: ChannelModel = channel_model

    def algorithm(self):
        # Do gNB allocation first, then eNB.
        AllocateUEList(self.gnb, self.gues + self.dues, tuple(), self.channel_model).allocate(allow_lower_mcs=False)    # FIXME: implement the space finding algo
        gue_allocated, gue_unallocated = divide_ue(tuple(self.gues))
        due_allocated, due_unallocated = divide_ue(tuple(self.dues))
        AllocateUEList(self.enb, self.eues + due_unallocated, gue_allocated + due_allocated,
                       self.channel_model).allocate(allow_lower_mcs=False)
