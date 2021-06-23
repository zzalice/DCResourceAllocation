from datetime import datetime
from typing import Dict

from src.simulation.data.data_generator import DataGenerator


def main_gen_data(parameter: Dict):
    DataGenerator(iteration=parameter['iteration'], output_file_path=parameter['output_file_path'],
                  total_num_ue=parameter['total_num_ue'],
                  eue_qos_range=parameter['eue_qos'], gue_qos_range=parameter['gue_qos'],
                  due_qos_range=parameter['due_qos'],
                  gnb_freq=parameter['gnb_freq'], gnb_time=parameter['gnb_time'],
                  enb_freq=parameter['enb_freq'], enb_time=parameter['enb_time'],
                  gnb_coordinate=parameter['gnb_coordinate'], gnb_radius=parameter['gnb_radius'],
                  enb_coordinate=parameter['enb_coordinate'], enb_radius=parameter['enb_radius'],
                  gnb_tx_power=parameter['gnb_tx_power'], enb_tx_power=parameter['enb_tx_power'],
                  gnb_layer=parameter['gnb_layer'],
                  inr_discount=parameter['inr_discount'],
                  deploy_type=parameter['deploy_type'],
                  edge_radius=parameter['cell_edge_radius_proportion'], edge_ue=parameter['edge_ue_proportion'],
                  hot_spots=parameter['hotspots'],
                  dc_proportion=parameter['dc_proportion'],
                  cochannel_bandwidth=parameter['cochannel_bandwidth'],
                  worsen_threshold=parameter['worsen_threshold']).generate_data()


if __name__ == '__main__':
    date: str = datetime.today().strftime("%m%d-%H%M%S")
    output_folder: str = f'{date}L_'  # <--- change

    num_of_layer = [1, 2, 3, 4, 5, 6]  # <--- change
    for i in num_of_layer:
        para = {'output_file_path': f'{output_folder}/{i}layer',
                'iteration': 1000,

                'total_num_ue': 300,
                # (lower bound, upper bound, proportion of ue) e.g. ((22_000, 40_000, 0.6), (40_000, 100_000, 0.4))
                'due_qos': ((100_000, 500_000, 1.0),),
                'gue_qos': ((100_000, 500_000, 1.0),),
                'eue_qos': ((100_000, 500_000, 1.0),),

                # gnb_freq(MHz/#): 5/25, 10/52, 15/79, 20/106, 25/133, 30/160, 40/216, 50/270, 60/324, 70/378, 80/434, 90/490, 100/546
                # enb_freq(MHz/#): 1.4/6, 3/15, 5/25, 10/50, 15/75, 20/100
                'gnb_freq': 216, 'gnb_time': 8, 'gnb_layer': i, 'gnb_tx_power': 46,
                'enb_freq': 200, 'enb_time': 8, 'enb_tx_power': 46,
                'cochannel_bandwidth': 25,

                'gnb_radius': 0.5, 'gnb_coordinate': (0.5, 0.0),
                'enb_radius': 0.5, 'enb_coordinate': (0.0, 0.0),

                'deploy_type': 0,  # 0: random, 1: cell edge, 2: hot spot, 3: more or less dUE
                'cell_edge_radius_proportion': 0.1, 'edge_ue_proportion': 0.4,
                'hotspots': (),  # e.g. ((0.4, 0.0, 0.09, 0.4),) => (x, y, radius, proportion of ue)
                'dc_proportion': 50,   # [0, 100]

                'inr_discount': 0.7,
                'worsen_threshold': -100_000_000  # bps
                # range of MCS: in file resource_allocation/ds/util_enum.py
                }

        main_gen_data(para)
