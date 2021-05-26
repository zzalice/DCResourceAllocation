import json
from typing import Dict, List, Tuple, Union

from src.channel_model.sinr import ChannelModel
from src.resource_allocation.ds.cochannel import cochannel
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.resource_allocation.ds.noma import setup_noma
from src.resource_allocation.ds.util_enum import LTEResourceBlock, Numerology, UEType
from src.resource_allocation.ds.util_type import CandidateSet, CircularRegion, Coordinate


class DataLoader:
    def run(self, data_set_file_path: str) -> Tuple[
        GNodeB, ENodeB, ChannelModel, Tuple[GUserEquipment, ...], Tuple[DUserEquipment, ...], Tuple[
            EUserEquipment, ...], Tuple[int, int], Tuple[int, int], float, float]:
        """
        Load the json file to create objects.
        :param data_set_file_path: The file path to data parameter.
        :return: g_nb, e_nb, channel_model, g_ue_list, d_ue_list, e_ue_list,
                 gue_qos, eue_qos, inr_discount, worsen_threshold
        """
        assert '.json' in data_set_file_path, 'Input file path error.'
        with open(data_set_file_path, 'r') as file:
            data_parameters = json.load(file)
        e_nb, g_nb = self.new_object_nb(data_parameters['e_nb'], data_parameters['g_nb'])
        channel_model = self.new_object_channel_model(data_parameters['cochannel_bandwidth'], e_nb, g_nb)
        g_ue_list, d_ue_list, e_ue_list = self.new_object_ue(data_parameters['g_ue_list'], data_parameters['d_ue_list'],
                                                             data_parameters['e_ue_list'], e_nb, g_nb)
        worsen_threshold = self.convert_worsen_threshold(data_parameters['worsen_threshold'], e_nb.frame.frame_time)
        return g_nb, e_nb, channel_model, g_ue_list, d_ue_list, e_ue_list, data_parameters[
            'gue_qos_range'], data_parameters['eue_qos_range'], data_parameters['inr_discount'], worsen_threshold

    @staticmethod
    def new_object_nb(para_enb: Dict, para_gnb: Dict) -> Tuple[ENodeB, GNodeB]:
        e_nb: ENodeB = ENodeB(
            region=CircularRegion(x=para_enb['coordinate'][0], y=para_enb['coordinate'][1],
                                  radius=para_enb['radius']),
            power_tx=para_enb['tx_power'],
            frame_freq=para_enb['freq'],
            frame_time=para_enb['time'])
        g_nb: GNodeB = GNodeB(
            region=CircularRegion(x=para_gnb['coordinate'][0], y=para_gnb['coordinate'][1],
                                  radius=para_gnb['radius']),
            power_tx=para_gnb['tx_power'],
            frame_freq=para_gnb['freq'],
            frame_time=para_gnb['time'],
            frame_max_layer=para_gnb['layer'])
        setup_noma([g_nb])
        return e_nb, g_nb

    def new_object_ue(self, g_profiles: Dict, d_profiles: Dict, e_profiles: Dict, e_nb: ENodeB, g_nb: GNodeB
                      ) -> Tuple[Tuple[GUserEquipment, ...], Tuple[DUserEquipment, ...], Tuple[EUserEquipment, ...]]:
        g_ue_list: Tuple[GUserEquipment, ...] = self.new_object_ue_list(UEType.G, g_profiles)
        d_ue_list: Tuple[DUserEquipment, ...] = self.new_object_ue_list(UEType.D, d_profiles)
        e_ue_list: Tuple[EUserEquipment, ...] = self.new_object_ue_list(UEType.E, e_profiles)

        for ue in (e_ue_list + g_ue_list + d_ue_list):
            ue.register_nb(e_nb, g_nb)

        return g_ue_list, d_ue_list, e_ue_list

    @staticmethod
    def new_object_ue_list(ue_type: UEType, ue_profile: Dict
                           ) -> Tuple[Union[GUserEquipment, DUserEquipment, EUserEquipment], ...]:
        if ue_type == UEType.E:
            ue_class = EUserEquipment
        elif ue_type == UEType.G:
            ue_class = GUserEquipment
        elif ue_type == UEType.D:
            ue_class = DUserEquipment
        else:
            raise AssertionError('Undefined UE type.')

        ue_list: List[Union[GUserEquipment, DUserEquipment, EUserEquipment]] = []
        for ue_idx in ue_profile:
            ue_para: Dict = ue_profile[ue_idx]
            if ue_type == UEType.E:
                candidate_set: Tuple[CandidateSet] = (LTEResourceBlock.E,)
            elif ue_type == UEType.G or ue_type == UEType.D:
                candidate_set: Tuple[CandidateSet, ...] = tuple(
                    Numerology[name] for name in ue_para['candidate_set'])
            else:
                raise AssertionError('Undefined UE type.')

            ue: Union[GUserEquipment, DUserEquipment, EUserEquipment] = ue_class(
                ue_para['request_data_rate'], candidate_set,
                Coordinate(ue_para['coordinate_x'], ue_para['coordinate_y']))
            ue.numerology_in_use = ue.candidate_set[-1]
            ue_list.append(ue)
        return tuple(ue_list)

    @staticmethod
    def new_object_channel_model(cochannel_bandwidth: int, e_nb: ENodeB, g_nb: GNodeB) -> ChannelModel:
        cochannel_index: Dict = cochannel(e_nb, g_nb, cochannel_bandwidth=cochannel_bandwidth)
        return ChannelModel(cochannel_index)

    @staticmethod
    def convert_worsen_threshold(worsen_threshold: int, frame_time: int) -> float:
        sec_to_frame: int = 1000 // (frame_time // 8)
        return worsen_threshold / sec_to_frame  # bit per frame
