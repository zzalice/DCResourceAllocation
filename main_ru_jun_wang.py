import os
import pickle
from datetime import datetime

from src.resource_allocation.algo.ru_jun_wang.wangphase1 import WangPhase1
from src.resource_allocation.algo.ru_jun_wang.wangphase2 import WangPhase2
from utils.pickle_generator import visualize_phase_uncategorized_ue

if __name__ == '__main__':
    visualize_the_algo: bool = True
    dirname = os.path.dirname(__file__)
    file_name_vis = "vis_wang_" + datetime.today().strftime('%Y%m%d') + ".P"
    visualization_file_path = os.path.join(dirname, 'utils/frame_visualizer', file_name_vis)

    data_set_file_path = os.path.join(dirname, 'src/simulation/data', 'data_generator.P')
    with open(data_set_file_path, "rb") as file:
        g_nb, e_nb, cochannel_index, channel_model, g_ue_list, d_ue_list, e_ue_list = pickle.load(file)

    g_phase1: WangPhase1 = WangPhase1(g_nb, g_ue_list + d_ue_list)
    g_phase1.calc_inr()
    g_phase1.select_init_numerology()
    g_zone_wide, g_zone_narrow = g_phase1.form_and_categorize_zone()
    g_zone_merged = g_phase1.merge_zone(g_zone_narrow, row_limit=False)
    g_zone_wide, g_zone_narrow = g_phase1.categorize_zone(g_zone_wide, g_zone_merged)
    g_zone_allocated, g_zone_unallocated = g_phase1.allocate_zone_to_layer(g_zone_wide)

    g_phase2: WangPhase2 = WangPhase2(g_nb, g_zone_allocated)
    g_phase2.calc_total_freq_space()

    if visualize_the_algo:
        visualize_phase_uncategorized_ue(visualization_file_path, "wb",
                                         "Phase1", g_nb, e_nb, g_ue_list, d_ue_list, e_ue_list, is_assert=False)

    # TODO 先調整完gNB再分配eNB
