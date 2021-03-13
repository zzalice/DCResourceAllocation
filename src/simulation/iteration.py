import os
import pickle
import time
from typing import Dict, List, Tuple

from main import dc_resource_allocation
from main_intuitive import intuitive_resource_allocation
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment


class IterateAlgo:
    def iter_layer(self, iteration: int, layers: List[int], folder_data: str) -> bool:
        folder_graph: str = f'{os.path.dirname(__file__)}/graph/{folder_data}/'
        file_result: str = f'{folder_graph}result_iter_layer.P'
        self._new_directory(folder_graph)
        with open(file_result, 'wb') as f:
            pickle.dump({'iteration': iteration, 'layers': layers, 'data folder': folder_data}, f)

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
        print("--- %s min ---" % round((time.time() - program_start_time)/60, 3))
        return True

    @staticmethod
    def _new_directory(path):
        if not os.path.exists(path):
            os.makedirs(path)
