import dataclasses
import pickle
from datetime import datetime
from typing import Tuple

from src.resource_allocation.algo.assistance import cluster_unallocated_ue
from src.resource_allocation.algo.phase1 import Phase1
from src.resource_allocation.algo.phase2 import Phase2
from src.resource_allocation.ds.cochannel import cochannel
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.resource_allocation.ds.ue import UserEquipment
from src.resource_allocation.ds.util_enum import LTEPhysicalResourceBlock, Numerology
from src.resource_allocation.ds.util_type import CandidateSet, DistanceRange
from src.resource_allocation.ds.zone import Zone, ZoneGroup


@dataclasses.dataclass
class UEProfiles:
    count: int
    request_data_rate: Tuple[int, ...]
    candidate_set: Tuple[CandidateSet, ...]
    distance: Tuple[float, ...]

    def __iter__(self):
        single_data = dataclasses.make_dataclass('UEProfile', (
            ('request_data_rate', int), ('candidate_set', CandidateSet), ('distance', float)))
        for i in range(self.count):
            yield single_data(self.request_data_rate[i], self.candidate_set[i], self.distance[i])


@dataclasses.dataclass
class DUEProfiles(UEProfiles):
    distance_enb: Tuple[float, ...]

    def __iter__(self):
        single_data = dataclasses.make_dataclass('DUEProfile', (
            ('request_data_rate', int), ('candidate_set', CandidateSet), ('distance', float), ('distance_enb', float)))
        for i in range(self.count):
            yield single_data(self.request_data_rate[i], self.candidate_set[i], self.distance[i], self.distance_enb[i])


