import json
import math
import os
import threading
import time
from typing import Any, Callable, Dict, List, Tuple

from main import dc_resource_allocation
from main_frsa import frsa
from main_intuitive import intuitive_resource_allocation
from main_msema import msema_rb_ra
from src.resource_allocation.ds.util_enum import E_MCS, G_MCS


class IterateAlgo:
    def __init__(self, iteration: int, algorithm: Tuple[str, ...], folder_data: str, to_start_over: bool = False):
        assert iteration > 0
        self.iteration: int = iteration
        self.algorithm: Tuple[str, ...] = algorithm
        self.folder_data: str = folder_data
        self.to_start_over: bool = to_start_over

        self.num_thread: int = 2
        assert self.num_thread > 0
        self.topic: Dict[str, Any] = {'topic': '', 'item': [], 'folder description': ''}
        self.folder_graph: str = ''
        self.exist_result: List[str] = []   # the iteration of algorithm that has already run

    def iter_layer(self, layers: List[int]):
        self.topic: Dict[str, Any] = {'topic': 'layers', 'item': layers, 'folder description': 'layer'}
        self.large_iter()

    def iter_ue(self, total_ue: List[int]):
        self.topic: Dict[str, Any] = {'topic': 'total ue', 'item': total_ue, 'folder description': 'ue'}
        self.large_iter()

    def iter_due_to_all(self, due_proportion: List[int]):
        self.topic: Dict[str, Any] = {'topic': 'due to all', 'item': due_proportion, 'folder description': 'p_due'}
        self.large_iter()

    def iter_gnb_bw(self, gnb_bw: List[int]):
        self.topic: Dict[str, Any] = {'topic': 'gNB BW', 'item': gnb_bw, 'folder description': 'bw_gnb'}
        self.large_iter()

    def iter_cochannel(self, cochannel_bw: List[int]):
        self.topic: Dict[str, Any] = {'topic': 'co-channel BW', 'item': cochannel_bw, 'folder description': 'bw_co'}
        self.large_iter()

    def large_iter(self):
        self.new_directory()
        threads = []
        program_start_time = time.time()
        for i in range(math.ceil(self.iteration / self.num_thread)):
            iter_lower_bound = i * self.num_thread
            iter_higher_bound = iter_lower_bound + (self.num_thread - 1) if iter_lower_bound + (self.num_thread - 1) < self.iteration else self.iteration - 1
            t = threading.Thread(target=self.iter, args=(iter_lower_bound, iter_higher_bound))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
        print("--- Total %s min ---" % round((time.time() - program_start_time) / 60, 1))
        self.gen_txt_parameter()

    def iter(self, iter_lower_bound: int, iter_higher_bound: int):
        for m in self.topic['item']:
            for i in range(iter_lower_bound, iter_higher_bound + 1):
                file_data: str = f'{self.folder_data}/{m}{self.topic["folder description"]}/{i}'
                if 'DC-RA' in self.algorithm:
                    self.run_algorithm('DC-RA', dc_resource_allocation, m, i, file_data)
                if 'FRSA' in self.algorithm:
                    self.run_algorithm('FRSA', frsa, m, i, file_data)
                if 'MSEMA' in self.algorithm:
                    self.run_algorithm('MSEMA', msema_rb_ra, m, i, file_data)
                if 'Baseline' in self.algorithm:
                    self.run_algorithm('Baseline', intuitive_resource_allocation, m, i, file_data)
        return True

    def run_algorithm(self, algo_name: str, func_algo: Callable, topic: int, iteration: int, file_data: str):
        filename: str = f'topic{topic}{self.topic["folder description"]}_iter{iteration}_algo{algo_name}.json'
        if filename in self.exist_result:
            return True
        start_time = time.time()
        result = func_algo(file_data)
        json_result = [result[0].to_json(),
                       result[1].to_json(),
                       [due.to_json() for due in result[2]],
                       [gue.to_json() for gue in result[3]],
                       [eue.to_json() for eue in result[4]]]
        print(f'm:{topic} i:{iteration} --- {round((time.time() - start_time) / 60, 3)} min {algo_name} ---')

        with open(f'{self.folder_graph}/{filename}', 'w') as f:
            json.dump({f'{topic}{self.topic["folder description"]}': {algo_name: json_result}}, f)

    def new_directory(self):
        self.folder_graph: str = f'{os.path.dirname(__file__)}/graph/{self.folder_data}'
        self.folder_graph += f'/gNB{self.parameter["gNB MCS"][0]}{self.parameter["gNB MCS"][1]}_eNB{self.parameter["eNB MCS"][0]}{self.parameter["eNB MCS"][1]}'
        self.folder_graph += f'/result'

        if os.path.exists(self.folder_graph):
            if not self.to_start_over:  # to continue
                self.exist_result: List[str] = next(os.walk(self.folder_graph))[2]
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


class OneIterationAlgo:
    def __init__(self, folder_data: str, folder_topic: str, iteration_index: int, algorithm_name: str):
        self.folder_data: str = folder_data  # e.g. '0507-164827PDUE_5MHz_qos800'
        self.topic: str = folder_topic  # e.g. '80p_due'
        self.iter_idx: int = iteration_index  # e.g. 59
        assert algorithm_name in ['DC-RA', 'FRSA', 'MSEMA', 'Baseline'], 'The name of the algorithm not found.'
        self.algorithm: str = algorithm_name

    def run(self):
        if self.algorithm == 'DC-RA':
            self._run_one_iter(dc_resource_allocation)
        elif self.algorithm == 'FRSA':
            self._run_one_iter(frsa)
        elif self.algorithm == 'MSEMA':
            self._run_one_iter(msema_rb_ra)
        elif self.algorithm == 'Baseline':
            self._run_one_iter(intuitive_resource_allocation)
        else:
            raise AssertionError('Algorithm name not found.')

    def _run_one_iter(self, func_algo: Callable):
        file_data: str = f'{self.folder_data}/{self.topic}/{self.iter_idx}'
        folder_result: str = f'{os.path.dirname(__file__)}/graph/{self.folder_data}'
        folder_result += f'/gNB{G_MCS.get_worst().name}{G_MCS.get_best().name}_eNB{E_MCS.get_worst().name}{E_MCS.get_best().name}'
        folder_result += f'/result'
        self.check_folder_exist(folder_result)
        file_result: str = f'topic{self.topic}_iter{self.iter_idx}_algo{self.algorithm}.json'

        result = func_algo(file_data)
        json_result = [result[0].to_json(),
                       result[1].to_json(),
                       [due.to_json() for due in result[2]],
                       [gue.to_json() for gue in result[3]],
                       [eue.to_json() for eue in result[4]]]
        with open(f'{folder_result}/{file_result}', 'w') as f:
            json.dump({f'{self.topic}': {self.algorithm: json_result}}, f)

    @staticmethod
    def check_folder_exist(folder_path: str):
        if not os.path.exists(folder_path):
            raise AssertionError('Wrong folder.')
