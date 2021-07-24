from datetime import datetime
from enum import Enum
from typing import Any, Dict, List

from main_gen_data_layer import main_gen_data


class GnbMhzBuConvertor(Enum):
    mhz0 = 0
    mhz5 = 25
    mhz10 = 52
    mhz15 = 79
    mhz20 = 106
    mhz25 = 133
    mhz30 = 160
    mhz35 = 188
    mhz40 = 216
    mhz45 = 243
    mhz50 = 270
    mhz55 = 297
    mhz60 = 324
    mhz65 = 351
    mhz70 = 378
    mhz75 = 406
    mhz80 = 434
    mhz85 = 462
    mhz90 = 490
    mhz95 = 518
    mhz100 = 546

    @staticmethod
    def mhz_to_bu(mhz: int) -> int:
        enum_name: str = f'mhz{mhz}'
        try:
            count_bu: int = getattr(GnbMhzBuConvertor, enum_name).value
            return count_bu
        except AttributeError:
            raise AttributeError('Undefined bandwidth.')

    @staticmethod
    def bu_to_mhz(count_bu: int) -> int:
        for mhz_enum in GnbMhzBuConvertor:
            if mhz_enum.value == count_bu:
                return int(mhz_enum.name.replace('mhz', ''))
        raise AttributeError('Undefined bandwidth.')


def gen_data_bw_gnb(gnb_bw: List[int], cochannel_bw: int, parameter: Dict[str, Any], folder: str):
    gnb_bw_in_bu: List[int] = [GnbMhzBuConvertor.mhz_to_bu(i) for i in gnb_bw]
    gnb_bw_in_bu.sort()
    assert cochannel_bw <= gnb_bw_in_bu[0] and cochannel_bw <= parameter[
        'enb_freq'], 'Co-channel BW is wider than NB BW.'
    parameter['cochannel_bandwidth'] = GnbMhzBuConvertor.mhz_to_bu(cochannel_bw)

    for i in gnb_bw_in_bu:
        parameter['output_file_path'] = f'{folder}/{i}bw_gnb'
        parameter['gnb_freq'] = i
        main_gen_data(parameter)


def gen_data_bw_cochannel(cochannel_bw: List[int], gnb_bw: int, parameter: Dict[str, Any], folder: str):
    cochannel_bw_in_bu: List[int] = [GnbMhzBuConvertor.mhz_to_bu(i) for i in cochannel_bw]
    cochannel_bw_in_bu.sort()
    parameter['gnb_freq'] = GnbMhzBuConvertor.mhz_to_bu(gnb_bw)
    assert cochannel_bw_in_bu[-1] <= parameter['gnb_freq'] and cochannel_bw_in_bu[-1] <= parameter[
        'enb_freq'], 'Co-channel BW is wider than NB BW.'

    for i in cochannel_bw_in_bu:
        parameter['output_file_path'] = f'{folder}/{i}bw_co'
        parameter['cochannel_bandwidth'] = i
        main_gen_data(parameter)


if __name__ == '__main__':
    date: str = datetime.today().strftime("%m%d-%H%M%S")
    output_folder: str = f'{date}BWGNB_golden3_inr100'  # <--- change

    para = {'iteration': 1000,

            'total_num_ue': 300,
            # (lower bound, upper bound, proportion of ue) e.g. ((22_000, 40_000, 0.6), (40_000, 100_000, 0.4))
            'due_qos': ((100_000, 500_000, 1.0),),
            'gue_qos': ((100_000, 500_000, 1.0),),
            'eue_qos': ((100_000, 500_000, 1.0),),

            # enb_freq(MHz/#): 1.4/6, 3/15, 5/25, 10/50, 15/75, 20/100
            'gnb_time': 8, 'gnb_layer': 4, 'gnb_tx_power': 46,
            'enb_freq': 200,  # number of BU
            'enb_time': 8, 'enb_tx_power': 46,

            'gnb_radius': 0.5, 'gnb_coordinate': (0.5, 0.0),
            'enb_radius': 0.5, 'enb_coordinate': (0.0, 0.0),

            'deploy_type': 0,  # 0: random, 1: cell edge, 2: hot spot, 3: more or less dUE
            'cell_edge_radius_proportion': 0.1, 'edge_ue_proportion': 0.4,
            'hotspots': (),  # e.g. ((0.4, 0.0, 0.09, 0.4),) => (x, y, radius, proportion of ue)
            'dc_proportion': 50,  # [0, 100]

            'inr_discount': 1.0,
            'worsen_threshold': -100_000_000  # bps
            # range of MCS: in file resource_allocation/ds/util_enum.py
            }

    # # gnb_freq(MHz/#): 5/25, 10/52, 15/79, 20/106, 25/133, 30/160, 40/216, 50/270, 60/324, 70/378, 80/434, 90/490, 100/546
    # '''
    gen_data_bw_gnb(
        gnb_bw=[i for i in range(10, 101, 5)],  # MHz
        cochannel_bw=5,  # MHz
        parameter=para, folder=output_folder)
    '''
    gen_data_bw_cochannel(
        cochannel_bw=[i for i in range(0, 36, 5)],  # MHz
        gnb_bw=40,  # MHz
        parameter=para, folder=output_folder)
    # '''
