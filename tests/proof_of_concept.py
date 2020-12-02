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
from src.resource_allocation.ds.util_enum import LTEPhysicalResourceBlock, Numerology
from src.resource_allocation.ds.util_type import CandidateSet, Coordinate
from src.resource_allocation.ds.zone import Zone, ZoneGroup


@dataclasses.dataclass
class UEProfiles:
    count: int
    request_data_rate_list: Tuple[int, ...]
    candidate_set_list: Tuple[CandidateSet, ...]
    coordinate_list: Tuple[Coordinate, ...]

    def __iter__(self):
        single_data = dataclasses.make_dataclass('UEProfile', (
            ('request_data_rate', int), ('candidate_set', CandidateSet), ('coordinate', Coordinate)))
        for i in range(self.count):
            yield single_data(self.request_data_rate_list[i], self.candidate_set_list[i], self.coordinate_list[i])


if __name__ == '__main__':
    EUE_COUNT = GUE_COUNT = DUE_COUNT = 10

    visualize_the_algo: bool = True
    visualization_file_path = "../utils/frame_visualizer/vis_" + datetime.today().strftime('%Y%m%d') + ".P"

    e_nb: ENodeB = ENodeB(Coordinate(0.0, 0.0))
    g_nb: GNodeB = GNodeB(Coordinate(0.0, 1.0))
    cochannel(e_nb, g_nb)

    """
    # # sample code to generate random profiles (the last tuple `distance_range.e_random` ONLY exists in dUE)
    # import random
    # frame_time: int = g_nb.frame.frame_time // 16
    # d_profile: UEProfiles = UEProfiles(
    #     DUE_COUNT,
    #     tuple(random.randrange(100_000 // frame_time, 3_000_000 // frame_time + 1, 10_000 // frame_time) for _ in
    #           range(DUE_COUNT)),
    #     tuple(Numerology.gen_candidate_set(random_pick=True) for _ in range(DUE_COUNT)),
    #     tuple(Coordinate.random_gen_coordinate(UEType.D, e_nb, g_nb) for _ in range(DUE_COUNT))
    # )
    """

    # TODO: eUE and gUE also need a distance to gNB and eNB respectively
    # the recorded random data for POC
    e_profiles: UEProfiles = UEProfiles(
        EUE_COUNT,
        (188, 2874, 535, 2420, 1876, 195, 1188, 1938, 369, 1502),
        LTEPhysicalResourceBlock.gen_candidate_set() * EUE_COUNT,  # dummy (unused)
        (Coordinate(x=0.27904007662973385, y=-0.9072418949440513),
         Coordinate(x=-0.3391483240699258, y=0.48930798994032465),
         Coordinate(x=-0.9486397914240245, y=0.07767896808797836),
         Coordinate(x=-0.9155037410216382, y=0.26428092968920575),
         Coordinate(x=-0.9407254926164714, y=0.012630089775539699),
         Coordinate(x=-0.8298324505135541, y=0.48022609317655207),
         Coordinate(x=0.6810005113203945, y=-0.3757571685462667),
         Coordinate(x=-0.8540495076040442, y=0.01531854045861003),
         Coordinate(x=-0.6056142622411749, y=0.7760145252364593),
         Coordinate(x=0.13873175803050541, y=-0.14590790079943894))
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
        (Coordinate(x=0.24452366700035255, y=0.5948949369029221),
         Coordinate(x=0.2661107105487832, y=0.44363940060067414),
         Coordinate(x=0.2098354808506795, y=0.30426250825903933),
         Coordinate(x=0.409973928061673, y=1.2014367272001483),
         Coordinate(x=0.7919789847331831, y=1.4757120857991768),
         Coordinate(x=0.44153326797988157, y=0.5413104964173447),
         Coordinate(x=-0.36338936696956803, y=1.3668609167513088),
         Coordinate(x=0.16420259312996777, y=1.6744026127381029),
         Coordinate(x=0.028253076196515625, y=0.5007356989615523),
         Coordinate(x=0.7612334035030806, y=0.42291624133948197))
    )
    d_profiles: UEProfiles = UEProfiles(
        DUE_COUNT,
        (2535, 308, 462, 1376, 2979, 642, 1581, 2162, 2506, 1676),
        ((Numerology.N0, Numerology.N1, Numerology.N2, Numerology.N3, Numerology.N4), (Numerology.N3,),
         (Numerology.N0, Numerology.N1, Numerology.N2, Numerology.N3, Numerology.N4),
         (Numerology.N0, Numerology.N2, Numerology.N3), (Numerology.N0, Numerology.N1, Numerology.N2, Numerology.N4),
         (Numerology.N0, Numerology.N2, Numerology.N3), (Numerology.N2, Numerology.N3, Numerology.N4),
         (Numerology.N1, Numerology.N2), (Numerology.N3,), (Numerology.N1, Numerology.N2, Numerology.N3)),
        (Coordinate(x=-0.17952404175855596, y=0.16714927685897485),
         Coordinate(x=-0.7855257260719444, y=0.566326771728464),
         Coordinate(x=-0.8271904468694042, y=0.513193321813546),
         Coordinate(x=-0.5248486058097599, y=0.7048968514883497),
         Coordinate(x=0.29977631841909314, y=0.26836097320160734),
         Coordinate(x=-0.5878335427909898, y=0.5025164790001936),
         Coordinate(x=-0.39935620740212685, y=0.19936557048711778),
         Coordinate(x=-0.35961342880992486, y=0.7878628043212192),
         Coordinate(x=0.2963560576204325, y=0.04833484625898177),
         Coordinate(x=-0.0887892326101336, y=0.8266906426834533))
    )

    e_ue_list: Tuple[EUserEquipment] = tuple(
        EUserEquipment(e.request_data_rate, e.candidate_set, e.coordinate) for e in e_profiles)
    g_ue_list: Tuple[GUserEquipment] = tuple(
        GUserEquipment(g.request_data_rate, g.candidate_set, g.coordinate) for g in g_profiles)
    d_ue_list: Tuple[DUserEquipment] = tuple(
        DUserEquipment(d.request_data_rate, d.candidate_set, d.coordinate) for d in d_profiles)

    for ue in (e_ue_list + g_ue_list + d_ue_list):
        ue.register_nb(e_nb, g_nb)

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
                         {"allocated": e_ue_list_allocated, "unallocated": e_ue_list_unallocated}],
                        file_of_frame_and_ue)
