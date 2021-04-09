from math import ceil, floor
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
        count_frame_rb: float = (nb.frame.frame_freq * nb.frame.frame_time * nb.frame.max_layer) / count_rb_bu

        if nb.nb_type == NodeBType.G:
            self.gnb_max_serve = floor(count_frame_rb / count_ue_rb)
        elif nb.nb_type == NodeBType.E:
            self.enb_max_serve = ceil(count_frame_rb / count_ue_rb)
        else:
            raise AssertionError

    @staticmethod
    def due_preference_order(due_list: Tuple[DUserEquipment]):
        for due in due_list:
            if due.coordinate.distance_enb > due.coordinate.distance_gnb:
                due.nb_preference = [0, 1]
            else:
                due.nb_preference = [1, 0]

    def algorithm(self, ue_list: Tuple[UE]):
        """
        Refer to the pseudocode in "Multi-Connectivity Enabled User Association".
        :param ue_list: All the UEs in the system.
        :return:
        """
        ue_list: List[UE] = list(ue_list)
        while ue_list:
            n_i: UE = ue_list.pop(0)  # ue
            m_j: int = n_i.nb_preference.pop(0)  # nb
            is_assigned, ue_ = self.assign(n_i, m_j)
            self.update(is_assigned, n_i, ue_)
            self.append_ue(ue_list, n_i)
            self.append_ue(ue_list, ue_)

    def assign(self, ue: UE, nb: int) -> Tuple[bool, UE]:
        """
        Subscribe to NodeB.
        :param ue: The UE to assign to nb
        :param nb: 0 represent eNB, 1 represent gNB.
        :return: Whether the input ue is assigned and the UE to be updated.
        """
        if nb == 0:
            self._enb_ue_list.append(ue)
            if len(self._enb_ue_list) > self.enb_max_serve:
                self._enb_ue_list.sort(key=lambda x: x.coordinate.distance_enb)  # better channel quality
                rejected: UE = self._enb_ue_list.pop()
                return not (rejected == ue), rejected
        elif nb == 1:
            self._gnb_ue_list.append(ue)
            if len(self._gnb_ue_list) > self.gnb_max_serve:
                self._gnb_ue_list.sort(key=lambda x: x.coordinate.distance_gnb)
                rejected: UE = self._gnb_ue_list.pop()
                return not (rejected == ue), rejected
        else:
            raise AssertionError
        return True, ue

    @staticmethod
    def update(is_assigned: bool, ue: UE, ue_: UE):
        if is_assigned:
            # ue was assigned
            if ue == ue_:
                # BS can serve more UE than rejecting any
                ue.connection_preference -= 1
                assert ue.connection_preference >= 0
            else:
                # BS has reached connection limit so ue_ was rejected
                ue_.connection_preference += 1
                assert ue_.connection_preference >= 0
        else:
            if ue == ue_:
                # ue was rejected
                pass  # nothing to update
            else:
                raise AssertionError

    @staticmethod
    def append_ue(ue_list: List[UE], ue: UE):
        if ue not in ue_list and ue.connection_preference > 0 and ue.nb_preference:  # there is other BS options for ue
            ue_list.append(ue)

    def left_over(self, ue_list: Tuple[UE]) -> Tuple[UE, ...]:
        unassigned_ue: List[UE] = []
        for ue in ue_list:
            if ue not in self.gnb_ue_list + self.enb_ue_list:
                unassigned_ue.append(ue)
        return tuple(unassigned_ue)

    @property
    def gnb_ue_list(self) -> Tuple[Union[GUserEquipment, DUserEquipment], ...]:
        return tuple(self._gnb_ue_list)

    @property
    def enb_ue_list(self) -> Tuple[Union[EUserEquipment, DUserEquipment], ...]:
        return tuple(self._enb_ue_list)
