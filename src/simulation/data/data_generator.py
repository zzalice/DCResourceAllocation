import os
import pickle
import random
from typing import Dict, Tuple

from src.channel_model.sinr import ChannelModel
from src.resource_allocation.ds.cochannel import cochannel
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.resource_allocation.ds.noma import setup_noma
from src.resource_allocation.ds.util_enum import LTEResourceBlock, Numerology
from src.resource_allocation.ds.util_type import CircularRegion
from src.simulation.data.deployment import Deploy
from src.simulation.data.util_type import HotSpot, UEProfiles


class DataGenerator:
    def __init__(self, iteration: int, output_file_path: str,
                 total_num_ue: int,
                 eue_qos_range: Tuple[int, int], gue_qos_range: Tuple[int, int], due_qos_range: Tuple[int, int],
                 enb_coordinate: Tuple[int, int], enb_radius: float, enb_tx_power: int, enb_freq: int, enb_time: int,
                 gnb_coordinate: Tuple[int, int], gnb_radius: float, gnb_tx_power: int, gnb_freq: int, gnb_time: int,
                 gnb_layer: int, inr_discount: float,
                 deploy_type: int,
                 edge_radius: float, edge_ue: float,
                 hot_spots: Tuple[Tuple[float, float, float, int], ...],
                 dc_proportion: float,
                 cochannel_bandwidth: int, worsen_threshold: int):
        assert iteration > 0
        self.iteration: int = iteration
        assert total_num_ue > 0
        self.total_num_ue: int = total_num_ue
        self.eue_num: int = 0
        self.gue_num: int = 0
        self.due_num: int = 0
        assert eue_qos_range[0] <= eue_qos_range[1]
        self.eue_qos_range: Tuple[int, int] = eue_qos_range  # bps
        assert gue_qos_range[0] <= gue_qos_range[1]
        self.gue_qos_range: Tuple[int, int] = gue_qos_range
        assert due_qos_range[0] <= due_qos_range[1]
        self.due_qos_range: Tuple[int, int] = due_qos_range

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
        assert 0.0 < inr_discount <= 1.0
        self.inr_discount: float = inr_discount

        self.deploy_type: int = deploy_type
        self.cell_edge_radius_proportion: float = edge_radius
        self.edge_ue_proportion: float = edge_ue
        self.hotspots: Tuple[HotSpot, ...] = tuple(HotSpot(hp[0], hp[1], hp[2], hp[3]) for hp in hot_spots)
        self.dc_proportion: float = dc_proportion

        assert cochannel_bandwidth >= 0
        self.cochannel_bandwidth: int = cochannel_bandwidth
        self.worsen_threshold: int = worsen_threshold

        self.output_file_path: str = f'{os.path.dirname(__file__)}/{output_file_path}'
        if not os.path.exists(self.output_file_path):
            os.makedirs(self.output_file_path)

    def generate_data(self):
        for i in range(self.iteration):
            # Set up BSs
            e_nb: ENodeB = ENodeB(
                region=CircularRegion(x=self.enb_coordinate[0], y=self.enb_coordinate[1], radius=self.enb_radius),
                power_tx=self.enb_tx_power, frame_freq=self.enb_freq, frame_time=self.enb_time)
            g_nb: GNodeB = GNodeB(
                region=CircularRegion(x=self.gnb_coordinate[0], y=self.gnb_coordinate[1], radius=self.gnb_radius),
                power_tx=self.gnb_tx_power, frame_freq=self.gnb_freq, frame_time=self.gnb_time,
                frame_max_layer=self.gnb_layer)
            setup_noma([g_nb])
            cochannel_index: Dict = cochannel(e_nb, g_nb, cochannel_bandwidth=self.cochannel_bandwidth)
            channel_model: ChannelModel = ChannelModel(cochannel_index)

            sec_to_frame: int = 1000 // (e_nb.frame.frame_time // 8)
            worsen_threshold: float = self.worsen_threshold / sec_to_frame  # bit per frame

            # Set up UE
            coordinates_sc, coordinates_dc = self.deploy_ue((e_nb.region, g_nb.region))
            self.eue_num: int = len(coordinates_sc[0])
            self.gue_num: int = len(coordinates_sc[1])
            self.due_num: int = len(coordinates_dc)
            e_profiles: UEProfiles = UEProfiles(
                self.eue_num,
                tuple(random.randrange(self.eue_qos_range[0] // sec_to_frame, self.eue_qos_range[1] // sec_to_frame + 1,
                                       10_000 // sec_to_frame) for _ in range(self.eue_num)),
                LTEResourceBlock.gen_candidate_set() * self.eue_num,  # dummy (unused)
                coordinates_sc[0]
            )
            g_profiles: UEProfiles = UEProfiles(
                self.gue_num,
                tuple(random.randrange(self.gue_qos_range[0] // sec_to_frame, self.gue_qos_range[1] // sec_to_frame + 1,
                                       10_000 // sec_to_frame) for _ in range(self.gue_num)),
                tuple(Numerology.gen_candidate_set(random_pick=True) for _ in range(self.gue_num)),
                coordinates_sc[1]
            )
            d_profiles: UEProfiles = UEProfiles(
                self.due_num,
                tuple(random.randrange(self.due_qos_range[0] // sec_to_frame, self.due_qos_range[1] // sec_to_frame + 1,
                                       10_000 // sec_to_frame) for _ in range(self.due_num)),
                tuple(Numerology.gen_candidate_set(random_pick=True) for _ in range(self.due_num)),
                coordinates_dc
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

            # Output
            with open(f'{self.output_file_path}/{str(i)}.P', "wb") as file_of_frame_and_ue:
                pickle.dump(
                    [g_nb, e_nb, channel_model,
                     g_ue_list, d_ue_list, e_ue_list, self.gue_qos_range, self.eue_qos_range,
                     self.inr_discount, worsen_threshold],
                    file_of_frame_and_ue)

        self.gen_txt_parameter()

    def deploy_ue(self, areas: Tuple[CircularRegion, ...]):
        assert areas, 'No input areas.'
        assert self.total_num_ue > 0, 'No UE to deploy.'
        if self.deploy_type == 0:
            return Deploy.random(self.total_num_ue, areas)
        elif self.deploy_type == 1:
            assert 0.0 < self.cell_edge_radius_proportion < 1.0, 'The edge area is too small/large.'
            assert 0.0 < self.edge_ue_proportion < 1.0, 'The UE in the edge is too much/little.'
            return Deploy.cell_edge(self.total_num_ue, areas,
                                    radius_proportion_of_cell_edge=self.cell_edge_radius_proportion,
                                    proportion_of_ue_in_edge=self.edge_ue_proportion)
        elif self.deploy_type == 2:
            assert self.hotspots, 'No hotspot.'
            return Deploy.hotspots(self.total_num_ue, areas, self.hotspots)
        elif self.deploy_type == 3:
            assert 0.0 <= self.dc_proportion <= 1.0, 'Proportion out of range.'
            return Deploy.dc_proportion(self.total_num_ue, areas, self.dc_proportion)

    def gen_txt_parameter(self):
        information: str = ''
        information += f'total number of UE: {self.total_num_ue}\n'
        information += f'dUE number: {self.due_num}\tQoS(in bps): {self.due_qos_range}\n'
        information += f'gUE number: {self.gue_num}\tQoS(in bps): {self.gue_qos_range}\n'
        information += f'eUE number: {self.eue_num}\tQoS(in bps): {self.eue_qos_range}\n\n'

        information += f'gNB-------\n'
        information += f'max layer: {self.gnb_layer}\n'
        information += f'frame, freq(in BU): {self.gnb_freq}\n'
        information += f'frame, time(in BU): {self.gnb_time}\n'
        information += f'radius: {self.gnb_radius}\n'
        information += f'coordinate: {self.gnb_coordinate}\n'
        information += f'tx power: {self.gnb_tx_power}\n'
        information += f'inr discount: {self.inr_discount}\n\n'

        information += f'eNB-------\n'
        information += f'frame, freq(in BU): {self.enb_freq}\n'
        information += f'frame, time(in BU): {self.enb_time}\n'
        information += f'radius: {self.enb_radius}\n'
        information += f'coordinate: {self.enb_coordinate}\n'
        information += f'tx power: {self.enb_tx_power}\n\n'

        information += f'deploy type: {self.deploy_type}\n'  # 0: random, 1: cell edge, 2: hot spot, 3: more or less dUE
        if self.deploy_type == 1:
            information += f'cell edge radius proportion: {self.cell_edge_radius_proportion}\t'
            information += f'edge_ue_proportion: {self.edge_ue_proportion}\n'
        elif self.deploy_type == 2:
            information += f'hot spots: {self.hotspots}\n'
        elif self.deploy_type == 3:
            information += f'DC proportion: {self.dc_proportion}\n'
        information += '\n'

        information += f'co-channel BW(in BU): {self.cochannel_bandwidth}\n'
        information += f'worsen_threshold(bps): {self.worsen_threshold}\n'

        with open(f'{self.output_file_path}/parameter_data.txt', 'w') as file:
            file.write(information)
