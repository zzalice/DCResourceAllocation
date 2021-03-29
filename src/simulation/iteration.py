import json
import os
import pickle
import time
from typing import Dict, List, Tuple

from main import dc_resource_allocation
from main_frsa import frsa
from main_intuitive import intuitive_resource_allocation
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.resource_allocation.ds.util_enum import E_MCS, G_MCS


class IterateAlgo:
    def __init__(self, iteration: int, folder_data: str):
        assert iteration > 0
        self.iteration: int = iteration
        self.folder_data: str = folder_data

    def iter_layer(self, layers: List[int]):
        self.iter(('layers', layers), 'layer')

    def iter_ue(self, total_ue: List[int]):
        self.iter(('total ue', total_ue), 'ue')

    def iter(self, topic: Tuple[str, List[int]], folder_description: str):
        file_result: str = self.create_file(topic)

        program_start_time = time.time()
        for m in topic[1]:
            print(f'm: {m}')
            for i in range(self.iteration):
                print(f'i: {i}')
                file_data: str = f'{self.folder_data}/{m}{folder_description}/{i}'
                result: Dict[
                    str, Tuple[GNodeB, ENodeB, List[DUserEquipment], List[GUserEquipment], List[EUserEquipment]]] = {}

                # DC-RA
                start_time = time.time()
                result['DC-RA'] = dc_resource_allocation(file_data)
                print("--- %s min DC-RA ---" % round((time.time() - start_time) / 60, 3))

                # FRSA
                start_time = time.time()
                result['FRSA'] = frsa(file_data)
                print("--- %s min FRSA ---" % round((time.time() - start_time) / 60, 3))

                # Intuitive
                start_time = time.time()
                result['Intuitive'] = intuitive_resource_allocation(file_data)
                print("--- %s min Intui ---" % round((time.time() - start_time) / 60, 3))

                with open(file_result, 'ab+') as f:
                    pickle.dump({f'{m}{folder_description}': result}, f)
        print("--- Total %s min ---" % round((time.time() - program_start_time) / 60, 3))
        return True

    def create_file(self, main_topic: Tuple[str, List[int]]) -> str:
        parameter = {'iteration': self.iteration, main_topic[0]: main_topic[1], 'data folder': self.folder_data,
                     'gNB MCS': [G_MCS.get_worst().name, G_MCS.get_best().name],
                     'eNB MCS': [E_MCS.get_worst().name, E_MCS.get_best().name]}

        folder_graph: str = f'{os.path.dirname(__file__)}/graph/{self.folder_data}/gNB{parameter["gNB MCS"][0]}{parameter["gNB MCS"][1]}_eNB{parameter["eNB MCS"][0]}{parameter["eNB MCS"][1]}'
        self._new_directory(folder_graph)
        self.gen_txt_parameter(parameter, folder_graph)

        file_result: str = f'{folder_graph}/result.P'
        with open(file_result, 'wb') as f:
            pickle.dump(parameter, f)
        return file_result

    @staticmethod
    def _new_directory(path):
        if not os.path.exists(path):
            os.makedirs(path)

    @staticmethod
    def gen_txt_parameter(parameter, output_file_path: str):
        with open(f'{output_file_path}/parameter_iteration.txt', 'w') as f:
            json.dump(parameter, f)
