import pickle
from datetime import datetime
from typing import Tuple

from src.channel_model.sinr import ChannelModel
from src.resource_allocation.algo.assistance import calc_system_throughput, divide_ue
from src.resource_allocation.algo.phase1 import Phase1
from src.resource_allocation.algo.phase2 import Phase2
from src.resource_allocation.algo.phase3 import Phase3
from src.resource_allocation.ds.eutran import EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GUserEquipment
from src.resource_allocation.ds.zone import Zone, ZoneGroup

if __name__ == '__main__':
    visualize_the_algo: bool = True
    visualization_file_path = "../utils/frame_visualizer/vis_" + datetime.today().strftime('%Y%m%d')
    data_set_file_path = "../src/resource_allocation/simulation/data/" + "data_generator" + ".P"

    with open(data_set_file_path, "rb") as file:
        g_nb, e_nb, cochannel_index, g_ue_list, d_ue_list, e_ue_list = pickle.load(file)

    # noinspection PyTypeChecker
    g_phase1: Phase1 = Phase1(g_ue_list + d_ue_list)
    g_phase1.calc_inr(0.5)
    g_phase1.select_init_numerology()
    g_zone_fit, g_zone_undersized = g_phase1.form_zones(g_nb)
    g_zone_merged: Tuple[Zone, ...] = g_phase1.merge_zone(g_zone_undersized)
    g_zone_wide, g_zone_narrow = g_phase1.categorize_zone(g_zone_fit, g_zone_merged)

    g_phase2: Phase2 = Phase2(g_nb)
    layer_using: int = g_phase2.calc_layer_using(g_zone_wide)
    g_zone_groups: Tuple[ZoneGroup, ...] = g_phase2.form_group(g_zone_wide, layer_using)
    g_zone_groups: Tuple[ZoneGroup, ...] = g_phase2.calc_residual_degree(g_zone_groups)
    g_zone_groups_allocated, g_zone_unallocated = g_phase2.allocate_zone_group(g_zone_groups)
    g_zone_allocated: Tuple[Zone, ...] = g_phase2.allocate_zone_to_layer(g_zone_unallocated)
    g_ue_list_allocated, g_ue_list_unallocated = divide_ue(g_ue_list)
    _, d_ue_list_unallocated = divide_ue(d_ue_list)

    # noinspection PyTypeChecker
    e_phase1: Phase1 = Phase1(e_ue_list + d_ue_list_unallocated)
    e_zone_fit, e_zone_undersized = e_phase1.form_zones(e_nb)
    e_zone_merged: Tuple[Zone, ...] = e_phase1.merge_zone(e_zone_undersized)
    e_zone_wide, e_zone_narrow = e_phase1.categorize_zone(e_zone_fit, e_zone_merged)

    e_phase2: Phase2 = Phase2(e_nb)
    e_zone_allocated: Tuple[Zone, ...] = e_phase2.allocate_zone_to_layer(e_zone_wide)  # TODO: CP value isn't implemented
    e_ue_list_allocated, e_ue_list_unallocated = divide_ue(e_ue_list)
    d_ue_list_allocated, d_ue_list_unallocated = divide_ue(d_ue_list)

    if visualize_the_algo:
        with open(visualization_file_path + ".P", "wb") as file:
            pickle.dump(["Phase2",
                         g_nb.frame, e_nb.frame, 0,
                         {"allocated": g_ue_list_allocated, "unallocated": g_ue_list_unallocated},
                         {"allocated": d_ue_list_allocated, "unallocated": d_ue_list_unallocated},
                         {"allocated": e_ue_list_allocated, "unallocated": e_ue_list_unallocated}],
                        file)

    ue_list_unallocated: Tuple[Tuple[GUserEquipment, ...], Tuple[DUserEquipment, ...], Tuple[EUserEquipment, ...]] = (
        g_ue_list_unallocated, d_ue_list_unallocated, e_ue_list_unallocated)
    phase3: Phase3 = Phase3(ChannelModel(cochannel_index), g_nb, e_nb)
    phase3.zone_adjust_mcs(e_zone_allocated)
    phase3.zone_adjust_mcs(g_zone_allocated)
    # phase3.zone_group_adjust_mcs(g_zone_groups_allocated)
    # g_ue_list_allocated, g_ue_list_unallocated = divide_ue(g_ue_list)
    # d_ue_list_allocated, d_ue_list_unallocated = divide_ue(d_ue_list)
    # e_ue_list_allocated, e_ue_list_unallocated = divide_ue(e_ue_list)
    # phase3.allocate_new_ue()    # ue_list_unallocated

    if visualize_the_algo:
        g_ue_list_allocated, g_ue_list_unallocated = divide_ue(g_ue_list)
        d_ue_list_allocated, d_ue_list_unallocated = divide_ue(d_ue_list)
        e_ue_list_allocated, e_ue_list_unallocated = divide_ue(e_ue_list)
        with open(visualization_file_path + ".P", "ab+") as file:
            pickle.dump(["Phase3",
                         g_nb.frame, e_nb.frame,
                         calc_system_throughput(g_ue_list_allocated + d_ue_list_allocated + e_ue_list_allocated),
                         {"allocated": g_ue_list_allocated, "unallocated": g_ue_list_unallocated},
                         {"allocated": d_ue_list_allocated, "unallocated": d_ue_list_unallocated},
                         {"allocated": e_ue_list_allocated, "unallocated": e_ue_list_unallocated}],
                        file)
