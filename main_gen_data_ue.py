import math
from datetime import datetime
from typing import Any, Dict, List

from main_gen_data_layer import main_gen_data


def calc_num_ue(total: List[int], proportion) -> List[Dict[str, int]]:
    """
    With given number of total UE in the whole system.
    Calculate the number of UE of each type by the input proportion.
    :param total: A list of total UE.
    :param proportion: The proportion of the num of dUE, gUE, and eUE.
    :return: [{'total': int, 'num_due': int, 'num_gue': int, 'num_eue': int}, {...}, ...]
    """
    p_total = 0
    for p in proportion:
        p_total += p
    result: List[Dict[str, int]] = []
    for t in total:
        due_num = math.ceil(t * (proportion[0] / p_total))
        gue_num = math.ceil(t * (proportion[1] / p_total))
        eue_num = math.ceil(t * (proportion[2] / p_total))
        result.append({'total': t, 'due': due_num, 'gue': gue_num, 'eue': eue_num})
    return result


def gen_data_number_ue(num_of_total_ue: List[int], proportion_of_ue: List[int],
                       parameter: Dict[str, Any], folder: str):
    num_of_ue = calc_num_ue(num_of_total_ue, proportion_of_ue)
    for i in num_of_ue:
        parameter['output_file_path'] = f'{folder}/{i["total"]}ue'
        parameter['due_num'] = i['due']
        parameter['gue_num'] = i['gue']
        parameter['eue_num'] = i['eue']

        main_gen_data(parameter)


def calc_fixed_due_avg_deploy_others(total_ue: int, due_to_all: List[int], gue_to_eue: List[int]
                                     ) -> List[Dict[str, int]]:
    result: List[Dict[str, int]] = []
    for p in due_to_all:
        due_num = math.ceil(total_ue * (p / 100))
        gue_num = math.ceil((total_ue - due_num) * (gue_to_eue[0] / (gue_to_eue[0] + gue_to_eue[1])))
        eue_num = math.ceil((total_ue - due_num) * (gue_to_eue[1] / (gue_to_eue[0] + gue_to_eue[1])))
        result.append({'proportion': p, 'due': due_num, 'gue': gue_num, 'eue': eue_num})
    return result


def gen_data_due_to_all(num_of_total_ue: int, proportion_due_to_all: List[int], proportion_gue_to_eue: List[int],
                        parameter: Dict[str, Any], folder: str):
    """
    :param num_of_total_ue:
    :param proportion_due_to_all: Default as %.
    :param proportion_gue_to_eue: The proportion of gUE:eUE. Better be average deploy.
    :param parameter:
    :param folder:
    :return:
    """
    assert 0 <= proportion_due_to_all[0] and proportion_due_to_all[-1] <= 100
    num_of_ue = calc_fixed_due_avg_deploy_others(num_of_total_ue, proportion_due_to_all, proportion_gue_to_eue)
    for i in num_of_ue:
        parameter['output_file_path'] = f'{folder}/{i["proportion"]}p_due'
        parameter['due_num'] = i['due']
        parameter['gue_num'] = i['gue']
        parameter['eue_num'] = i['eue']

        main_gen_data(parameter)


if __name__ == '__main__':
    output_folder: str = 'avg_deploy'  # <--- change
    para = {'iteration': 100,
            'due_qos': [16_000, 100_000],
            'due_hotspots': (),  # e.g. ((-0.15, 0.0, 0.15, 75),) => (x, y, radius, #ue)
            'gue_qos': [16_000, 100_000],
            'gue_hotspots': (),
            'eue_qos': [16_000, 100_000],
            'eue_hotspots': (),

            # gnb_freq(MHz/#): 5/25, 10/52, 15/79, 20/106, 25/133, 30/160, 40/216, 50/270, 60/324, 70/378, 80/434, 90/490, 100/546
            # enb_freq(MHz/#): 1.4/6, 3/15, 5/25, 10/50, 15/75, 20/100
            'gnb_freq': 25, 'gnb_time': 8, 'gnb_radius': 0.4, 'gnb_coordinate': (0.5, 0.0), 'gnb_tx_power': 30,
            'gnb_layer': 5, 'inr_discount': 0.5,
            'enb_freq': 200, 'enb_time': 8, 'enb_radius': 0.5, 'enb_coordinate': (0.0, 0.0), 'enb_tx_power': 46,

            'cochannel_bandwidth': 0,
            'worsen_threshold': -100_000_000  # bps
            # range of MCS: in file resource_allocation/ds/util_enum.py
            }

    # # due:gue:eue_num = 3:4:17    when radius 0.5 and 0.3, coordinate gNB (0.5, 0)
    # # due:gue:eue_num = 2:3:6     when radius 0.5 and 0.4, coordinate gNB (0.5, 0)
    # # due:gue:eue_num = 29:21:49  when radius 0.5 and 0.4, coordinate gNB (0.4, 0)
    # gen_data_number_ue(num_of_total_ue=[300, 400, 500, 600, 700, 800, 900],
    #                    proportion_of_ue=[2, 3, 6], parameter=para, folder=f'{datetime.today().strftime("%m%d-%H%M%S")}{output_folder}')
    gen_data_due_to_all(num_of_total_ue=600,
                        proportion_due_to_all=[i for i in range(10, 91, 10)],  # [30, 40, 50] means 0.3, 0.4, 0.5
                        proportion_gue_to_eue=[3, 6], parameter=para, folder=f'{datetime.today().strftime("%m%d-%H%M%S")}{output_folder}')