import json
import os
import random
from typing import Dict

from src.resource_allocation.ds.util_enum import Numerology
from src.resource_allocation.ds.util_type import CircularRegion, Coordinate
from src.simulation.data.deployment import Deploy


def gen_data_relate_para_pdue(folder_of_para_to_follow: str, dc_proportion: int, para: Dict):
    folder_of_para_to_follow: str = f'{os.path.dirname(__file__)}/src/simulation/data/{folder_of_para_to_follow}'
    output_file_path: str = f'{os.path.dirname(__file__)}/src/simulation/data/{para["output_file_path"]}'
    if not os.path.exists(output_file_path):
        os.makedirs(output_file_path)

    iterations = para['iteration']
    eue_num: int = 0
    gue_num: int = 0
    due_num: int = 0
    for i in range(iterations):
        with open(f'{folder_of_para_to_follow}/{i}.json', 'r') as f:
            data = json.load(f)
        enb_region: CircularRegion = CircularRegion(x=data['e_nb']['coordinate'][0], y=data['e_nb']['coordinate'][1],
                                                    radius=data['e_nb']['radius'])
        gnb_region: CircularRegion = CircularRegion(x=data['g_nb']['coordinate'][0], y=data['g_nb']['coordinate'][1],
                                                    radius=data['g_nb']['radius'])
        coordinates_sc, coordinates_dc = Deploy.dc_proportion(
            para['total_num_ue'], (enb_region, gnb_region), dc_proportion)
        eue_num: int = len(coordinates_sc[0])
        gue_num: int = len(coordinates_sc[1])
        due_num: int = len(coordinates_dc)
        num_ue_to_due: int = due_num - len(data['d_ue_list'])
        for j in range(num_ue_to_due):
            idx_ue_to_due: int = random.randint(0, len(data['e_ue_list']) + len(data['g_ue_list']) - 1)
            if idx_ue_to_due < len(data['e_ue_list']):
                data = json_move_ue_to_due(data, 'e_ue_list', idx_ue_to_due, coordinates_dc[j])
            else:
                data = json_move_ue_to_due(data, 'g_ue_list', idx_ue_to_due - len(data['e_ue_list']), coordinates_dc[j])

        with open(f'{output_file_path}/{str(i)}.json', 'w') as f:
            json.dump(data, f)

    modify_txt_parameter(folder_of_para_to_follow, output_file_path, para, due_num, gue_num, eue_num)


def json_move_ue_to_due(data: Dict, ue_list_type: str, idx_ue: int, new_coordinate: Coordinate) -> Dict:
    ue: Dict = data[ue_list_type][str(idx_ue)]
    if ue_list_type == 'e_ue_list':
        candidate_set = Numerology.gen_candidate_set(random_pick=True)
        ue['candidate_set'] = tuple(c.name for c in candidate_set)
    ue['coordinate_x'] = new_coordinate.x
    ue['coordinate_y'] = new_coordinate.y
    data['d_ue_list'][str(len(data['d_ue_list']))] = ue

    del data[ue_list_type][str(idx_ue)]
    for new_idx in range(idx_ue, len(data[ue_list_type])):
        data[ue_list_type][str(new_idx)] = data[ue_list_type].pop(str(new_idx+1))

    return data


def modify_txt_parameter(folder_of_para_to_follow: str, output_file_path: str,
                         para: Dict, due_num: int, gue_num: int, eue_num: int):
    with open(f'{folder_of_para_to_follow}/parameter_data.txt', 'r') as f:
        information = f.readlines()

    information[1] = f'dUE number: {due_num}\tQoS(in bps): {para["due_qos"]}\n'
    information[2] = f'gUE number: {gue_num}\tQoS(in bps): {para["gue_qos"]}\n'
    information[3] = f'eUE number: {eue_num}\tQoS(in bps): {para["eue_qos"]}\n'
    information[22] = f'DC proportion: {para["dc_proportion"]}\n'

    with open(f'{output_file_path}/parameter_data.txt', 'w') as f:
        f.writelines(information)
