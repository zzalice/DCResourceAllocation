import math
from datetime import datetime
from typing import Dict, List

from src.simulation.data.data_generator import DataGenerator


def main(parameter: Dict):
    DataGenerator(iteration=parameter['iteration'], output_file_path=parameter['output_file_path'],
                  eue_num=parameter['eue_num'], eue_qos_range=parameter['eue_qos'], eue_hotspots=parameter['eue_hotspots'],
                  gue_num=parameter['gue_num'], gue_qos_range=parameter['gue_qos'], gue_hotspots=parameter['gue_hotspots'],
                  due_num=parameter['due_num'], due_qos_range=parameter['due_qos'], due_hotspots=parameter['due_hotspots'],
                  enb_coordinate=parameter['enb_coordinate'], enb_radius=parameter['enb_radius'],
                  enb_tx_power=parameter['enb_tx_power'], enb_freq=parameter['enb_freq'],
                  enb_time=parameter['enb_time'],
                  gnb_coordinate=parameter['gnb_coordinate'], gnb_radius=parameter['gnb_radius'],
                  gnb_tx_power=parameter['gnb_tx_power'], gnb_freq=parameter['gnb_freq'],
                  gnb_time=parameter['gnb_time'], gnb_layer=parameter['gnb_layer'],
                  inr_discount=parameter['inr_discount'],
                  cochannel_bandwidth=parameter['cochannel_bandwidth'],
                  worsen_threshold=parameter['worsen_threshold']).generate_data()


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


if __name__ == '__main__':
    date: str = datetime.today().strftime("%m%d-%H%M%S")
    output_folder: str = f'{date}avg_deploy'  # <--- change

    # # --- for layer ---
    # num_of_layer = [1, 2, 3, 4, 5]  # <--- change
    # for i in num_of_layer:
    #     para = {'output_file_path': f'{output_folder}/{i}layer',
    # # --- for ue ---
    # # due:gue:eue_num = 3:4:17   when radius are 0.5 and 0.3
    # # due:gue:eue_num = 2:3:6    when radius are 0.5 and 0.4
    num_of_total_ue = [60, 80, 100, 120, 140, 160, 180, 200]  # <--- change
    proportion_of_ue = [2, 3, 6]  # for radius 0.4   <--- change
    num_of_ue = calc_num_ue(num_of_total_ue, proportion_of_ue)
    for i in num_of_ue:
        para = {'output_file_path': f'{output_folder}/{i["total"]}ue',
                'iteration': 100,
                'due_num': i['due'],
                'due_qos': [16_000, 100_000],
                'due_hotspots': (),  # e.g. ((-0.15, 0.0, 0.15, 75),) => (x, y, radius, #ue)
                'gue_num': i['gue'],
                'gue_qos': [16_000, 100_000],
                'gue_hotspots': (),
                'eue_num': i['eue'],
                'eue_qos': [16_000, 100_000],
                'eue_hotspots': (),

                # gnb_freq(MHz/#): 5/25, 10/52, 15/79, 20/106, 25/133, 30/160, 40/216, 50/270, 60/324, 70/378, 80/434, 90/490, 100/546
                # enb_freq(MHz/#): 1.4/6, 3/15, 5/25, 10/50, 15/75, 20/100
                'gnb_freq': 25, 'gnb_time': 8, 'gnb_radius': 0.4, 'gnb_coordinate': (0.5, 0.0), 'gnb_tx_power': 30,
                'gnb_layer': 5, 'inr_discount': 0.5,
                'enb_freq': 200, 'enb_time': 8, 'enb_radius': 0.5, 'enb_coordinate': (0.0, 0.0), 'enb_tx_power': 46,

                'cochannel_bandwidth': 0,
                'worsen_threshold': -20  # bps, must be <= 0
                # range of MCS: in file resource_allocation/ds/util_enum.py
                }

        main(para)
