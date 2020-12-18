import pickle
from datetime import datetime
from typing import Tuple

from src.channel_model.sinr import ChannelModel
from src.resource_allocation.algo.assistance import cluster_unallocated_ue
from src.resource_allocation.algo.phase1 import Phase1
from src.resource_allocation.algo.phase2 import Phase2
from src.resource_allocation.algo.phase3 import Phase3
from src.resource_allocation.ds.ue import UserEquipment
from src.resource_allocation.ds.zone import Zone, ZoneGroup

if __name__ == '__main__':
    visualize_the_algo: bool = True
    visualization_file_path = "../utils/frame_visualizer/vis_" + datetime.today().strftime('%Y%m%d')
    data_set_file_path = "../src/resource_allocation/simulation/data/" + "data_generator" + ".P"

    with open(data_set_file_path, "rb") as file_of_frame_and_ue:
        g_nb, e_nb, total_bandwidth, g_ue_list, d_ue_list, e_ue_list = pickle.load(file_of_frame_and_ue)

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
    g_zone_unallocated: Tuple[Zone, ...] = g_phase2.allocate_zone_group(g_zone_groups)
    g_phase2.allocate_zone_to_layer(g_zone_unallocated)
    g_ue_list_allocated, g_ue_list_unallocated = cluster_unallocated_ue(g_ue_list)
    d_ue_list_allocated, d_ue_list_unallocated = cluster_unallocated_ue(d_ue_list)

    # noinspection PyTypeChecker
    e_phase1: Phase1 = Phase1(e_ue_list + d_ue_list_unallocated)
    e_zone_fit, e_zone_undersized = e_phase1.form_zones(e_nb)
    e_zone_merged: Tuple[Zone, ...] = e_phase1.merge_zone(e_zone_undersized)
    e_zone_wide, e_zone_narrow = e_phase1.categorize_zone(e_zone_fit, e_zone_merged)

    e_phase2: Phase2 = Phase2(e_nb)
    e_phase2.allocate_zone_to_layer(e_zone_wide)
    e_ue_list_allocated, e_ue_list_unallocated = cluster_unallocated_ue(e_ue_list)
    d_ue_list_unallocated = cluster_unallocated_ue(d_ue_list)[1]

    if visualize_the_algo is True:
        with open(visualization_file_path + ".P", "wb") as file_of_frame_and_ue:
            pickle.dump(["Phase2",
                         g_nb.frame, e_nb.frame,
                         {"allocated": g_ue_list_allocated, "unallocated": g_ue_list_unallocated},
                         {"allocated": d_ue_list_allocated, "unallocated": d_ue_list_unallocated},
                         {"allocated": e_ue_list_allocated, "unallocated": e_ue_list_unallocated}],
                        file_of_frame_and_ue)

    ue_list_allocated: Tuple[UserEquipment] = g_ue_list_allocated + e_ue_list_allocated + d_ue_list_allocated
    ue_list_unallocated: Tuple[UserEquipment] = g_ue_list_unallocated + e_ue_list_unallocated + d_ue_list_unallocated
    phase3: Phase3 = Phase3(ChannelModel(total_bandwidth), ue_list_allocated, ue_list_unallocated)
    phase3.improve_system_throughput()

    if visualize_the_algo is True:
        with open(visualization_file_path + ".P", "ab+") as file_of_frame_and_ue:
            pickle.dump(["Phase3",
                         g_nb.frame, e_nb.frame,
                         {"allocated": g_ue_list_allocated, "unallocated": g_ue_list_unallocated},
                         {"allocated": d_ue_list_allocated, "unallocated": d_ue_list_unallocated},
                         {"allocated": e_ue_list_allocated, "unallocated": e_ue_list_unallocated}],
                        file_of_frame_and_ue)
