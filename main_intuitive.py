import os
import pickle
import sys
from datetime import datetime
from typing import List, Tuple

from src.resource_allocation.algo.algo_intuitive import Intuitive
from src.resource_allocation.algo.utils import divide_ue
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from utils.pickle_generator import visualize_phase_uncategorized_ue


def intuitive_resource_allocation(data_set, visualize_the_algo: bool = False) -> Tuple[
    GNodeB, ENodeB, List[DUserEquipment], List[GUserEquipment], List[EUserEquipment]]:
    dirname = os.path.dirname(__file__)
    file_name_vis = "vis_intuitive_" + datetime.today().strftime('%Y%m%d') + ".P"
    visualization_file_path = os.path.join(dirname, 'utils/frame_visualizer', file_name_vis)

    data_set_file_path = os.path.join(dirname, 'src/simulation/data', data_set + '.P')
    with open(data_set_file_path, "rb") as file:
        g_nb, e_nb, cochannel_index, channel_model, g_ue_list, d_ue_list, e_ue_list, _, _ = pickle.load(file)

    # main
    Intuitive(g_nb, g_ue_list + d_ue_list, tuple(), channel_model).allocate(allow_lower_mcs=False)
    gue_allocated, gue_unallocated = divide_ue(g_ue_list)
    due_allocated, due_unallocated = divide_ue(d_ue_list)
    Intuitive(e_nb, e_ue_list + due_unallocated, gue_allocated + due_allocated, channel_model).allocate(
        allow_lower_mcs=False)

    if visualize_the_algo:
        visualize_phase_uncategorized_ue(visualization_file_path, 'wb',
                                         "intuitive", g_nb, e_nb, g_ue_list, d_ue_list, e_ue_list)
    return g_nb, e_nb, d_ue_list, g_ue_list, e_ue_list


if __name__ == '__main__':
    file_path: str = '0316-164735small/3layer/0'
    file_path: str = '0316-181915small_frame50/3layer/0'
    file_path: str = '0316-183832small_frame50_moreUE/3layer/0'
    file_path: str = '0318-004644low_qos/1layer/0'
    if len(sys.argv) == 2:
        file_path: str = sys.argv[1]
    intuitive_resource_allocation(data_set=file_path, visualize_the_algo=True)
