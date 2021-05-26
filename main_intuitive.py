import os
import sys
from datetime import datetime
from typing import Tuple

from src.resource_allocation.algo.algo_intuitive import Intuitive
from src.resource_allocation.algo.utils import divide_ue
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.simulation.data.data_loader import DataLoader
from utils.pickle_generator import visualize_phase_uncategorized_ue


def intuitive_resource_allocation(data_set, visualize_the_algo: bool = False) -> Tuple[
    GNodeB, ENodeB, Tuple[DUserEquipment, ...], Tuple[GUserEquipment, ...], Tuple[EUserEquipment, ...]]:
    dirname = os.path.dirname(__file__)
    file_name_vis = "vis_baseline_" + datetime.today().strftime('%Y%m%d') + ".P"
    visualization_file_path = os.path.join(dirname, 'utils/frame_visualizer', file_name_vis)

    data_set_file_path = os.path.join(dirname, 'src/simulation/data', data_set + '.json')
    g_nb, e_nb, channel_model, g_ue_list, d_ue_list, e_ue_list, _, _, _, _ = DataLoader().run(data_set_file_path)

    # main
    Intuitive(g_nb, e_nb, g_ue_list + d_ue_list, tuple(), channel_model).allocate(allow_lower_mcs=False)
    gue_allocated, _ = divide_ue(g_ue_list)
    due_allocated, due_unallocated = divide_ue(d_ue_list)
    Intuitive(e_nb, g_nb, e_ue_list + due_unallocated, gue_allocated + due_allocated, channel_model).allocate(
        allow_lower_mcs=False)

    if visualize_the_algo:
        visualize_phase_uncategorized_ue(visualization_file_path, 'wb',
                                         "baseline", g_nb, e_nb, g_ue_list, d_ue_list, e_ue_list)
    return g_nb, e_nb, d_ue_list, g_ue_list, e_ue_list


if __name__ == '__main__':
    file_path: str = '0526-180322L_/4layer/2'
    if len(sys.argv) == 2:
        file_path: str = sys.argv[1]
    intuitive_resource_allocation(data_set=file_path, visualize_the_algo=True)
