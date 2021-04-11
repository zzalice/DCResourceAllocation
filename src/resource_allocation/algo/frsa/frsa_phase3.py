from typing import List, Tuple, Union

from src.channel_model.adjust_mcs import AdjustMCS
from src.channel_model.sinr import ChannelModel
from src.resource_allocation.algo.new_ue import AllocateUEList
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.resource_allocation.ds.ue import UserEquipment
from src.resource_allocation.ds.undo import Undo

UE = Union[UserEquipment, DUserEquipment, GUserEquipment, EUserEquipment]


class FRSAPhase3(Undo):
    def __init__(self, nb: Union[GNodeB, ENodeB], channel_model: ChannelModel):
        super().__init__()
        self.nb: Union[GNodeB, ENodeB] = nb
        self.channel_model: ChannelModel = channel_model

    def adjust_mcs_allocated_in_phase2(self, allocated_ue: Tuple[UE, ...]):
        allocated_ue: List[UE] = list(allocated_ue)
        for ue in allocated_ue:
            self.channel_model.sinr_ue(ue)
            AdjustMCS().remove_from_tail(ue)
            self.adjust_effected_ue(allocated_ue)

    def adjust_effected_ue(self, allocated_ue: List[UE]):
        while True:
            is_all_adjusted: bool = True
            for ue in allocated_ue:
                if ue.is_to_recalculate_mcs:
                    is_all_adjusted: bool = False
                    self.channel_model.sinr_ue(ue)
                    AdjustMCS().remove_from_tail(ue)
                    if not ue.is_allocated:
                        allocated_ue.remove(ue)
            if is_all_adjusted:
                return True

    def allocate_new_ue(self, unallocated_ue: Tuple[UE, ...], allocated_ue: Tuple[UE, ...]):
        AllocateUEList(self.nb, unallocated_ue, allocated_ue, self.channel_model).allocate(allow_lower_than_cqi0=False)
