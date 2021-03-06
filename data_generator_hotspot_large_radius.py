import os
import pickle
import random
from typing import Dict, Tuple

from src.channel_model.sinr import ChannelModel
from src.resource_allocation.ds.cochannel import cochannel
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.resource_allocation.ds.noma import setup_noma
from src.resource_allocation.ds.util_enum import LTEResourceBlock, Numerology, UEType
from src.resource_allocation.ds.util_type import Coordinate
from src.simulation.data.util_type import HotSpot, UECoordinate, UEProfiles

if __name__ == '__main__':
    times: int = 100
    max_layer: int = 1
    data_file_path: str = 'hotspot_large_radius'

    output_file_path: str = f'src/simulation/data/{data_file_path}/{str(max_layer)}layer'
    if not os.path.exists(output_file_path):
        os.makedirs(output_file_path)

    for i in range(times):
        EUE_COUNT = GUE_COUNT = DUE_COUNT = 300

        e_nb: ENodeB = ENodeB(coordinate=Coordinate(0.0, 0.0), radius=1)
        g_nb: GNodeB = GNodeB(coordinate=Coordinate(0.8, 0.0), radius=0.5, frame_max_layer=max_layer)
        setup_noma([g_nb])
        cochannel_index: Dict = cochannel(e_nb, g_nb)
        channel_model: ChannelModel = ChannelModel(cochannel_index)

        # sample code to generate random profiles (the last tuple `distance_range.e_random` ONLY exists in dUE)
        sec_to_frame: int = 1000 // (e_nb.frame.frame_time // 8)
        qos_lower_bound_bps: int = 16_000  # QoS range: 16,000-512,000 bps
        qos_higher_bound_bps: int = 512_000

        e_profiles: UEProfiles = UEProfiles(
            EUE_COUNT,
            tuple(random.randrange(qos_lower_bound_bps // sec_to_frame, qos_higher_bound_bps // sec_to_frame + 1,
                                   10_000 // sec_to_frame) for _ in
                  range(EUE_COUNT)),
            LTEResourceBlock.gen_candidate_set() * EUE_COUNT,  # dummy (unused)
            UECoordinate(UEType.E, EUE_COUNT, e_nb, g_nb, (
                HotSpot(Coordinate(-0.15, 0.0), 0.15, 75),
                HotSpot(Coordinate(-0.45, 0.0), 0.15, 75),
                HotSpot(Coordinate(-0.75, 0.0), 0.15, 75))).generate()
        )

        g_profiles: UEProfiles = UEProfiles(
            GUE_COUNT,
            tuple(random.randrange(qos_lower_bound_bps // sec_to_frame, qos_higher_bound_bps // sec_to_frame + 1,
                                   10_000 // sec_to_frame) for _ in
                  range(GUE_COUNT)),
            tuple(Numerology.gen_candidate_set(random_pick=True) for _ in range(GUE_COUNT)),
            UECoordinate(UEType.G, GUE_COUNT, e_nb, g_nb).generate()
        )

        d_profiles: UEProfiles = UEProfiles(
            DUE_COUNT,
            tuple(random.randrange(qos_lower_bound_bps // sec_to_frame, qos_higher_bound_bps // sec_to_frame + 1,
                                   10_000 // sec_to_frame) for _ in
                  range(DUE_COUNT)),
            tuple(Numerology.gen_candidate_set(random_pick=True) for _ in range(DUE_COUNT)),
            UECoordinate(UEType.D, DUE_COUNT, e_nb, g_nb, (
                HotSpot(Coordinate(0.46, 0.0), 0.15, 100),)).generate()
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

        with open(os.path.join(output_file_path, str(i) + '.P'), "wb") as file_of_frame_and_ue:
            pickle.dump([g_nb, e_nb, cochannel_index, channel_model, g_ue_list, d_ue_list, e_ue_list], file_of_frame_and_ue)
