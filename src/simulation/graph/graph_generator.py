import os
import pickle
from typing import Any, Dict, List, Tuple

from main import dc_resource_allocation
from main_intuitive import intuitive_resource_allocation
from src.resource_allocation.algo.utils import bpframe_to_mbps, calc_system_throughput_uncategorized_ue
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.simulation.graph.util_graph import line_chart
import time


class GraphGenerator:
    def __init__(self, times: int, folder: str):
        assert times > 0
        self.times: int = times
        self.folder: str = folder
        self.output_file_path: str = f'{os.path.dirname(__file__)}/{folder}'
        if not os.path.exists(self.output_file_path):
            os.makedirs(self.output_file_path)

    def gen_sys_throughput_layer(self, layers: List[int]):
        pickle_file_path: str = f'{self.output_file_path}/dcra_intuitive.P'
        with open(pickle_file_path, 'wb') as f:
            pickle.dump('new file', f)
        program_start_time = time.time()

        avg_system_throughput: Dict[str, List[Any]] = {'DC-RA': [0.0 for _ in range(len(layers))],
                                                       'Intuitive': [0.0 for _ in range(len(layers))]}
        for i in range(len(layers)):
            print(f'l: {layers[i]}')
            data_description: str = f'{layers[i]}layer'
            result: Dict[str, Dict[str, List[Tuple[GNodeB, ENodeB, List[DUserEquipment], List[GUserEquipment], List[
                EUserEquipment]]]]
                ] = self._run_algo(f'{self.folder}/{layers[i]}layer/', pickle_file_path, data_description)

            # sum system throughput
            for j in range(self.times):
                for data in avg_system_throughput:
                    avg_system_throughput[data][i] += calc_system_throughput_uncategorized_ue(
                        result[data_description][data][j][2] + result[data_description][data][j][3] +
                        result[data_description][data][j][4])

            # avg system throughput
            for data in avg_system_throughput:
                avg_system_throughput[data][i] /= self.times
                avg_system_throughput[data][i] = bpframe_to_mbps(avg_system_throughput[data][i],
                                                                 result[data_description][data][-1][0].frame.frame_time)

        line_chart('', 'The number of gNB layer', ([str(i) for i in layers]), 'System throughput(Mbps)',
                   avg_system_throughput, self.output_file_path, self._parameter())

        print("--- %s sec ---" % round((time.time() - program_start_time), 3))

    def _run_algo(self, data_set_file_path: str, pickle_file_path: str, result_information: str):
        result: Dict[str, Dict[
            str, List[Tuple[GNodeB, ENodeB, List[DUserEquipment], List[GUserEquipment], List[EUserEquipment]]]]] = {
            result_information: {'DC-RA': [], 'Intuitive': []}}
        for i in range(self.times):
            print(f'i:{i}')

            start_time = time.time()
            result[result_information]['DC-RA'].append(dc_resource_allocation(data_set_file_path + str(i)))
            print("--- %s sec DC-RA ---" % round((time.time() - start_time), 3))

            start_time = time.time()
            result[result_information]['Intuitive'].append(intuitive_resource_allocation(data_set_file_path + str(i)))
            print("--- %s sec Intui ---" % round((time.time() - start_time), 3))

        with open(pickle_file_path, 'ab+') as f:
            pickle.dump(result, f)
        return result

    def _parameter(self) -> Dict:
        return {'times': self.times}
