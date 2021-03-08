import math
import os
import pickle
import time
from typing import Any, Dict, List, Tuple, Union

from main import dc_resource_allocation
from main_intuitive import intuitive_resource_allocation
from src.resource_allocation.algo.utils import bpframe_to_mbps, calc_system_throughput_uncategorized_ue
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.simulation.graph.util_graph import bar_chart, line_chart


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
            pickle.dump('new file', f)  # TODO: new a empty pickle
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

    def gen_used_percentage(self, data_file_path: str):
        x_labels: List[str] = []
        averaged_data: Dict[str, List[Union[int, float]]] = dict()
        with open(data_file_path, 'rb') as f:
            pickle.load(f)  # TODO: new a empty pickle
            while True:
                try:
                    output_data: Dict[str, Any] = self.read_data(pickle.load(f))

                    x_labels.append(output_data['max_layer'])
                    for algo in output_data['algo']:
                        try:
                            averaged_data[algo]
                        except KeyError:
                            averaged_data[algo] = []
                        percent: float = 0.0
                        for data in output_data['iter'][algo]:
                            gnb: GNodeB = data[0]

                            # calculate how many percent of BUs are occupied in the gNB, ONE gNB
                            count_used_bu: int = 0
                            assert 'layer' in output_data['max_layer'], 'Input data error.'
                            max_layer: int = int(output_data['max_layer'].replace('layer', ''))
                            for layer in range(max_layer):
                                for i in gnb.frame.layer[layer].bu_status:
                                    for j in i:
                                        count_used_bu += 1 if j else 0
                            percent += count_used_bu / (gnb.frame.frame_time * gnb.frame.frame_freq * max_layer)

                        averaged_data[algo].append(round(percent / len(output_data['iter'][algo]), 3))
                        assert 0.0 <= averaged_data[algo][-1] <= 1.0 \
                               or math.isclose(averaged_data[algo][-1], 0.0) \
                               or math.isclose(averaged_data[algo][-1], 1)
                except EOFError:
                    break

        bar_chart('Frame used', 'The number of layer in a gNB', x_labels, 'Percentage(%)', averaged_data,
                  self.output_file_path, self._parameter())

    def _run_algo(self, data_set_file_path: str, pickle_file_path: str, result_information: str):
        result: Dict[str, Dict[
            str, List[Tuple[GNodeB, ENodeB, List[DUserEquipment], List[GUserEquipment], List[EUserEquipment]]]]] = {
            result_information: {'DC-RA': [], 'Intuitive': []}}  # TODO: refactor, raw_data_output/input
        for i in range(self.times):
            print(f'i:{i}')

            start_time = time.time()
            result[result_information]['DC-RA'].append(dc_resource_allocation(data_set_file_path + str(i)))
            print("--- %s sec DC-RA ---" % round((time.time() - start_time), 3))

            start_time = time.time()
            result[result_information]['Intuitive'].append(
                intuitive_resource_allocation(data_set_file_path + str(i)))
            print("--- %s sec Intui ---" % round((time.time() - start_time), 3))

        with open(pickle_file_path, 'ab+') as f:
            pickle.dump(result, f)
        return result

    def _parameter(self) -> Dict:
        return {'times': self.times}

    @staticmethod
    def read_data(pickle_data: Dict[str, Dict[str, List[
        Tuple[GNodeB, ENodeB, List[DUserEquipment], List[GUserEquipment], List[EUserEquipment]]]]]
                  ) -> Dict[str, Any]:
        tran_data: Dict[str, Any] = dict()
        tran_data['max_layer']: str = next(iter(pickle_data.items()))[0]  # e.g. '1layer'
        tran_data['iter']: Dict[str, List[
            Tuple[GNodeB, ENodeB, List[DUserEquipment], List[GUserEquipment], List[EUserEquipment]]]
        ] = pickle_data[tran_data['max_layer']]
        # e.g. {'DC-RA': [[gNB, eNB, dUE, gUE, eUE], ...], 'Intuitive': [[gNB, eNB, dUE, gUE, eUE], ...]}
        tran_data['algo']: List[str] = [i for i in tran_data['iter']]  # e.g. ['DC-RA', 'Intuitive']
        return tran_data
