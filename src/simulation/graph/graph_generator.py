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
from src.resource_allocation.ds.util_enum import UEType
from src.simulation.graph.util_graph import bar_chart, line_chart, scatter_chart


class GraphGenerator:
    def __init__(self, times: int, folder: str):
        assert times > 0
        self.times: int = times  # TODO: shouldn't be a input value. len(output_data['iter'][algo])
        self.folder: str = folder
        if isinstance(folder, str):
            self.output_file_path: str = f'{os.path.dirname(__file__)}/{folder}'
            if not os.path.exists(self.output_file_path):
                os.makedirs(self.output_file_path)
        elif isinstance(folder, list):
            self.output_file_path = []
            for i, f in enumerate(folder):
                self.output_file_path.append(f'{os.path.dirname(__file__)}/{f}')
                if not os.path.exists(self.output_file_path[i]):
                    os.makedirs(self.output_file_path[i])

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
        x_label = 'The number of layer in a gNB'
        y_label = 'Percentage(%)'
        bar_chart('Frame used', x_label, x_labels, y_label, averaged_data,
                  f'{self.output_file_path}/{x_label}_{y_label}', self._parameter())

    def gen_deployment(self, data_file_path: str):
        with open(data_file_path, 'rb') as f:
            pickle.load(f)  # TODO: new a empty pickle
            while True:
                try:
                    output_data: Dict[str, Any] = self.read_data(pickle.load(f))
                    for algo in output_data['algo']:
                        x = []
                        y = []
                        color = []
                        gnb: GNodeB = output_data['iter'][algo][0][0]
                        gnb_radius = gnb.radius
                        gnb_coordinate = (gnb.coordinate.x, gnb.coordinate.y)
                        enb: ENodeB = output_data['iter'][algo][0][1]
                        enb_radius = enb.radius
                        enb_coordinate = (enb.coordinate.x, enb.coordinate.y)
                        x.extend([gnb_coordinate[0], enb_coordinate[0]])
                        y.extend([gnb_coordinate[1], enb_coordinate[1]])
                        color.extend(['r'] * 2)
                        for data in output_data['iter'][algo]:
                            assert data[0].radius == gnb_radius and data[1].radius == enb_radius
                            assert (data[0].coordinate.x, data[0].coordinate.y) == gnb_coordinate and (
                                    (data[1].coordinate.x, data[1].coordinate.y) == enb_coordinate)
                            due: List[DUserEquipment] = data[2]
                            gue: List[GUserEquipment] = data[3]
                            eue: List[EUserEquipment] = data[4]
                            x, y, color = self._ue_deployment([due, gue, eue], x, y, color)

                        assert len(x) == len(y) == len(color)
                        scatter_chart(f'The deployment of {output_data["max_layer"]} gNBs, eNBs, and UEs({algo})', x, y,
                                      color, (-enb_radius, gnb_coordinate[0] + gnb_radius), (-enb_radius, enb_radius),
                                      f'{self.output_file_path}/deployment_{output_data["max_layer"]}_{algo}',
                                      self._parameter())  # TODO: x_lim, y_lim不要寫死
                except EOFError:
                    break

    @staticmethod
    def _ue_deployment(all_ue: List[Union[List[DUserEquipment], List[GUserEquipment], List[EUserEquipment]]],
                       x: List[float], y: List[float], color: List[str]) -> Tuple[List[float], List[float], List[str]]:
        c = ['b', 'g', 'm']
        for i, ue_list in enumerate(all_ue):
            for ue in ue_list:
                if ue.is_allocated:
                    x.append(ue.coordinate.x)
                    y.append(ue.coordinate.y)
                    color.append(c[i])
        return x, y, color

    def gen_avg_allocated_ue(self, data_file_path: List[str]):
        raw_data: Dict[str, Dict[str, Dict[str, Dict[str, int]]]] = dict()
        #         variation layer     algo       ue       avg_allo_ue
        ue_str: List[str] = ['due', 'gue', 'eue', 'due-cross-bs']

        for variation in self.folder:
            variation_file_path = data_file_path[0] + variation + data_file_path[1]
            with open(variation_file_path, 'rb') as f:
                raw_data[variation] = dict()
                pickle.load(f)  # TODO: new a empty pickle
                while True:
                    try:
                        output_data: Dict[str, Any] = self.read_data(pickle.load(f))
                        raw_data[variation][output_data['max_layer']] = dict()
                        for algo in output_data['algo']:
                            raw_data[variation][output_data['max_layer']][algo] = dict()
                            for i in ue_str:
                                raw_data[variation][output_data['max_layer']][algo][i] = 0
                            for data in output_data['iter'][algo]:
                                due: List[DUserEquipment] = data[2]
                                gue: List[GUserEquipment] = data[3]
                                eue: List[EUserEquipment] = data[4]
                                raw_data = self.count_allocated_ue([due, gue, eue],
                                                                   raw_data, variation, output_data['max_layer'], algo)
                                raw_data = self.count_due_cross_bs(due,
                                                                   raw_data, variation, output_data['max_layer'], algo)
                            for i in ue_str:
                                raw_data[variation][output_data['max_layer']][algo][i] /= len(output_data['iter'][algo])
                    except EOFError:
                        break
        folder: str = ''
        for f in self.folder:
            folder += f
        for layer in next(iter(raw_data.values())):
            for algo in next(iter(raw_data.values()))[layer]:
                chart_data: Dict[str, List[int]] = {s: [] for s in ue_str}
                for variation in raw_data:
                    for s in ue_str:
                        chart_data[s].append(raw_data[variation][layer][algo][s])
                        # {'due': [4.1, 12.9, 53.5], 'gue': [58.0, 190.4, 39.2], 'eue': [57.0, 117.8, 76.7], 'due-cross-bs': [0.0, 0.0, 2.0]}
                bar_chart(f'The number of allocated UE for {algo} of {layer}',
                          x_label='Variation of radius', x_tick_labels=self.folder,
                          y_label='Number of UEs', data=chart_data,
                          output_file_path=f'{os.path.dirname(__file__)}/{folder}/avg_allocated_ue/{algo}_{layer}',
                          parameter=self._parameter())

    @staticmethod
    def count_allocated_ue(all_ue: List[Union[List[DUserEquipment], List[GUserEquipment], List[EUserEquipment]]],
                           raw_data: Dict[str, Dict[str, Dict[str, Dict[str, int]]]], variation, max_layer, algo
                           ) -> Dict[str, Dict[str, Dict[str, Dict[str, int]]]]:
        for ue_list in all_ue:
            if ue_list[0].ue_type == UEType.D:
                ue_str = 'due'
            elif ue_list[0].ue_type == UEType.G:
                ue_str = 'gue'
            elif ue_list[0].ue_type == UEType.E:
                ue_str = 'eue'
            else:
                raise AssertionError
            for ue in ue_list:
                raw_data[variation][max_layer][algo][ue_str] += 1 if ue.is_allocated else 0
        return raw_data

    @staticmethod
    def count_due_cross_bs(due_list: List[DUserEquipment],
                           raw_data: Dict[str, Dict[str, Dict[str, Dict[str, int]]]], variation, max_layer, algo
                           ) -> Dict[str, Dict[str, Dict[str, Dict[str, int]]]]:
        for due in due_list:
            if due.is_allocated:
                raw_data[variation][max_layer][algo]['due-cross-bs'] += 1 if due.cross_nb else 0
        return raw_data

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
