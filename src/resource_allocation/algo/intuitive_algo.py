from typing import Dict, List, Tuple, Union

from src.channel_model.sinr import ChannelModel
from src.resource_allocation.algo.new_ue_allocation import AllocateUE
from src.resource_allocation.algo.space import empty_space, Space
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.resource_allocation.ds.ue import UserEquipment
from src.resource_allocation.ds.undo import Undo
from src.resource_allocation.ds.util_enum import NodeBType, UEType


class Intuitive(Undo):
    def __init__(self, gnb: GNodeB, enb: ENodeB, cochannel_index: Dict, gue: Tuple[GUserEquipment],
                 due: Tuple[DUserEquipment], eue: Tuple[EUserEquipment]):
        super().__init__()
        self.gnb: GNodeB = gnb
        self.enb: ENodeB = enb
        self.gues: List[GUserEquipment] = list(gue)
        self.dues: List[DUserEquipment] = list(due)
        self.eues: List[EUserEquipment] = list(eue)

        self.ue_gnb_to_allocate: List[Union[GUserEquipment, DUserEquipment]] = self.gues + self.dues
        self.ue_enb_to_allocate: List[Union[EUserEquipment, DUserEquipment]] = self.eues
        self.gue_allocated: List[GUserEquipment] = []
        self.due_allocated: List[DUserEquipment] = []
        self.eue_allocated: List[EUserEquipment] = []
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
            ue_nb_to_allocate: List[Union[GUserEquipment, DUserEquipment]] = self.ue_gnb_to_allocate
            nb: GNodeB = self.gnb
        else:
            self.ue_enb_to_allocate.sort(key=lambda x: x.coordinate.distance_enb, reverse=True)
            ue_nb_to_allocate: List[Union[EUserEquipment, DUserEquipment]] = self.ue_enb_to_allocate
            nb: ENodeB = self.enb

        while ue_nb_to_allocate:
            ue: UserEquipment = ue_nb_to_allocate.pop()  # the unallocated ue with best SINR

            # allocate ue
            is_complete: bool = False
            for layer in nb.frame.layer:
                spaces: Tuple[Space] = empty_space(layer)
                if len(spaces) == 0:    # TODO: 需不需要在整個frame都沒空間後，就break while ue
                    # run out of space in this layer
                    continue
                allocate_ue: AllocateUE = AllocateUE(ue, spaces, self.channel_model)
                is_complete: bool = allocate_ue.new_ue()
                self.append_undo([lambda: allocate_ue.undo(), allocate_ue])

                # TODO: adjust the mcs of effected UEs.
                # TODO: If lowers down any MCS. undo the new allocated UE.
                # is_complete: bool = False

                if is_complete:
                    self.purge_undo()
                    break
                else:
                    self.undo()

            if ue.ue_type == UEType.G:
                (self.gue_allocated if is_complete else self.gue_fail).append(ue)
            elif ue.ue_type == UEType.D:
                (self.due_allocated if is_complete else self.due_fail).append(ue)
            elif ue.ue_type == UEType.E:
                (self.eue_allocated if is_complete else self.eue_fail).append(ue)
            else:
                raise AssertionError
