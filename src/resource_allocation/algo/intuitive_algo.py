from typing import Dict, List, Optional, Tuple, Union

from src.channel_model.sinr import ChannelModel
from src.resource_allocation.algo.new_ue_allocation import AllocateUE
from src.resource_allocation.algo.space import empty_space, Space
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.resource_allocation.ds.ue import UserEquipment
from src.resource_allocation.ds.util_enum import NodeBType, UEType


class Intuitive:
    def __init__(self, gnb: GNodeB, enb: ENodeB, cochannel_index: Dict, gue: Tuple[GUserEquipment], due: Tuple[DUserEquipment], eue: Tuple[EUserEquipment]):
        self.gnb: GNodeB = gnb
        self.enb: ENodeB = enb
        self.gue_unallocated: List[GUserEquipment] = list(gue)
        self.due_unallocated: List[DUserEquipment] = list(due)
        self.eue_unallocated: List[EUserEquipment] = list(eue)

        self.ue_gnb_to_allocate: List[Union[GUserEquipment, DUserEquipment]] = self.gue_unallocated + self.due_unallocated
        self.ue_enb_to_allocate: List[Union[EUserEquipment, DUserEquipment]] = self.eue_unallocated
        self.ue_gnb_allocated: List[Union[GUserEquipment, DUserEquipment]] = []
        self.ue_enb_allocated: List[Union[EUserEquipment, DUserEquipment]] = []
        self.gue_fail: List[GUserEquipment] = []
        self.due_fail: List[DUserEquipment] = []
        self.eue_fail: List[EUserEquipment] = []

        self.channel_model: ChannelModel = ChannelModel(cochannel_index)

    def algorithm(self):
        # Do gNB allocation first, then eNB.
        self.resource_allocation(self.gnb.nb_type)
        self.ue_enb_to_allocate.extend(self.due_fail)
        self.resource_allocation(self.enb.nb_type)

    def resource_allocation(self, nb_type: NodeBType):
        if nb_type == NodeBType.G:
            self.ue_gnb_to_allocate.sort(key=lambda x: x.coordinate.distance_gnb, reverse=True)
            ue_nb_to_allocate: List[UserEquipment] = self.ue_gnb_to_allocate
            ue_nb_allocated: List[UserEquipment] = self.ue_gnb_allocated
            nb: GNodeB = self.gnb
        else:
            self.ue_enb_to_allocate.sort(key=lambda x: x.coordinate.distance_enb, reverse=True)
            ue_nb_to_allocate: List[UserEquipment] = self.ue_enb_to_allocate
            ue_nb_allocated: List[UserEquipment] = self.ue_enb_allocated
            nb: ENodeB = self.enb

        while ue_nb_to_allocate:
            ue: UserEquipment = ue_nb_to_allocate.pop()     # the unallocated ue with best SINR

            # allocate ue
            is_complete: bool = False
            for layer in nb.frame.layer:
                is_complete: bool = AllocateUE(ue, empty_space(layer), self.channel_model).new_ue()

                # TODO: adjust the mcs of effected UEs.
                # TODO: If lowers down any MCS. undo the new allocated UE.

                if is_complete:
                    ue_nb_allocated.append(ue)
                    break

            if is_complete is False:
                if ue.ue_type == UEType.G:
                    self.gue_fail.append(ue)
                elif ue.ue_type == UEType.D:
                    self.due_fail.append(ue)
                elif ue.ue_type == UEType.E:
                    self.eue_fail.append(ue)