if __name__ == '__main__':
    EUE_COUNT = GUE_COUNT = DUE_COUNT = 10
    NB_DISTANCE: float = 1.0

    visualize_the_algo: bool = True
    visualization_file_path = "../utils/frame_visualizer/vis_" + datetime.today().strftime('%Y%m%d') + ".P"

    e_nb: ENodeB = ENodeB()
    g_nb: GNodeB = GNodeB()
    cochannel(e_nb, g_nb)
    distance_range: DistanceRange = UserEquipment.calc_distance_range(e_nb, g_nb, NB_DISTANCE)

    """
    # # sample code to generate random profiles (the last tuple `distance_range.e_random` ONLY exists in dUE)
    # import random
    # frame_time = g_nb.frame.frame_time / 16
    # d_profile: DUEProfiles = DUEProfiles(
    #     DUE_COUNT,
    #     tuple(random.randrange(100_000/frame_time, 3_000_000/frame_time + 1, 10_000/frame_time) for _ in range(DUE_COUNT)),
    #     tuple(Numerology.gen_candidate_set(random_pick=True) for _ in range(DUE_COUNT)),
    #     tuple(distance_range.g_random for _ in range(DUE_COUNT)),
    #     tuple(distance_range.e_random for _ in range(DUE_COUNT))
    # )
    """

    # TODO: eUE and gUE also need a distance to gNB and eNB respectively
    # the recorded random data for POC
    e_profiles: UEProfiles = UEProfiles(
        EUE_COUNT,
        (188, 2874, 535, 2420, 1876, 195, 1188, 1938, 369, 1502),
        LTEPhysicalResourceBlock.gen_candidate_set() * EUE_COUNT,  # dummy (unused)
        (0.1966428804066318, 0.057080955932419464, 1.4405252071379413, 1.0483062430804293, 1.6058972474023123,
         0.8128944817212764, 0.3657009563462874, 0.0353501680934305, 0.6121033657944013, 1.834894681274421)
    )
    g_profiles: UEProfiles = UEProfiles(
        GUE_COUNT,
        (2959, 1178, 2845, 115, 2173, 982, 1273, 876, 2581, 408),
        ((Numerology.N0, Numerology.N2), (Numerology.N0, Numerology.N1), (Numerology.N0, Numerology.N1, Numerology.N2),
         (Numerology.N0, Numerology.N2, Numerology.N3, Numerology.N4),
         (Numerology.N1, Numerology.N2, Numerology.N3, Numerology.N4),
         (Numerology.N0, Numerology.N1, Numerology.N2, Numerology.N3, Numerology.N4),
         (Numerology.N0, Numerology.N1, Numerology.N2, Numerology.N3, Numerology.N4),
         (Numerology.N3,), (Numerology.N1,), (Numerology.N0, Numerology.N2, Numerology.N3)),
        (0.7677129770499276, 0.8157435917373685, 0.91368073427943, 0.2757412263344503, 0.5026575657377796,
         0.32486265346961796, 0.06084168900599651, 0.7298781480380104, 0.6775811631446377, 0.30057089836073225)
    )
    d_profiles: DUEProfiles = DUEProfiles(
        DUE_COUNT,
        (2535, 308, 462, 1376, 2979, 642, 1581, 2162, 2506, 1676),
        ((Numerology.N0, Numerology.N1, Numerology.N2, Numerology.N3, Numerology.N4), (Numerology.N3,),
         (Numerology.N0, Numerology.N1, Numerology.N2, Numerology.N3, Numerology.N4),
         (Numerology.N0, Numerology.N2, Numerology.N3), (Numerology.N0, Numerology.N1, Numerology.N2, Numerology.N4),
         (Numerology.N0, Numerology.N2, Numerology.N3), (Numerology.N2, Numerology.N3, Numerology.N4),
         (Numerology.N1, Numerology.N2), (Numerology.N3,), (Numerology.N1, Numerology.N2, Numerology.N3)),
        # distance to gNB
        (0.8832104044839353, 0.5754695768065541, 0.6192237346764458, 0.6145347127318851, 0.8673121249758964,
         0.3271009411141079, 0.16287824560145325, 0.018620056066250723, 0.5140653976735469, 0.4436894194468033),
        # distance to eNB
        (0.5400880259947132, 1.8254505595966275, 1.781946824652473, 0.9107641326794418, 1.4510985030401478,
         1.8159087210729097, 0.4751103185515886, 0.44364239375116, 1.5278385936317163, 0.4160850979483002)
    )

    e_ue_list: Tuple[EUserEquipment] = tuple(EUserEquipment(e.request_data_rate, e.candidate_set) for e in e_profiles)
    g_ue_list: Tuple[GUserEquipment] = tuple(GUserEquipment(g.request_data_rate, g.candidate_set) for g in g_profiles)
    d_ue_list: Tuple[DUserEquipment] = tuple(DUserEquipment(d.request_data_rate, d.candidate_set) for d in d_profiles)

    for index, e_profile in enumerate(e_profiles):
        e_ue_list[index].register_nb(e_nb, e_profile.distance)
    for index, g_profile in enumerate(g_profiles):
        g_ue_list[index].register_nb(g_nb, g_profile.distance)
    for index, d_profile in enumerate(d_profiles):
        d_ue_list[index].register_nb(e_nb, d_profile.distance_enb)
        d_ue_list[index].register_nb(g_nb, d_profile.distance)

    # tmp: use first (smallest) numerology in candidate set
    for g_ue in g_ue_list:
        g_ue.numerology_in_use = g_ue.candidate_set[0]
    for d_ue in d_ue_list:
        d_ue.numerology_in_use = d_ue.candidate_set[0]

    # noinspection PyTypeChecker
    # TODO type checking warning
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
    d_ue_list_allocated, d_ue_list_unallocated = cluster_unallocated_ue(d_ue_list)

    if visualize_the_algo is True:
        with open(visualization_file_path, "wb") as file_of_frame_and_ue:
            pickle.dump([g_nb.frame, e_nb.frame,
                        {"allocated": g_ue_list_allocated, "unallocated": g_ue_list_unallocated},
                        {"allocated": d_ue_list_allocated, "unallocated": d_ue_list_unallocated},
                        {"allocated": e_ue_list_allocated, "unallocated": e_ue_list_unallocated}], file_of_frame_and_ue)
