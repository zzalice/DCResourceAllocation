from typing import Tuple, Union

from src.channel_model.adjust_mcs import AdjustMCS
from src.channel_model.sinr import ChannelModel
from src.resource_allocation.algo.new_ue import AllocateUEList
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.resource_allocation.ds.ue import UserEquipment
from src.resource_allocation.ds.undo import Undo
from src.resource_allocation.ds.util_enum import NodeBType

UE = Union[UserEquipment, DUserEquipment, GUserEquipment, EUserEquipment]


class FRSAPhase3(Undo):
    def __init__(self, nb: Union[GNodeB, ENodeB], channel_model: ChannelModel):
        super().__init__()
        self.nb: Union[GNodeB, ENodeB] = nb
        self.channel_model: ChannelModel = channel_model

    def adjust_mcs(self, allocated_ue: Tuple[UE]):  # TODO: adjust effected UEs
        for ue in allocated_ue:
            self.channel_model.sinr_ue(ue)
            AdjustMCS().remove_from_tail(ue,
                                         ue.gnb_info if self.nb.nb_type == NodeBType.G else ue.enb_info)  # FIXME: must be single connection ue

    def allocate_new_ue(self, unallocated_ue: Tuple[UE], allocated_ue: Tuple[UE]):
        AllocateUEList(self.nb, unallocated_ue, allocated_ue, self.channel_model).allocate(allow_lower_than_cqi0=False)
