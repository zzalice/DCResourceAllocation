import os
import sys
from typing import List, Tuple, Union

from src.resource_allocation.algo.algo_mcuphm import McupHm
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.simulation.data.data_loader import DataLoader


def mcup_hm(g_nb: GNodeB, e_nb: ENodeB, g_ue_list: Tuple[GUserEquipment, ...], d_ue_list: Tuple[DUserEquipment, ...],
            e_ue_list: Tuple[EUserEquipment, ...], gue_qos: Tuple[int, int], eue_qos: Tuple[int, int]
            ) -> Tuple[Tuple[Union[GUserEquipment, DUserEquipment], ...],
                       Tuple[Union[EUserEquipment, DUserEquipment], ...],
                       Tuple[DUserEquipment, ...]]:
    """
    :return gnb_sc_ue, enb_sc_ue: The single connection UEs that are assigned to gNB/eNB.
    :return dc_ue: The dual connection UE that must connect to two BSs.
    """
    mcup = McupHm()
    mcup.calc_max_serve_ue(g_nb, (gue_qos[0], gue_qos[1]))
    mcup.calc_max_serve_ue(e_nb, (eue_qos[0], eue_qos[1]))
    mcup.due_preference_order(d_ue_list)
    mcup.algorithm(e_ue_list + g_ue_list + d_ue_list)

    for ue in e_ue_list + g_ue_list + d_ue_list:
        assert len(ue.nb_preference) == 0
    gue_unassigned: Tuple[GUserEquipment, ...] = mcup.left_over(g_ue_list)
    eue_unassigned: Tuple[EUserEquipment, ...] = mcup.left_over(e_ue_list)
    due_unassigned: Tuple[DUserEquipment, ...] = mcup.left_over(d_ue_list)
    mcup.set_preference(mcup.gnb_ue_list + gue_unassigned, g_nb.nb_type)
    mcup.set_preference(mcup.enb_ue_list + eue_unassigned, e_nb.nb_type)
    gnb_sc_due, enb_sc_due = mcup.set_preference_due(due_unassigned)
    for ue in e_ue_list + g_ue_list:
        assert len(ue.nb_preference) == 1

    gnb_sc_ue: List[Union[GUserEquipment, DUserEquipment]] = list(mcup.gnb_ue_list + gue_unassigned + gnb_sc_due)
    enb_sc_ue: List[Union[EUserEquipment, DUserEquipment]] = list(mcup.enb_ue_list + eue_unassigned + enb_sc_due)
    dc_ue: List[DUserEquipment] = []
    for due in d_ue_list:
        assert 1 <= len(set(due.nb_preference)) <= 2
        if len(set(due.nb_preference)) == 2:
            dc_ue.append(due)
            gnb_sc_ue.remove(due)
            enb_sc_ue.remove(due)
    assert len(gnb_sc_ue + enb_sc_ue + dc_ue) == len(g_ue_list + e_ue_list + d_ue_list)

    return tuple(gnb_sc_ue), tuple(enb_sc_ue), tuple(dc_ue)


def main(data_set: str):
    data_set_file_path = f'{os.path.dirname(__file__)}/src/simulation/data/{data_set}.json'
    g_nb, e_nb, _, g_ue_list, d_ue_list, e_ue_list, gue_qos, eue_qos, _, _ = DataLoader().run(data_set_file_path)
    mcup_hm(g_nb, e_nb, g_ue_list, d_ue_list, e_ue_list, gue_qos, eue_qos)


if __name__ == '__main__':
    file_path: str = '0526-180322L_/4layer/2'

    if len(sys.argv) == 2:
        file_path: str = sys.argv[1]
    main(file_path)
