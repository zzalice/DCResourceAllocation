from typing import List, Tuple, Union

from src.channel_model.sinr import ChannelModel
from src.resource_allocation.algo.new_ue import AllocateUEList, AllocateUEListSameNumerology
from src.resource_allocation.algo.utils import sort_by_channel_quality
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.resource_allocation.ds.ue import UserEquipment
from src.resource_allocation.ds.undo import Undo

UE = Union[UserEquipment, GUserEquipment, EUserEquipment, DUserEquipment]


class Msema(Undo):
    """
    UEs can only allocate to [BUs that has the same numerology as itself] or [BUs that are not used].
    At the same time, the RBs of a UE must be [continuous] but [can be in different layers].
    """

    def __init__(self, nb: Union[GNodeB, ENodeB], channel_model: ChannelModel, allocated_ue: Tuple[UE, ...]):
        super().__init__()
        self.nb: Union[GNodeB, ENodeB] = nb
        self.channel_model: ChannelModel = channel_model
        self.allocated_ue: List[UE] = list(allocated_ue)
        self.unallocated_ue: List[UE] = []

    def allocate_ue_list(self, ue_list: Tuple[UE]):
        self.unallocated_ue: List[UE] = list(ue_list)

        # lap with same numerology or unused BU in any layer
        self.unallocated_ue: List[UE] = sort_by_channel_quality(self.unallocated_ue, self.nb.nb_type)
        same_numerology: AllocateUEListSameNumerology = AllocateUEListSameNumerology(self.nb,
                                                                                     tuple(self.unallocated_ue),
                                                                                     tuple(self.allocated_ue),
                                                                                     self.channel_model)
        same_numerology.allocate_ue_list(allow_lower_than_cqi0=False)
        self.allocated_ue = same_numerology.allocated_ue
        self.unallocated_ue = same_numerology.unallocated_ue

        # allocate to any empty space
        self.unallocated_ue: List[UE] = sort_by_channel_quality(self.unallocated_ue, self.nb.nb_type)
        AllocateUEList(self.nb, tuple(self.unallocated_ue), tuple(self.allocated_ue), self.channel_model).allocate(
            allow_lower_than_cqi0=False)
