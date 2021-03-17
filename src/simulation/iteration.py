import json
import os
import pickle
import time
from typing import Dict, List, Tuple

from main import dc_resource_allocation
from main_intuitive import intuitive_resource_allocation
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.resource_allocation.ds.util_enum import E_MCS, G_MCS


class IterateAlgo:
    def iter_layer(self, iteration: int, layers: List[int], folder_data: str) -> bool:
        parameter = {'iteration': iteration, 'layers': layers, 'data folder': folder_data,
                     'gNB MCS': [G_MCS.get_worst().name, G_MCS.get_best().name],
                     'eNB MCS': [E_MCS.get_worst().name, E_MCS.get_best().name]}

        folder_graph: str = f'{os.path.dirname(__file__)}/graph/{folder_data}/gNB{parameter["gNB MCS"][0]}{parameter["gNB MCS"][1]}_eNB{parameter["eNB MCS"][0]}{parameter["eNB MCS"][1]}'
        self._new_directory(folder_graph)
        self.gen_txt_parameter(parameter, folder_graph)

        file_result: str = f'{folder_graph}/result.P'
        with open(file_result, 'wb') as f:
            pickle.dump(parameter, f)

        program_start_time = time.time()
        for l in layers:
            print(f'l: {l}')

            for i in range(iteration):
                print(f'i: {i}')
                file_data: str = f'{folder_data}/{l}layer/{i}'
                result: Dict[
                    str, Tuple[GNodeB, ENodeB, List[DUserEquipment], List[GUserEquipment], List[EUserEquipment]]] = {
                    'DC-RA': (), 'Intuitive': ()}

                # DC-RA
                start_time = time.time()
                result['DC-RA'] = dc_resource_allocation(file_data)
                print("--- %s min DC-RA ---" % round((time.time() - start_time) / 60, 3))

                # Intuitive
                start_time = time.time()
                result['Intuitive'] = intuitive_resource_allocation(file_data)
                print("--- %s min Intui ---" % round((time.time() - start_time) / 60, 3))

                with open(file_result, 'ab+') as f:
                    pickle.dump({f'{l}layer': result}, f)
        print("--- %s min ---" % round((time.time() - program_start_time) / 60, 3))
        return True

    @staticmethod
    def _new_directory(path):
        if not os.path.exists(path):
            os.makedirs(path)

    @staticmethod
    def gen_txt_parameter(parameter, output_file_path: str):
        with open(f'{output_file_path}/parameter_iteration.txt', 'w') as f:
            json.dump(parameter, f)
