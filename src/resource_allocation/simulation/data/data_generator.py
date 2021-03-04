import dataclasses
import pickle
import random
from pathlib import Path
from typing import Dict, Tuple

from src.channel_model.sinr import ChannelModel
from src.resource_allocation.ds.cochannel import cochannel
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.resource_allocation.ds.noma import setup_noma
from src.resource_allocation.ds.util_enum import LTEResourceBlock, Numerology, UEType
from src.resource_allocation.ds.util_type import CandidateSet, Coordinate
from src.resource_allocation.simulation.data.util_type import HotSpot, UECoordinate


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
    EUE_COUNT = GUE_COUNT = DUE_COUNT = 300

    e_nb: ENodeB = ENodeB(coordinate=Coordinate(0.0, 0.0), radius=0.5)
    g_nb: GNodeB = GNodeB(coordinate=Coordinate(0.5, 0.0), radius=0.1)
    setup_noma([g_nb])
    cochannel_index: Dict = cochannel(e_nb, g_nb)
    channel_model: ChannelModel = ChannelModel(cochannel_index)

    # sample code to generate random profiles (the last tuple `distance_range.e_random` ONLY exists in dUE)
    sec_to_frame: int = 1000 // (e_nb.frame.frame_time // 8)
    qos_lower_bound_bps: int = 16_000  # QoS range: 16,000-512,000 bps
    qos_higher_bound_bps: int = 512_000

    e_profiles: UEProfiles = UEProfiles(
        EUE_COUNT,
        tuple(random.randrange(qos_lower_bound_bps // sec_to_frame, qos_higher_bound_bps // sec_to_frame + 1, 10_000 // sec_to_frame) for _ in
              range(EUE_COUNT)),
        LTEResourceBlock.gen_candidate_set() * EUE_COUNT,  # dummy (unused)
        UECoordinate(UEType.E, EUE_COUNT, e_nb, g_nb, (
            HotSpot(Coordinate(-0.1, 0.0), 0.05, 100),
            HotSpot(Coordinate(-0.25, 0.0), 0.05, 100),
            HotSpot(Coordinate(-0.4, 0.0), 0.05, 100))).generate()
    )

    g_profiles: UEProfiles = UEProfiles(
        GUE_COUNT,
        tuple(random.randrange(qos_lower_bound_bps // sec_to_frame, qos_higher_bound_bps // sec_to_frame + 1, 10_000 // sec_to_frame) for _ in
              range(GUE_COUNT)),
        tuple(Numerology.gen_candidate_set(random_pick=True) for _ in range(GUE_COUNT)),
        UECoordinate(UEType.G, GUE_COUNT, e_nb, g_nb, (
            HotSpot(Coordinate(0.55, 0.0), 0.04, 100),
            HotSpot(Coordinate(0.55, 0.005), 0.03, 100))).generate()
    )

    d_profiles: UEProfiles = UEProfiles(
        DUE_COUNT,
        tuple(random.randrange(qos_lower_bound_bps // sec_to_frame, qos_higher_bound_bps // sec_to_frame + 1, 10_000 // sec_to_frame) for _ in
              range(DUE_COUNT)),
        tuple(Numerology.gen_candidate_set(random_pick=True) for _ in range(DUE_COUNT)),
        UECoordinate(UEType.D, DUE_COUNT, e_nb, g_nb).generate()
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
        pickle.dump([g_nb, e_nb, cochannel_index, channel_model, g_ue_list, d_ue_list, e_ue_list], file_of_frame_and_ue)
