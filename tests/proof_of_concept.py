import dataclasses
from typing import Tuple

from src.resource_allocation.ds.eutran import ENodeB
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.resource_allocation.ds.ue import UserEquipment
from src.resource_allocation.ds.util_enum import Numerology
from src.resource_allocation.ds.util_type import CandidateSet, DistanceRange


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
    GUE_COUNT = DUE_COUNT = 10
    NB_DISTANCE: float = 1.0

    e_nb: ENodeB = ENodeB()  # radius: 2.0, frame_freq: 50, frame_time: 160, frame_max_layer: 1
    g_nb: GNodeB = GNodeB()  # radius: 1.0, frame_freq: 100, frame_max_layer: 3
    distance_range: DistanceRange = UserEquipment.calc_distance_range(e_nb, g_nb, NB_DISTANCE)

    """
    # # sample code to generate random profiles (the last tuple `distance_range.e_random` ONLY exists in dUE)
    # import random
    # d_profile: DUEProfiles = DUEProfiles(
    #     DUE_COUNT,
    #     tuple(random.randrange(1_200, 3_000_000 + 1, 1_200) for _ in range(DUE_COUNT)),
    #     tuple(Numerology.gen_candidate_set(random_pick=True) for _ in range(DUE_COUNT)),
    #     tuple(distance_range.g_random for _ in range(DUE_COUNT)),
    #     tuple(distance_range.e_random for _ in range(DUE_COUNT))
    # )
    """

    # the recorded random data for POC
    g_profiles: UEProfiles = UEProfiles(
        GUE_COUNT,
        (2959200, 1178400, 2845200, 115200, 2173200, 982800, 1273200, 87600, 2581200, 40800),
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
        (2535600, 308400, 462000, 1376400, 2979600, 642000, 1581600, 2162400, 2506800, 1676400),
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

    g_ue_list: Tuple[GUserEquipment] = tuple(GUserEquipment(g.request_data_rate, g.candidate_set) for g in g_profiles)
    d_ue_list: Tuple[DUserEquipment] = tuple(DUserEquipment(d.request_data_rate, d.candidate_set) for d in d_profiles)

    for index, g_profile in enumerate(g_profiles):
        g_ue_list[index].register_nb(g_nb, g_profile.distance)
    for index, d_profile in enumerate(d_profiles):
        d_ue_list[index].register_nb(e_nb, d_profile.distance_enb)
        d_ue_list[index].register_nb(g_nb, d_profile.distance)
