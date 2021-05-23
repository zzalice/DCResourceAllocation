import os
import pickle
import sys
from datetime import datetime
from typing import List, Tuple

from src.resource_allocation.algo.phase1 import Phase1
from src.resource_allocation.algo.phase2 import Phase2
from src.resource_allocation.algo.phase3 import Phase3
from src.resource_allocation.algo.utils import divide_ue
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.resource_allocation.ds.zone import Zone, ZoneGroup
from utils.pickle_generator import visualize_phase_uncategorized_ue


def dc_resource_allocation(data_set, visualize_the_algo: bool = False) -> Tuple[
    GNodeB, ENodeB, List[DUserEquipment], List[GUserEquipment], List[EUserEquipment]]:
    dirname = os.path.dirname(__file__)
    file_name_vis = "vis_" + datetime.today().strftime('%Y%m%d') + ".P"
    visualization_file_path = os.path.join(dirname, 'utils/frame_visualizer', file_name_vis)

    data_set_file_path = os.path.join(dirname, 'src/simulation/data', data_set + '.P')
    with open(data_set_file_path, "rb") as file:
        g_nb, e_nb, channel_model, g_ue_list, d_ue_list, e_ue_list, _, _, inr_discount, worsen_threshold = pickle.load(
            file)

    # gNB phase 1
    # noinspection PyTypeChecker
    g_phase1: Phase1 = Phase1(d_ue_list + g_ue_list)
    g_phase1.calc_inr(inr_discount)
    g_phase1.select_init_numerology()
    g_zone_fit, g_zone_undersized = g_phase1.form_zones(g_nb)
    g_zone_merged: Tuple[Zone, ...] = g_phase1.merge_zone(g_zone_undersized)
    g_zone_wide, g_zone_narrow = g_phase1.categorize_zone(g_zone_fit, g_zone_merged)

    # gNB phase 2
    g_phase2: Phase2 = Phase2(g_nb)
    layer_using: int = g_phase2.calc_layer_using(g_zone_wide)
    g_zone_groups: Tuple[ZoneGroup, ...] = g_phase2.form_group(g_zone_wide, layer_using)
    g_zone_groups: Tuple[ZoneGroup, ...] = g_phase2.calc_residual_degree(g_zone_groups)
    g_zone_allocated, g_zone_unallocated = g_phase2.allocate_zone_group(g_zone_groups)
    g_zone_allocated: List[List[Zone]] = g_phase2.allocate_zone_to_layer(g_nb.nb_type, g_zone_allocated,
                                                                         g_zone_unallocated)
    _, d_ue_list_unallocated = divide_ue(d_ue_list, is_assert=False)

    # eNB phase 1
    # noinspection PyTypeChecker
    e_phase1: Phase1 = Phase1(d_ue_list_unallocated + e_ue_list)
    e_zone_fit, e_zone_undersized = e_phase1.form_zones(e_nb)
    e_zone_merged: Tuple[Zone, ...] = e_phase1.merge_zone(e_zone_undersized)
    e_zone_wide, e_zone_narrow = e_phase1.categorize_zone(e_zone_fit, e_zone_merged)

    # eNB phase 2
    e_phase2: Phase2 = Phase2(e_nb)
    e_zone_allocated: List[List[Zone]] = e_phase2.allocate_zone_to_layer(e_nb.nb_type, [[]], e_zone_wide)

    if visualize_the_algo:
        visualize_phase_uncategorized_ue(visualization_file_path, "wb",
                                         "Phase2", g_nb, e_nb, g_ue_list, d_ue_list, e_ue_list, is_assert=False)

    # phase 3 step 1
    phase3: Phase3 = Phase3(channel_model)
    phase3.phase2_ue_adjust_mcs(e_nb, e_zone_allocated)
    phase3.phase2_ue_adjust_mcs(g_nb, g_zone_allocated)

    if visualize_the_algo:
        visualize_phase_uncategorized_ue(visualization_file_path, "ab+",
                                         "Phase3_zoneGroup", g_nb, e_nb, g_ue_list, d_ue_list, e_ue_list)

    # gNB step 2
    g_ue_list_allocated, g_ue_list_unallocated = divide_ue(g_ue_list)
    d_ue_list_allocated, d_ue_list_unallocated = divide_ue(d_ue_list)
    e_ue_list_allocated, e_ue_list_unallocated = divide_ue(e_ue_list)
    phase3.allocate_new_ue(g_nb, d_ue_list_unallocated + g_ue_list_unallocated,
                           d_ue_list_allocated + g_ue_list_allocated + e_ue_list_allocated, worsen_threshold)

    # eNB step 2
    g_ue_list_allocated, g_ue_list_unallocated = divide_ue(g_ue_list)
    d_ue_list_allocated, d_ue_list_unallocated = divide_ue(d_ue_list)
    e_ue_list_allocated, _ = divide_ue(e_ue_list)  # for the concern of co-channel area
    phase3.allocate_new_ue(e_nb, d_ue_list_unallocated + e_ue_list_unallocated,
                           d_ue_list_allocated + g_ue_list_allocated + e_ue_list_allocated, worsen_threshold)

    if visualize_the_algo:
        visualize_phase_uncategorized_ue(visualization_file_path, "ab+",
                                         "Phase3_newUE", g_nb, e_nb, g_ue_list, d_ue_list, e_ue_list)

    return g_nb, e_nb, d_ue_list, g_ue_list, e_ue_list


if __name__ == '__main__':
    file_path: str = '0513-010046L_/5layer/0'
    if len(sys.argv) == 2:
        file_path: str = sys.argv[1]
    dc_resource_allocation(data_set=file_path, visualize_the_algo=True)
