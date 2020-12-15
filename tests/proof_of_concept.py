import dataclasses
import pickle
from datetime import datetime
from typing import Tuple

from src.channel_model.sinr import ChannelModel
from src.resource_allocation.algo.assistance import cluster_unallocated_ue
from src.resource_allocation.algo.phase1 import Phase1
from src.resource_allocation.algo.phase2 import Phase2
from src.resource_allocation.algo.phase3 import Phase3
from src.resource_allocation.ds.cochannel import cochannel
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.resource_allocation.ds.ue import UserEquipment
from src.resource_allocation.ds.util_enum import LTEPhysicalResourceBlock, Numerology, UEType
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
    visualization_file_path = "../utils/frame_visualizer/vis_" + datetime.today().strftime('%Y%m%d')

    e_nb: ENodeB = ENodeB(coordinate=Coordinate(0.0, 0.0), radius=0.5)
    g_nb: GNodeB = GNodeB(coordinate=Coordinate(0.4, 0.0), radius=0.1)
    total_bandwidth: int = cochannel(e_nb, g_nb)

    """
    # sample code to generate random profiles (the last tuple `distance_range.e_random` ONLY exists in dUE)
    import random
    sec_to_frame: int = 1000 // (e_nb.frame.frame_time // 16)
    e_profiles: UEProfiles = UEProfiles(
        EUE_COUNT,
        tuple(random.randrange(100_000 // sec_to_frame, 3_000_000 // sec_to_frame + 1, 10_000 // sec_to_frame) for _ in
              range(EUE_COUNT)),
        tuple(Numerology.gen_candidate_set(random_pick=True) for _ in range(EUE_COUNT)),
        tuple(Coordinate.random_gen_coordinate(UEType.E, e_nb, g_nb) for _ in range(EUE_COUNT))
    )

    g_profiles: UEProfiles = UEProfiles(
        GUE_COUNT,
        tuple(random.randrange(100_000 // sec_to_frame, 3_000_000 // sec_to_frame + 1, 10_000 // sec_to_frame) for _ in
              range(GUE_COUNT)),
        tuple(Numerology.gen_candidate_set(random_pick=True) for _ in range(GUE_COUNT)),
        tuple(Coordinate.random_gen_coordinate(UEType.G, e_nb, g_nb) for _ in range(GUE_COUNT))
    )

    d_profiles: UEProfiles = UEProfiles(
        DUE_COUNT,
        tuple(random.randrange(100_000 // sec_to_frame, 3_000_000 // sec_to_frame + 1, 10_000 // sec_to_frame) for _ in
              range(DUE_COUNT)),
        tuple(Numerology.gen_candidate_set(random_pick=True) for _ in range(DUE_COUNT)),
        tuple(Coordinate.random_gen_coordinate(UEType.D, e_nb, g_nb) for _ in range(DUE_COUNT))
    )
    """

    # the recorded random data for POC
    e_profiles: UEProfiles = UEProfiles(
        EUE_COUNT,
        (1800, 600, 1790, 800, 2520, 360, 1430, 220, 890, 730),
        LTEPhysicalResourceBlock.gen_candidate_set() * EUE_COUNT,  # dummy (unused)
        (Coordinate(x=-0.29610054426949417, y=-0.3623702725939647),
         Coordinate(x=-0.1645602743367075, y=-0.39874429401931677),
         Coordinate(x=-0.4865763070064515, y=-0.05278531088664759),
         Coordinate(x=-0.35771222995013163, y=-0.16640874090420957),
         Coordinate(x=-0.46574854383261843, y=0.0792304624990183),
         Coordinate(x=-0.33044775096220125, y=-0.12931218469829836),
         Coordinate(x=-0.25163254489635334, y=-0.17898287986750266),
         Coordinate(x=-0.20541176426579988, y=0.24327444866369202),
         Coordinate(x=-0.12925435675223962, y=0.08518355229612778),
         Coordinate(x=0.3181355504372627, y=0.3034799359148609)))

    g_profiles: UEProfiles = UEProfiles(
        GUE_COUNT,
        (1370, 2150, 280, 1870, 2710, 2630, 2650, 1630, 1080, 1930),
        ((Numerology.N1, Numerology.N2, Numerology.N4),
         (Numerology.N2, Numerology.N3, Numerology.N4),
         (Numerology.N0, Numerology.N1, Numerology.N2, Numerology.N3, Numerology.N4),
         (Numerology.N0, Numerology.N1, Numerology.N2, Numerology.N3, Numerology.N4),
         (Numerology.N0, Numerology.N2, Numerology.N4),
         (Numerology.N0, Numerology.N2, Numerology.N3, Numerology.N4),
         (Numerology.N1, Numerology.N2, Numerology.N3),
         (Numerology.N0, Numerology.N1, Numerology.N2, Numerology.N3, Numerology.N4),
         (Numerology.N1, Numerology.N4),
         (Numerology.N0, Numerology.N2)),
        (Coordinate(x=0.39442468781514345, y=0.07893335787534583),
         Coordinate(x=0.31291174581576614, y=0.04376320896919416),
         Coordinate(x=0.4605290512969942, y=-0.06679764687010638),
         Coordinate(x=0.4345620732463405, y=-0.021367100583666587),
         Coordinate(x=0.4007353530424709, y=0.07208298106858023),
         Coordinate(x=0.32558124905729474, y=-0.049071581201010545),
         Coordinate(x=0.49882511212018393, y=0.015248490102904052),
         Coordinate(x=0.47345986377159344, y=-0.0676071257749736),
         Coordinate(x=0.324713152388773, y=0.061494024930919225),
         Coordinate(x=0.45110251155889425, y=-0.026972583602258356)))

    d_profiles: UEProfiles = UEProfiles(
        EUE_COUNT,
        (2990, 2230, 2120, 1130, 1570, 2890, 1410, 1580, 1910, 2590),
        ((Numerology.N1, Numerology.N2, Numerology.N4),
         (Numerology.N4,),
         (Numerology.N0, Numerology.N1, Numerology.N2, Numerology.N3, Numerology.N4),
         (Numerology.N0, Numerology.N1, Numerology.N2, Numerology.N3, Numerology.N4),
         (Numerology.N0, Numerology.N1, Numerology.N2, Numerology.N3, Numerology.N4),
         (Numerology.N0, Numerology.N1, Numerology.N2, Numerology.N3, Numerology.N4),
         (Numerology.N1, Numerology.N2),
         (Numerology.N3,),
         (Numerology.N0, Numerology.N1, Numerology.N2, Numerology.N3, Numerology.N4),
         (Numerology.N1, Numerology.N2)),
        (Coordinate(x=0.32476433491237766, y=-0.05834765134288816),
         Coordinate(x=0.47660027780653613, y=0.023282613187806278),
         Coordinate(x=0.38015351283451504, y=0.06612644145248509),
         Coordinate(x=0.4802380312986635, y=0.048239653541915034),
         Coordinate(x=0.4096463664664044, y=0.05017068154933363),
         Coordinate(x=0.3803402492112279, y=-0.08519935531736675),
         Coordinate(x=0.40239269600556105, y=0.08438025945597755),
         Coordinate(x=0.3795875474946112, y=-0.046407950055602165),
         Coordinate(x=0.479156248719507, y=-0.04850929587869729),
         Coordinate(x=0.43644972223648637, y=0.06110838172570382)))

    e_ue_list: Tuple[EUserEquipment] = tuple(
        EUserEquipment(e.request_data_rate, e.candidate_set, e.coordinate) for e in e_profiles)
    g_ue_list: Tuple[GUserEquipment] = tuple(
        GUserEquipment(g.request_data_rate, g.candidate_set, g.coordinate) for g in g_profiles)
    d_ue_list: Tuple[DUserEquipment] = tuple(
        DUserEquipment(d.request_data_rate, d.candidate_set, d.coordinate) for d in d_profiles)

    # noinspection PyTypeChecker
    for ue in (e_ue_list + g_ue_list + d_ue_list):
        ue.register_nb(e_nb, g_nb)

    # tmp: use first (smallest) numerology in candidate set
    for g_ue in g_ue_list:
        g_ue.numerology_in_use = g_ue.candidate_set[0]
    for d_ue in d_ue_list:
        d_ue.numerology_in_use = d_ue.candidate_set[0]

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
    d_ue_list_allocated, d_ue_list_unallocated = cluster_unallocated_ue(d_ue_list)

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
