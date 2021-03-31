import os
import pickle
import sys
from typing import Tuple, Union

from src.resource_allocation.algo.algo_mcuphm import McupHm
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment


def mcup_hm(data_set) -> Tuple[GNodeB, ENodeB,
                               Tuple[Union[GUserEquipment, DUserEquipment], ...],
                               Tuple[Union[EUserEquipment, DUserEquipment], ...],
                               Tuple[DUserEquipment, ...]]:
    dirname = os.path.dirname(__file__)
    data_set_file_path = os.path.join(dirname, 'src/simulation/data', data_set + '.P')
    with open(data_set_file_path, "rb") as file:
        g_nb, e_nb, cochannel_index, channel_model, g_ue_list, d_ue_list, e_ue_list, _, _ = pickle.load(file)  # FIXME: pass eUE, gUE demand range in Tuple[int, int]

    # main
    mcup = McupHm()
    mcup.calc_max_serve_ue(g_nb, (1000_000, 1512_000))  # FIXME
    mcup.calc_max_serve_ue(e_nb, (1000_000, 1512_000))
    gue_unassigned: Tuple[GUserEquipment] = mcup.assign_single_connection_ue(g_nb.nb_type, g_ue_list)
    eue_unassigned: Tuple[EUserEquipment] = mcup.assign_single_connection_ue(e_nb.nb_type, e_ue_list)
    due_unassigned: Tuple[DUserEquipment] = mcup.assign_dual_connection_ue(d_ue_list)
    mcup.append_left_over(g_nb.nb_type, gue_unassigned)  # Notice: unassigned dUE are not append to any BS
    mcup.append_left_over(e_nb.nb_type, eue_unassigned)

    return g_nb, e_nb, mcup.gnb_ue_list, mcup.enb_ue_list, due_unassigned


if __name__ == '__main__':
    file_path: str = '0318-004644low_qos/1layer/0'

    if len(sys.argv) == 2:
        file_path: str = sys.argv[1]
    mcup_hm(file_path)
