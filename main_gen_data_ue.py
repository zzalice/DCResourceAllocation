from datetime import datetime
from typing import Any, Dict, List, Tuple

from main_gen_data_layer import main_gen_data


def gen_data_number_ue(num_of_total_ue: List[int], deploy_type: int, cell_edge_radius_proportion: float,
                       edge_ue_proportion: float, hotspots: Tuple[Tuple[float, float, float, int], ...],
                       dc_proportion: int, parameter: Dict[str, Any], folder: str):
    parameter['deploy_type'] = deploy_type
    parameter['cell_edge_radius_proportion'] = cell_edge_radius_proportion
    parameter['edge_ue_proportion'] = edge_ue_proportion
    parameter['hotspots'] = hotspots
    parameter['dc_proportion'] = dc_proportion

    for i in num_of_total_ue:
        parameter['output_file_path'] = f'{folder}/{i}ue'
        parameter['total_num_ue'] = i
        main_gen_data(parameter)


def gen_data_due_to_all(proportion_due_to_all: List[int], num_of_total_ue: int, parameter: Dict[str, Any], folder: str):
    """
    :param proportion_due_to_all: Default as %.
    :param num_of_total_ue:
    :param parameter:
    :param folder:
    :return:
    """
    assert 0 <= proportion_due_to_all[0] and proportion_due_to_all[-1] <= 100
    parameter['total_num_ue'] = num_of_total_ue

    parameter['deploy_type'] = 3,  # 3: more or less dUE
    parameter['cell_edge_radius_proportion'] = None
    parameter['edge_ue_proportion'] = None
    parameter['hotspots'] = None
    for i in proportion_due_to_all:
        parameter['output_file_path'] = f'{folder}/{i}p_due'
        parameter['dc_proportion'] = i
        main_gen_data(parameter)


if __name__ == '__main__':
    date: str = datetime.today().strftime("%m%d-%H%M%S")
    output_folder: str = f'{date}UE_'  # <--- change

    para = {'iteration': 100,
            'due_qos': [22_000, 100_000],
            'gue_qos': [22_000, 100_000],
            'eue_qos': [12_000, 60_000],

            # gnb_freq(MHz/#): 5/25, 10/52, 15/79, 20/106, 25/133, 30/160, 40/216, 50/270, 60/324, 70/378, 80/434, 90/490, 100/546
            # enb_freq(MHz/#): 1.4/6, 3/15, 5/25, 10/50, 15/75, 20/100
            'gnb_freq': 216, 'gnb_time': 8, 'gnb_layer': 5, 'gnb_tx_power': 46,
            'enb_freq': 100, 'enb_time': 8, 'enb_tx_power': 46,
            'cochannel_bandwidth': 0,

            'gnb_radius': 0.5, 'gnb_coordinate': (0.5, 0.0),
            'enb_radius': 0.5, 'enb_coordinate': (0.0, 0.0),

            'inr_discount': 0.5,
            'worsen_threshold': -100_000_000  # bps
            # range of MCS: in file resource_allocation/ds/util_enum.py
            }

    # '''
    gen_data_number_ue(
        num_of_total_ue=[300, 400, 500, 600, 700, 800, 900],
        deploy_type=0,  # 0: random, 1: cell edge, 2: hot spot
        cell_edge_radius_proportion=0.1, edge_ue_proportion=0.4,
        hotspots=(),  # e.g. ((0.4, 0.0, 0.09, 0.4),) => (x, y, radius, proportion of ue)
        dc_proportion=50,  # [0, 100]
        parameter=para, folder=output_folder)
    '''
    gen_data_due_to_all(
        proportion_due_to_all=[i for i in range(10, 91, 10)],  # [30, 40, 50] means 0.3, 0.4, 0.5
        num_of_total_ue=600,
        parameter=para, folder=output_folder)
    '''
