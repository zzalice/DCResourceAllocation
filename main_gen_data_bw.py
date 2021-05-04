from datetime import datetime
from typing import Any, Dict, List

from main_gen_data_layer import main_gen_data


def gnb_mhz_to_bu(mhz: int):
    if mhz == 5:
        return 25
    elif mhz == 10:
        return 52
    elif mhz == 15:
        return 79
    elif mhz == 20:
        return 106
    elif mhz == 25:
        return 133
    elif mhz == 30:
        return 160
    elif mhz == 35:
        return 188
    elif mhz == 40:
        return 216
    elif mhz == 45:
        return 243
    elif mhz == 50:
        return 270
    elif mhz == 55:
        return 297
    elif mhz == 60:
        return 324
    elif mhz == 65:
        return 351
    elif mhz == 70:
        return 378
    elif mhz == 75:
        return 406
    elif mhz == 80:
        return 434
    elif mhz == 85:
        return 462
    elif mhz == 90:
        return 490
    elif mhz == 95:
        return 518
    elif mhz == 100:
        return 546


def gen_data_bw_gnb(gnb_bw: List[int], cochannel_bw: int, parameter: Dict[str, Any], folder: str):
    gnb_bw_in_bu: List[int] = [gnb_mhz_to_bu(i) for i in gnb_bw]
    gnb_bw_in_bu.sort()
    assert cochannel_bw <= gnb_bw_in_bu[0] and cochannel_bw <= parameter[
        'enb_freq'], 'Co-channel BW is wider than NB BW.'
    parameter['cochannel_bandwidth'] = gnb_mhz_to_bu(cochannel_bw)

    for i in gnb_bw_in_bu:
        parameter['output_file_path'] = f'{folder}/{i}bw_gnb'
        parameter['gnb_freq'] = i
        main_gen_data(parameter)


def gen_data_bw_cochannel(cochannel_bw: List[int], gnb_bw: int, parameter: Dict[str, Any], folder: str):
    cochannel_bw_in_bu: List[int] = [gnb_mhz_to_bu(i) for i in cochannel_bw]
    cochannel_bw_in_bu.sort()
    parameter['gnb_freq'] = gnb_mhz_to_bu(gnb_bw)
    assert cochannel_bw_in_bu[-1] <= parameter['gnb_freq'] and cochannel_bw_in_bu[-1] <= parameter[
        'enb_freq'], 'Co-channel BW is wider than NB BW.'

    for i in cochannel_bw_in_bu:
        parameter['output_file_path'] = f'{folder}/{i}bw_co'
        parameter['cochannel_bandwidth'] = i
        main_gen_data(parameter)


if __name__ == '__main__':
    date: str = datetime.today().strftime("%m%d-%H%M%S")
    output_folder: str = f'{date}BWGNB_'  # <--- change

    para = {'iteration': 100,

            'total_num_ue': 600,
            'due_qos': [22_000, 100_000],
            'gue_qos': [22_000, 100_000],
            'eue_qos': [12_000, 60_000],

            # enb_freq(MHz/#): 1.4/6, 3/15, 5/25, 10/50, 15/75, 20/100
            'gnb_time': 8, 'gnb_layer': 5, 'gnb_tx_power': 46,
            'enb_freq': 100,  # number of BU
            'enb_time': 8, 'enb_tx_power': 46,

            'gnb_radius': 0.5, 'gnb_coordinate': (0.5, 0.0),
            'enb_radius': 0.5, 'enb_coordinate': (0.0, 0.0),

            'deploy_type': 0,  # 0: random, 1: cell edge, 2: hot spot, 3: more or less dUE
            'cell_edge_radius_proportion': 0.1, 'edge_ue_proportion': 0.4,
            'hotspots': (),  # e.g. ((0.4, 0.0, 0.09, 0.4),) => (x, y, radius, proportion of ue)
            'dc_proportion': 50,  # [0, 100]

            'inr_discount': 0.5,
            'worsen_threshold': -100_000_000  # bps
            # range of MCS: in file resource_allocation/ds/util_enum.py
            }

    # # gnb_freq(MHz/#): 5/25, 10/52, 15/79, 20/106, 25/133, 30/160, 40/216, 50/270, 60/324, 70/378, 80/434, 90/490, 100/546
    # '''
    gen_data_bw_gnb(
        gnb_bw=[10, 20, 30, 40, 50, 60, 70, 80, 90, 100],  # MHz
        cochannel_bw=0,  # MHz
        parameter=para, folder=output_folder)
    '''
    gen_data_bw_cochannel(
        cochannel_bw=[i for i in range(5, 51, 5)],  # MHz
        gnb_bw=50,  # MHz
        parameter=para, folder=output_folder)
    # '''
