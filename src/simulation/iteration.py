import json
import math
import os
import pickle
import threading
import time
from typing import Any, Dict, List, Tuple

from main import dc_resource_allocation
from main_frsa import frsa
from main_intuitive import intuitive_resource_allocation
from main_msema import msema_rb_ra
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.resource_allocation.ds.util_enum import E_MCS, G_MCS


class IterateAlgo:
    def __init__(self, iteration: int, folder_data: str):
        assert iteration > 0
        self.iteration: int = iteration
        self.folder_data: str = folder_data

        self.topic: Dict[str, Any] = {'topic': '', 'item': [], 'folder description': ''}
        self.folder_graph: str = ''

    def iter_layer(self, layers: List[int]):
        self.topic: Dict[str, Any] = {'topic': 'layers', 'item': layers, 'folder description': 'layer'}
        self.large_iter()

    def iter_ue(self, total_ue: List[int]):
        self.topic: Dict[str, Any] = {'topic': 'total ue', 'item': total_ue, 'folder description': 'ue'}
        self.large_iter()

    def iter_due_to_all(self, due_proportion: List[int]):
        self.topic: Dict[str, Any] = {'topic': 'due to all', 'item': due_proportion, 'folder description': 'p_due'}
        self.large_iter()

    def large_iter(self):
        each_file_run: int = 1
        assert each_file_run > 0, 'Value Error.'

        self.new_directory()
        threads = []
        program_start_time = time.time()
        for i in range(math.ceil(self.iteration / each_file_run)):
            iter_lower_bound = i * each_file_run
            iter_higher_bound = iter_lower_bound + (each_file_run - 1) if iter_lower_bound + (each_file_run - 1) < self.iteration else self.iteration - 1
            t = threading.Thread(target=self.iter,
                                 args=(iter_lower_bound, iter_higher_bound))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
        print("--- Total %s min ---" % round((time.time() - program_start_time) / 60, 1))
        self.gen_txt_parameter()

    def iter(self, iter_lower_bound: int, iter_higher_bound: int):
        filename_result: str = self.create_file(iter_lower_bound, iter_higher_bound)

        for m in self.topic['item']:
            print(f'm: {m}')
            for i in range(iter_lower_bound, iter_higher_bound + 1):
                print(f'i: {i}')
                file_data: str = f'{self.folder_data}/{m}{self.topic["folder description"]}/{i}'
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

                # MSEMA
                start_time = time.time()
                result['MSEMA'] = msema_rb_ra(file_data)
                print("--- %s min MSEMA ---" % round((time.time() - start_time) / 60, 3))

                # Baseline
                start_time = time.time()
                result['Baseline'] = intuitive_resource_allocation(file_data)
                print("--- %s min Base ---" % round((time.time() - start_time) / 60, 3))

                with open(filename_result, 'ab+') as f:
                    pickle.dump({f'{m}{self.topic["folder description"]}': result}, f)
        return True

    def create_file(self, iter_lower_bound: int, iter_higher_bound: int) -> str:
        assert self.folder_graph != '', 'Run new_directory first.'

        filename_result: str = f'{self.folder_graph}/result{iter_lower_bound}-{iter_higher_bound}.P'
        with open(filename_result, 'wb') as f:
            pickle.dump(self.parameter, f)
        return filename_result

    def new_directory(self):
        self.folder_graph: str = f'{os.path.dirname(__file__)}/graph/{self.folder_data}/gNB{self.parameter["gNB MCS"][0]}{self.parameter["gNB MCS"][1]}_eNB{self.parameter["eNB MCS"][0]}{self.parameter["eNB MCS"][1]}'

        if os.path.exists(self.folder_graph):
            return True
        else:
            os.makedirs(self.folder_graph)

        # copy data parameter
        from shutil import copyfile
        copyfile(
            f'{os.path.dirname(__file__)}/data/{self.folder_data}/{self.topic["item"][-1]}{self.topic["folder description"]}/parameter_data.txt',
            f'{os.path.dirname(__file__)}/graph/{self.folder_data}/parameter_data.txt')

    def gen_txt_parameter(self):
        assert self.folder_graph != '', 'Run new_directory first.'

        with open(f'{self.folder_graph}/parameter_iteration.txt', 'w') as f:
            json.dump(self.parameter, f)

    @property
    def parameter(self) -> Dict[str, Any]:
        parameter = {'iteration': self.iteration,
                     self.topic['topic']: self.topic['item'],
                     'data folder': self.folder_data,
                     'gNB MCS': [G_MCS.get_worst().name, G_MCS.get_best().name],
                     'eNB MCS': [E_MCS.get_worst().name, E_MCS.get_best().name]}
        return parameter
