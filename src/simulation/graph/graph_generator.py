import math
import os
import pickle
from typing import Any, Dict, List, Tuple, Union

from src.resource_allocation.algo.utils import bpframe_to_mbps, calc_system_throughput_uncategorized_ue
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.resource_allocation.ds.util_enum import UEType
from src.simulation.graph.util_graph import bar_chart, line_chart, scatter_chart


class GraphGenerator:
    def __init__(self, folder_result: Tuple[str], graph_type: str, *args, **kwargs):
        self.output_file_path: List[str] = []
        for f in folder_result:
            self.output_file_path.append(f'{os.path.dirname(__file__)}/{f}')

        # parameters for graph generating usage
        self.collect_data = {}
        self.count_iter = {}
        self.frame_time: int = -1

        # main
        for file_path in self.output_file_path:
            file_result: str = f'{file_path}/result_iter_layer.P'
            with open(file_result, 'rb') as f:
                information: Dict = pickle.load(f)
                while True:
                    try:
                        algo_result: Dict[
                            str, Dict[str, Tuple[GNodeB, ENodeB, List[DUserEquipment], List[GUserEquipment], List[
                                EUserEquipment]]]] = pickle.load(f)
                        if graph_type == 'sys throughput - layer':
                            self.collect_sys_throughput_layer(kwargs['iteration'], algo_result)
                    except EOFError:
                        if graph_type == 'sys throughput - layer':
                            self.gen_sys_throughput_layer(kwargs['iteration'], kwargs['layers'], file_path)
                        break

    def collect_sys_throughput_layer(self, iteration: int, result: Dict[str, Dict[str, Tuple[GNodeB, ENodeB, List[
                                                    DUserEquipment], List[GUserEquipment], List[EUserEquipment]]]]):
        #                                                               layer     algo
        # collect: Dict[str, Dict[str, Tuple[gNB, enb, List[dUE], List[gUE], List[eUE]]]]
        #               layer     algo
        self.frame_time: int = next(iter(next(iter(result.values())).values()))[0].frame.frame_time

        for layer in result:
            l: int = int(layer.replace('layer', ''))
            try:
                if self.count_iter[l] >= iteration:
                    return True
                else:
                    self.count_iter[l] += 1
            except KeyError:
                self.count_iter[l] = 1
                self.collect_data[l] = {}

            for algo in result[layer]:
                try:
                    self.collect_data[l][algo] += calc_system_throughput_uncategorized_ue(
                        result[layer][algo][2] + result[layer][algo][3] + result[layer][algo][4])
                except KeyError:
                    self.collect_data[l][algo] = calc_system_throughput_uncategorized_ue(
                        result[layer][algo][2] + result[layer][algo][3] + result[layer][algo][4])
        return True

    def gen_sys_throughput_layer(self, iteration: int, layers: List[int], output_file_path: str):
        for i in range(len(layers) - 1):
            assert layers[i] < layers[i + 1], 'Not in order.'
        avg_system_throughput: Dict[str, List[float]] = {algo: [] for algo in next(iter(self.collect_data.values()))}
        #                           algo      avg throughput of each layer

        for layer in layers:
            for algo in self.collect_data[layer]:
                assert self.count_iter[layer] == iteration
                self.collect_data[layer][algo] /= iteration
                assert self.frame_time > 0
                self.collect_data[layer][algo] = bpframe_to_mbps(self.collect_data[layer][algo], self.frame_time)
                avg_system_throughput[algo].append(self.collect_data[layer][algo])

        line_chart('', 'The number of gNB layer', ([str(i) for i in layers]), 'System throughput(Mbps)',
                   avg_system_throughput, output_file_path, {'iteration': iteration})

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
