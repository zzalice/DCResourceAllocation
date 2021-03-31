from math import ceil
from typing import List, Tuple, Union

from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.resource_allocation.ds.util_enum import E_MCS, G_MCS, LTEResourceBlock, NodeBType, Numerology

UE = Union[GUserEquipment, DUserEquipment, EUserEquipment]


class McupHm:
    def __init__(self):
        self.gnb_max_serve: int = 0
        self.enb_max_serve: int = 0
        self._gnb_ue_list: List[Union[GUserEquipment, DUserEquipment]] = []
        self._enb_ue_list: List[Union[EUserEquipment, DUserEquipment]] = []

    def calc_max_serve_ue(self, nb: Union[GNodeB, ENodeB], qos: Tuple[int, int]):
        # count how many RB a UE will need
        qos: List[float] = [i / (1000 // (nb.frame.frame_time // 8)) for i in qos]  # bps to bit per frame
        qos_avg: float = (qos[0] + qos[1]) / 2  # bit per frame
        rate_rb: float = G_MCS.CQI15.value if nb.nb_type == NodeBType.G else E_MCS.CQI15.value  # bit per RB
        count_ue_rb: int = ceil(qos_avg / rate_rb)

        # count how many RB in a layer
        count_rb_bu: int = Numerology.N0.count_bu if nb.nb_type == NodeBType.G else LTEResourceBlock.E.count_bu
        count_frame_rb: float = (nb.frame.frame_freq * nb.frame.frame_time) / count_rb_bu

        if nb.nb_type == NodeBType.G:
            self.gnb_max_serve = ceil(count_frame_rb / count_ue_rb)
        elif nb.nb_type == NodeBType.E:
            self.enb_max_serve = ceil(count_frame_rb / count_ue_rb)
        else:
            raise AssertionError

    def assign_single_connection_ue(self, nb_type: NodeBType, ue_list: Tuple[Union[GUserEquipment, EUserEquipment]]
                                    ) -> Tuple[Union[GUserEquipment, EUserEquipment], ...]:
        ue_list: List[Union[GUserEquipment, EUserEquipment]] = list(ue_list)
        # sort by distance
        if nb_type == NodeBType.G:
            ue_list.sort(key=lambda x: x.coordinate.distance_gnb)
        elif nb_type == NodeBType.E:
            ue_list.sort(key=lambda x: x.coordinate.distance_enb)
        else:
            raise AssertionError

        # append to limit
        nb_max_serve: int = self.gnb_max_serve if nb_type == NodeBType.G else self.enb_max_serve
        i: int = len(ue_list)   # any value to let method return empty array if didn't enter for loop
        for i in range(min(nb_max_serve, len(ue_list))):
            self.append_ue(nb_type, ue_list[i])
        return tuple(ue_list[i+1:])    # ue not assigned

    def assign_dual_connection_ue(self, due_list: Tuple[DUserEquipment]) -> Tuple[DUserEquipment, ...]:
        due_list: List[DUserEquipment] = list(due_list)
        # gNB
        due_list.sort(key=lambda x: x.coordinate.distance_gnb)
        for due in due_list:
            self.append_ue(NodeBType.G, due)

        # eNB
        due_list.sort(key=lambda x: x.coordinate.distance_enb)
        for due in due_list:
            self.append_ue(NodeBType.E, due)

        due_unassigned: List[DUserEquipment] = []
        for due in due_list:
            if due not in self.gnb_ue_list and due not in self.enb_ue_list:
                due_unassigned.append(due)
        return tuple(due_unassigned)

    def append_left_over(self, nb_type: NodeBType, ue_list: Tuple[UE]):
        if nb_type == NodeBType.G:
            self._gnb_ue_list.extend(ue_list)
        elif nb_type == NodeBType.E:
            self._enb_ue_list.extend(ue_list)
        else:
            raise AssertionError

    def append_ue(self, nb_type: NodeBType, ue: UE) -> bool:
        if nb_type == NodeBType.G:
            self._gnb_ue_list.append(ue)
            if len(self._gnb_ue_list) > self.gnb_max_serve:
                self._gnb_ue_list.sort(key=lambda x: x.coordinate.distance_gnb)
                return not(self._gnb_ue_list.pop() == ue)
        elif nb_type == NodeBType.E:
            self._enb_ue_list.append(ue)
            if len(self._enb_ue_list) > self.enb_max_serve:
                self._enb_ue_list.sort(key=lambda x: x.coordinate.distance_enb)
                return not(self._enb_ue_list.pop() == ue)
        else:
            raise AssertionError
        return True

    @property
    def gnb_ue_list(self) -> Tuple[Union[GUserEquipment, DUserEquipment], ...]:
        return tuple(self._gnb_ue_list)

    @property
    def enb_ue_list(self) -> Tuple[Union[EUserEquipment, DUserEquipment], ...]:
        return tuple(self._enb_ue_list)
