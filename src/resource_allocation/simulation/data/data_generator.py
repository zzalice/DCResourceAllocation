import dataclasses
import pickle
import random
from pathlib import Path
from typing import Dict, Tuple

from src.resource_allocation.ds.cochannel import cochannel
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.resource_allocation.ds.util_enum import LTEResourceBlock, Numerology, UEType
from src.resource_allocation.ds.util_type import CandidateSet, Coordinate


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
    # TODO: channel_model too
    EUE_COUNT = GUE_COUNT = DUE_COUNT = 300

    e_nb: ENodeB = ENodeB(coordinate=Coordinate(0.0, 0.0), radius=0.5)
    g_nb: GNodeB = GNodeB(coordinate=Coordinate(0.4, 0.0), radius=0.1)
    cochannel_index: Dict = cochannel(e_nb, g_nb)

    # sample code to generate random profiles (the last tuple `distance_range.e_random` ONLY exists in dUE)
    sec_to_frame: int = 1000 // (e_nb.frame.frame_time // 16)
    qos_lower_bound_bps: int = 100_000  # QoS range: 100,000-3,000,000 bps
    qos_higher_bound_bps: int = 3_000_000

    e_profiles: UEProfiles = UEProfiles(
        EUE_COUNT,
        tuple(random.randrange(qos_lower_bound_bps // sec_to_frame, qos_higher_bound_bps // sec_to_frame + 1, 10_000 // sec_to_frame) for _ in
              range(EUE_COUNT)),
        LTEResourceBlock.gen_candidate_set() * EUE_COUNT,  # dummy (unused)
        tuple(Coordinate.random_gen_coordinate(UEType.E, e_nb, g_nb) for _ in range(EUE_COUNT))
    )

    g_profiles: UEProfiles = UEProfiles(
        GUE_COUNT,
        tuple(random.randrange(qos_lower_bound_bps // sec_to_frame, qos_higher_bound_bps // sec_to_frame + 1, 10_000 // sec_to_frame) for _ in
              range(GUE_COUNT)),
        tuple(Numerology.gen_candidate_set(random_pick=True) for _ in range(GUE_COUNT)),
        tuple(Coordinate.random_gen_coordinate(UEType.G, e_nb, g_nb) for _ in range(GUE_COUNT))
    )

    d_profiles: UEProfiles = UEProfiles(
        DUE_COUNT,
        tuple(random.randrange(qos_lower_bound_bps // sec_to_frame, qos_higher_bound_bps // sec_to_frame + 1, 10_000 // sec_to_frame) for _ in
              range(DUE_COUNT)),
        tuple(Numerology.gen_candidate_set(random_pick=True) for _ in range(DUE_COUNT)),
        tuple(Coordinate.random_gen_coordinate(UEType.D, e_nb, g_nb) for _ in range(DUE_COUNT))
    )

    e_ue_list: Tuple[EUserEquipment] = tuple(
        EUserEquipment(e.request_data_rate, e.candidate_set, e.coordinate) for e in e_profiles)
    g_ue_list: Tuple[GUserEquipment] = tuple(
        GUserEquipment(g.request_data_rate, g.candidate_set, g.coordinate) for g in g_profiles)
    d_ue_list: Tuple[DUserEquipment] = tuple(
        DUserEquipment(d.request_data_rate, d.candidate_set, d.coordinate) for d in d_profiles)

    # noinspection PyTypeChecker
    for ue in (e_ue_list + g_ue_list + d_ue_list):
        ue.register_nb(e_nb, g_nb)

    # tmp: use last (lowest latency) numerology in candidate set
    for g_ue in g_ue_list:
        g_ue.numerology_in_use = g_ue.candidate_set[-1]
    for d_ue in d_ue_list:
        d_ue.numerology_in_use = d_ue.candidate_set[-1]

    with open(Path(__file__).stem + ".P", "wb") as file_of_frame_and_ue:
        pickle.dump([g_nb, e_nb, cochannel_index, g_ue_list, d_ue_list, e_ue_list], file_of_frame_and_ue)
