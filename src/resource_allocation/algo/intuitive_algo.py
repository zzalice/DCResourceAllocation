from typing import Dict, List, Tuple, Union

from src.channel_model.adjust_mcs import AdjustMCS
from src.channel_model.sinr import ChannelModel
from src.resource_allocation.algo.new_ue_allocation import AllocateUE
from src.resource_allocation.ds.space import empty_space, Space
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
        self.adjust_mcs = AdjustMCS(self.channel_model, self.gue_allocated, self.gue_fail,
                                    self.due_allocated, self.due_fail, self.eue_allocated, self.eue_fail)

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

        spaces: Tuple[Space] = self.update_empty_space(nb)

        while ue_nb_to_allocate:
            ue: UserEquipment = ue_nb_to_allocate.pop()
            is_allocated: bool = False
            if len(spaces) > 0:
                # allocate new ue
                allocate_ue: AllocateUE = AllocateUE(ue, spaces, self.channel_model)
                is_allocated: bool = allocate_ue.new_ue()
                self.append_undo([lambda a_u=allocate_ue: a_u.undo(), lambda a_u=allocate_ue: a_u.purge_undo()])

                # the effected UEs
                if is_allocated:
                    has_positive_effect: bool = self.adjust_mcs.adjust_mcs_allocated_ues(allow_lower_mcs=False)
                    self.append_undo(
                        [lambda a_m=self.adjust_mcs: a_m.undo(), lambda a_m=self.adjust_mcs: a_m.purge_undo()])
                    if not has_positive_effect:
                        is_allocated: bool = False

                if is_allocated:
                    spaces: Tuple[Space] = self.update_empty_space(nb)
                    self.purge_undo()
                else:
                    self.undo()
                # self.assert_is_empty(spaces, ue, is_allocated)

            if ue.ue_type == UEType.G:
                (self.gue_allocated if is_allocated else self.gue_fail).append(ue)
            elif ue.ue_type == UEType.D:
                (self.due_allocated if is_allocated else self.due_fail).append(ue)
            elif ue.ue_type == UEType.E:
                (self.eue_allocated if is_allocated else self.eue_fail).append(ue)
            else:
                raise AssertionError

    @staticmethod
    def update_empty_space(nb: Union[GNodeB, ENodeB]) -> Tuple[Space]:
        tmp_spaces: List[Space] = []
        for layer in nb.frame.layer:
            do_extend: bool = True
            new_spaces: Tuple[Space] = empty_space(layer)

            # skip the layer if there is a complete layer in tmp_space already
            if len(new_spaces) == 1:
                for space in tmp_spaces:
                    if (new_spaces[0].starting_i == space.starting_i == 0) and (
                            new_spaces[0].starting_j == space.starting_j == 0) and (
                            new_spaces[0].ending_i == space.ending_i == nb.frame.frame_freq - 1) and (
                            new_spaces[0].ending_j == space.ending_j == nb.frame.frame_time - 1):
                        do_extend: bool = False
                        break
            if do_extend:
                tmp_spaces.extend(new_spaces)
        return tuple(tmp_spaces)

    @staticmethod
    def assert_is_empty(spaces, this_ue, is_allocated):
        for space in spaces:
            for i in range(space.starting_i, space.ending_i + 1):
                for j in range(space.starting_j, space.ending_j + 1):
                    if space.layer.bu_status[i][j]:
                        assert space.layer.bu[i][j].within_rb.ue is this_ue, "Which UE is this???"
                        assert is_allocated is True, "undo() fail. Space not cleared"
                        raise AssertionError
