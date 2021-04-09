import os
import pickle
from datetime import datetime
from typing import List, Tuple

from main_mcuphm import mcup_hm
from src.resource_allocation.algo.algo_intuitive import Intuitive
from src.resource_allocation.algo.frsa.frsa_phase1 import FRSAPhase1
from src.resource_allocation.algo.frsa.frsa_phase2 import FRSAPhase2
from src.resource_allocation.algo.frsa.frsa_phase3 import FRSAPhase3
from src.resource_allocation.algo.utils import divide_ue
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from utils.pickle_generator import visualize_phase_uncategorized_ue


def frsa(data_set: str, visualize_the_algo: bool = False) -> Tuple[
    GNodeB, ENodeB, List[DUserEquipment], List[GUserEquipment], List[EUserEquipment]]:
    """
    Combines FRSA with MCUP.
    :param data_set:
    :param visualize_the_algo:
    :return:
    """
    dirname = os.path.dirname(__file__)
    file_name_vis = "vis_frsa_" + datetime.today().strftime('%Y%m%d') + ".P"
    visualization_file_path = os.path.join(dirname, 'utils/frame_visualizer', file_name_vis)

    data_set_file_path = os.path.join(dirname, 'src/simulation/data', data_set + '.P')
    with open(data_set_file_path, "rb") as file:
        g_nb, e_nb, channel_model, g_ue_list, d_ue_list, e_ue_list, gue_qos, eue_qos, _, _ = pickle.load(file)

    # main
    # DC user association
    gnb_sc_ue_list, enb_sc_ue_list, dc_ue_list = mcup_hm(g_nb, e_nb, g_ue_list, d_ue_list, e_ue_list, gue_qos, eue_qos)

    # gNB resource allocation
    g_phase1: FRSAPhase1 = FRSAPhase1(g_nb, dc_ue_list + gnb_sc_ue_list)
    g_phase1.calc_inr()
    g_phase1.select_init_numerology()
    g_zone_wide, g_zone_narrow = g_phase1.form_and_categorize_zone()
    g_zone_merged = g_phase1.merge_zone_over_half(g_zone_narrow)
    g_zone_wide, g_zone_narrow = g_phase1.categorize_zone(g_zone_wide, g_zone_merged)
    g_zone_allocated, g_zone_unallocated = g_phase1.virtual_allocate_zone(g_zone_wide)

    g_phase2: FRSAPhase2 = FRSAPhase2(g_nb, g_zone_allocated)
    g_phase2.zd()
    g_phase2.za()
    gnb_allocated, gnb_unallocated = divide_ue(dc_ue_list + gnb_sc_ue_list, is_assert=False)

    if visualize_the_algo:
        visualize_phase_uncategorized_ue(visualization_file_path, 'wb',
                                         "phase2", g_nb, e_nb, g_ue_list, d_ue_list, e_ue_list, is_assert=False)

    g_phase3: FRSAPhase3 = FRSAPhase3(g_nb, channel_model)
    g_phase3.adjust_mcs(gnb_allocated)
    gnb_allocated, gnb_unallocated = divide_ue(dc_ue_list + gnb_sc_ue_list)
    g_phase3.allocate_new_ue(gnb_unallocated, gnb_allocated)

    # eNB resource allocation
    gnb_sc_allocated, gnb_sc_unallocated = divide_ue(gnb_sc_ue_list)
    dc_ue_allocated, dc_ue_unallocated = divide_ue(dc_ue_list)
    # FIXME dc_ue_allocated +
    Intuitive(e_nb, enb_sc_ue_list, gnb_sc_allocated + dc_ue_allocated, channel_model).allocate(
        allow_lower_mcs=False)

    if visualize_the_algo:
        visualize_phase_uncategorized_ue(visualization_file_path, 'ab+',
                                         "phase3", g_nb, e_nb, g_ue_list, d_ue_list, e_ue_list)

    return g_nb, e_nb, d_ue_list, g_ue_list, e_ue_list


if __name__ == '__main__':
    file_path: str = '0409-143305test_mcup/4layer/5'
    frsa(file_path, visualize_the_algo=True)
