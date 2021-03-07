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
from src.simulation.data.util_type import UECoordinate, UEProfiles


class DataGenerator:
    def __init__(self, times: int, output_file_path: str,
                 qos_range: Tuple[int, int],
                 eue_num: int, eue_hotspots: Tuple[Tuple[float, float, float, int]],
                 gue_num: int, gue_hotspots: Tuple[Tuple[float, float, float, int]],
                 due_num: int, due_hotspots: Tuple[Tuple[float, float, float, int]],
                 enb_coordinate: Tuple[int, int], enb_radius: float, enb_tx_power: int, enb_freq: int, enb_time: int,
                 gnb_coordinate: Tuple[int, int], gnb_radius: float, gnb_tx_power: int, gnb_freq: int, gnb_time: int,
                 gnb_layer: int,
                 cochannel_bandwidth: int):
        assert times > 0
        self.times: int = times
        self.output_file_path: str = f'{os.path.dirname(__file__)}/{output_file_path}'
        assert qos_range[0] <= qos_range[1]
        self.qos_range: Tuple[int, int] = qos_range
        assert eue_num >= 0 and gue_num >= 0 and due_num >= 0
        self.eue_num: int = eue_num
        self.eue_hotspots: Tuple[Tuple[float, float, float, int]] = eue_hotspots
        self.gue_num: int = gue_num
        self.gue_hotspots: Tuple[Tuple[float, float, float, int]] = gue_hotspots
        self.due_num: int = due_num
        self.due_hotspots: Tuple[Tuple[float, float, float, int]] = due_hotspots
        self.enb_coordinate: Tuple[int, int] = enb_coordinate
        self.enb_radius: float = enb_radius
        self.enb_tx_power: int = enb_tx_power
        self.enb_freq: int = enb_freq
        assert enb_time == gnb_time
        self.enb_time: int = enb_time
        self.gnb_coordinate: Tuple[int, int] = gnb_coordinate
        self.gnb_radius: float = gnb_radius
        self.gnb_tx_power: int = gnb_tx_power
        self.gnb_freq: int = gnb_freq
        self.gnb_time: int = gnb_time
        assert gnb_layer > 0
        self.gnb_layer: int = gnb_layer
        assert cochannel_bandwidth >= 0
        self.cochannel_bandwidth: int = cochannel_bandwidth

    def generate_data(self):
        self.gen_txt_parameter()
        for i in range(self.times):
            e_nb: ENodeB = ENodeB(coordinate=Coordinate(self.enb_coordinate[0], self.enb_coordinate[1]),
                                  radius=self.enb_radius, power_tx=self.enb_tx_power, frame_freq=self.enb_freq,
                                  frame_time=self.enb_time)
            g_nb: GNodeB = GNodeB(coordinate=Coordinate(self.gnb_coordinate[0], self.gnb_coordinate[1]),
                                  radius=self.gnb_radius, power_tx=self.gnb_tx_power, frame_freq=self.gnb_freq,
                                  frame_time=self.gnb_time, frame_max_layer=self.gnb_layer)
            setup_noma([g_nb])
            cochannel_index: Dict = cochannel(e_nb, g_nb, cochannel_bandwidth=self.cochannel_bandwidth)
            channel_model: ChannelModel = ChannelModel(cochannel_index)

            sec_to_frame: int = 1000 // (e_nb.frame.frame_time // 8)
            qos_lower_bound_bps: int = self.qos_range[0]  # QoS range: 16,000-512,000 bps
            qos_higher_bound_bps: int = self.qos_range[1]

            e_profiles: UEProfiles = UEProfiles(
                self.eue_num,
                tuple(random.randrange(qos_lower_bound_bps // sec_to_frame, qos_higher_bound_bps // sec_to_frame + 1,
                                       10_000 // sec_to_frame) for _ in range(self.eue_num)),
                LTEResourceBlock.gen_candidate_set() * self.eue_num,  # dummy (unused)
                UECoordinate(UEType.E, self.eue_num, e_nb, g_nb, self.eue_hotspots).generate()
            )

            g_profiles: UEProfiles = UEProfiles(
                self.gue_num,
                tuple(random.randrange(qos_lower_bound_bps // sec_to_frame, qos_higher_bound_bps // sec_to_frame + 1,
                                       10_000 // sec_to_frame) for _ in
                      range(self.gue_num)),
                tuple(Numerology.gen_candidate_set(random_pick=True) for _ in range(self.gue_num)),
                UECoordinate(UEType.G, self.gue_num, e_nb, g_nb, self.gue_hotspots).generate()
            )

            d_profiles: UEProfiles = UEProfiles(
                self.due_num,
                tuple(random.randrange(qos_lower_bound_bps // sec_to_frame, qos_higher_bound_bps // sec_to_frame + 1,
                                       10_000 // sec_to_frame) for _ in
                      range(self.due_num)),
                tuple(Numerology.gen_candidate_set(random_pick=True) for _ in range(self.due_num)),
                UECoordinate(UEType.D, self.due_num, e_nb, g_nb, self.due_hotspots).generate()
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

            with open(f'{self.output_file_path}/{str(i)}.P', "wb") as file_of_frame_and_ue:
                pickle.dump([g_nb, e_nb, cochannel_index, channel_model, g_ue_list, d_ue_list, e_ue_list],
                            file_of_frame_and_ue)

    def gen_txt_parameter(self):
        with open(f'{self.output_file_path}/parameter.txt', 'w') as file:
            file.write(
                f'QoS range(in bps): {self.qos_range}\n' +
                f'dUE number: {self.due_num}\thot spots: {self.due_hotspots}\n' +
                f'gUE number: {self.gue_num}\thot spots: {self.gue_hotspots}\n' +
                f'eUE number: {self.eue_num}\thot spots: {self.eue_hotspots}\n\n' +

                f'gNB-------\n' +
                f'max layer: {self.gnb_layer}\n' +
                f'radius: {self.gnb_radius}\n' +
                f'coordinate: {self.gnb_coordinate}\n' +
                f'frame, freq(in BU): {self.gnb_freq}\n' +
                f'frame, time(in BU): {self.gnb_time}\n' +
                f'tx power: {self.gnb_tx_power}\n\n' +

                f'eNB-------\n' +
                f'radius: {self.enb_radius}\n' +
                f'coordinate: {self.enb_coordinate}\n' +
                f'frame, freq(in BU): {self.enb_freq}\n' +
                f'frame, time(in BU): {self.enb_time}\n' +
                f'tx power: {self.enb_tx_power}\n\n' +

                f'co-channel BW(in BU): {self.cochannel_bandwidth}\n')
