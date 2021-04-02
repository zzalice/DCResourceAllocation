import os
import pickle
import sys
from typing import Tuple, Union

from src.resource_allocation.algo.algo_mcuphm import McupHm
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment


def mcup_hm(data_set) -> Tuple[GNodeB, ENodeB,
                               Tuple[Union[GUserEquipment, DUserEquipment]],
                               Tuple[Union[EUserEquipment, DUserEquipment]],
                               Tuple[GUserEquipment], Tuple[EUserEquipment], Tuple[DUserEquipment]]:
    with open(f'{os.path.dirname(__file__)}/src/simulation/data/{data_set}.P', "rb") as file:
        g_nb, e_nb, channel_model, g_ue_list, d_ue_list, e_ue_list, gue_qos, eue_qos, _, _ = pickle.load(file)

    # main
    mcup = McupHm()
    mcup.calc_max_serve_ue(g_nb, (gue_qos[0], gue_qos[1]))
    mcup.calc_max_serve_ue(e_nb, (eue_qos[0], eue_qos[1]))
    mcup.due_preference_order(d_ue_list)
    mcup.algorithm(e_ue_list + g_ue_list + d_ue_list)
    eue_unassigned: Tuple[EUserEquipment] = mcup.left_over(e_ue_list)
    gue_unassigned: Tuple[GUserEquipment] = mcup.left_over(g_ue_list)
    due_unassigned: Tuple[DUserEquipment] = mcup.left_over(d_ue_list)

    return g_nb, e_nb, mcup.gnb_ue_list, mcup.enb_ue_list, gue_unassigned, eue_unassigned, due_unassigned


if __name__ == '__main__':
    file_path: str = '0402-090957test_mcup/3layer/0'

    if len(sys.argv) == 2:
        file_path: str = sys.argv[1]
    mcup_hm(file_path)
