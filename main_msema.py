import os
import pickle
from datetime import datetime
from typing import List, Tuple

from src.resource_allocation.algo.algo_intuitive import Intuitive
from src.resource_allocation.algo.algo_msema import Msema
from src.resource_allocation.algo.utils import divide_ue
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from utils.pickle_generator import visualize_phase_uncategorized_ue


def msema_rb_ra(data_set: str, visualize_the_algo: bool = False) -> Tuple[
                                    GNodeB, ENodeB, List[DUserEquipment], List[GUserEquipment], List[EUserEquipment]]:
    dirname = os.path.dirname(__file__)
    file_name_vis = "vis_msema_" + datetime.today().strftime('%Y%m%d') + ".P"
    visualization_file_path = os.path.join(dirname, 'utils/frame_visualizer', file_name_vis)

    data_set_file_path = os.path.join(dirname, 'src/simulation/data', data_set + '.P')
    with open(data_set_file_path, "rb") as file:
        g_nb, e_nb, channel_model, g_ue_list, d_ue_list, e_ue_list, _, _, _, _ = pickle.load(file)

    # main
    # gNB resource allocation
    Msema(g_nb, channel_model, ()).allocate_ue_list(g_ue_list + d_ue_list)

    # eNB resource allocation
    gue_allocated, gue_unallocated = divide_ue(g_ue_list)
    due_allocated, due_unallocated = divide_ue(d_ue_list)
    Intuitive(e_nb, e_ue_list + due_unallocated, gue_allocated + due_allocated, channel_model).allocate(
        allow_lower_mcs=False)

    if visualize_the_algo:
        visualize_phase_uncategorized_ue(visualization_file_path, 'wb',
                                         "MSEMA", g_nb, e_nb, g_ue_list, d_ue_list, e_ue_list)

    return g_nb, e_nb, d_ue_list, g_ue_list, e_ue_list


if __name__ == '__main__':
    file_path: str = '0406-132558test_many_ue/2layer/5'
    msema_rb_ra(file_path, visualize_the_algo=True)
