from datetime import datetime
from typing import Dict

from src.simulation.data.data_generator import DataGenerator


def main(parameter: Dict):
    DataGenerator(iteration=parameter['iteration'], output_file_path=parameter['output_file_path'],
                  qos_range=parameter['qos_range'],
                  eue_num=parameter['eue_num'], eue_hotspots=parameter['eue_hotspots'],
                  gue_num=parameter['gue_num'], gue_hotspots=parameter['gue_hotspots'],
                  due_num=parameter['due_num'], due_hotspots=parameter['due_hotspots'],
                  enb_coordinate=parameter['enb_coordinate'], enb_radius=parameter['enb_radius'],
                  enb_tx_power=parameter['enb_tx_power'], enb_freq=parameter['enb_freq'],
                  enb_time=parameter['enb_time'],
                  gnb_coordinate=parameter['gnb_coordinate'], gnb_radius=parameter['gnb_radius'],
                  gnb_tx_power=parameter['gnb_tx_power'], gnb_freq=parameter['gnb_freq'],
                  gnb_time=parameter['gnb_time'], gnb_layer=parameter['gnb_layer'],
                  inr_discount=parameter['inr_discount'],
                  cochannel_bandwidth=parameter['cochannel_bandwidth'],
                  worsen_threshold=parameter['worsen_threshold']).generate_data()


if __name__ == '__main__':
    num_of_layer = [1, 2, 3, 4, 5]  # <--- change
    date: str = datetime.today().strftime("%m%d-%H%M%S")
    output_folder: str = f'{date}large_radius'   # <--- change
    for i in num_of_layer:
        para = {'output_file_path': f'{output_folder}/{i}layer',
                'iteration': 100,
                'qos_range': [16_000, 512_000],
                # due:gue:eue_num = 14:10:62 when radius are 0.5 and 0.3
                # due:gue:eue_num = 3:2:6    when radius are 0.5 and 0.4
                'due_num': 210,
                'due_hotspots': (),  # e.g. ((-0.15, 0.0, 0.15, 75),) => (x, y, radius, #ue)
                'gue_num': 150,
                'gue_hotspots': (),
                'eue_num': 930,
                'eue_hotspots': (),

                # gnb_freq(MHz/#): 5/25, 10/52, 15/79, 20/106, 25/133, 30/160, 40/216, 50/270, 60/324, 70/378, 80/434, 90/490, 100/546
                # enb_freq(MHz/#): 1.4/6, 3/15, 5/25, 10/50, 15/75, 20/100
                'gnb_coordinate': (0.5, 0.0), 'gnb_radius': 0.3, 'gnb_tx_power': 30, 'gnb_freq': 216, 'gnb_time': 80,
                'gnb_layer': i, 'inr_discount': 0.5,
                'enb_coordinate': (0.0, 0.0), 'enb_radius': 0.5, 'enb_tx_power': 46, 'enb_freq': 200, 'enb_time': 80,

                'cochannel_bandwidth': 25,
                'worsen_threshold': -20  # bps, must be <= 0
                # range of MCS: in file resource_allocation/ds/util_enum.py
                }

        main(para)
