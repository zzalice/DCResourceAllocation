import os
from typing import Dict

from src.simulation.data.data_generator import DataGenerator


def main(parameter: Dict):
    DataGenerator(times=parameter['times'], output_file_path=parameter['output_file_path'],
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
                  cochannel_bandwidth=parameter['cochannel_bandwidth']).generate_data()


if __name__ == '__main__':
    num_of_layer = [1, 2, 3]  # <--- change
    for i in num_of_layer:  # <--- change
        folder_name: str = f'large_radius/{i}layer'  # <--- change

        para = {'times': 500,
                'output_file_path': folder_name,
                'qos_range': [16_000, 512_000],
                'eue_num': 300,
                'eue_hotspots': ((-0.15, 0.0, 0.15, 75), (-0.45, 0.0, 0.15, 75), (-0.75, 0.0, 0.15, 75)),
                'gue_num': 300,
                'gue_hotspots': (),
                'due_num': 300,
                'due_hotspots': ((0.46, 0.0, 0.15, 100),),
                'enb_coordinate': (0.0, 0.0), 'enb_radius': 1, 'enb_tx_power': 46, 'enb_freq': 100, 'enb_time': 8,
                'gnb_coordinate': (0.8, 0.0), 'gnb_radius': 0.5, 'gnb_tx_power': 30, 'gnb_freq': 216, 'gnb_time': 8,
                'gnb_layer': i,
                'cochannel_bandwidth': 25}  # <--- change i in para

        if not os.path.exists(f'src/simulation/data/{para["output_file_path"]}'):
            os.makedirs(f'src/simulation/data/{para["output_file_path"]}')

        main(para)