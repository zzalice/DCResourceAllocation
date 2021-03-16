import os
import pickle
import sys
from datetime import datetime
from typing import List, Tuple

from src.resource_allocation.algo.intuitive_algo import Intuitive
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from utils.pickle_generator import visualize_phase


def intuitive_resource_allocation(data_set, visualize_the_algo: bool = False) -> Tuple[
                                    GNodeB, ENodeB, List[DUserEquipment], List[GUserEquipment], List[EUserEquipment]]:
    dirname = os.path.dirname(__file__)
    file_name_vis = "vis_intuitive_" + datetime.today().strftime('%Y%m%d') + ".P"
    visualization_file_path = os.path.join(dirname, 'utils/frame_visualizer', file_name_vis)

    data_set_file_path = os.path.join(dirname, 'src/simulation/data', data_set + '.P')
    with open(data_set_file_path, "rb") as file:
        g_nb, e_nb, cochannel_index, channel_model, g_ue_list, d_ue_list, e_ue_list, _ = pickle.load(file)

    intuitive: Intuitive = Intuitive(g_nb, e_nb, cochannel_index, g_ue_list, d_ue_list, e_ue_list)
    intuitive.algorithm()

    if visualize_the_algo:
        visualize_phase(visualization_file_path, 'wb',
                        "intuitive", g_nb, e_nb, tuple(intuitive.gue_allocated), tuple(intuitive.due_allocated),
                        tuple(intuitive.eue_allocated), tuple(intuitive.gue_fail), tuple(intuitive.due_fail),
                        tuple(intuitive.eue_fail))

    return g_nb, e_nb, d_ue_list, g_ue_list, e_ue_list


if __name__ == '__main__':
    file_path: str = '0315-094335small/3layer/0'
    if len(sys.argv) == 2:
        file_path: str = sys.argv[1]
    intuitive_resource_allocation(data_set=file_path, visualize_the_algo=True)
