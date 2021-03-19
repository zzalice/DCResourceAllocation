import json
import os
import pickle
from typing import Any, Dict, List, Tuple, Union

from src.resource_allocation.algo.utils import bpframe_to_mbps, calc_system_throughput_uncategorized_ue
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.resource_allocation.ds.ue import UserEquipment
from src.resource_allocation.ds.util_enum import UEType
from src.simulation.graph.util_graph import bar_chart, line_chart, scatter_chart


class GraphGenerator:
    def __init__(self, folder_result: Tuple[str], graph_type: str, **kwargs):
        self.output_file_path: List[str] = []
        for f in folder_result:
            self.output_file_path.append(f'{os.path.dirname(__file__)}/{f}')

        # parameters for graph generating usage
        self.collect_data = {}
        self.count_iter = {}
        if graph_type == 'sys throughput - layer':
            self.frame_time: int = -1

        # main
        for file_path in self.output_file_path:
            file_result: str = f'{file_path}/result.P'
            with open(file_result, 'rb') as f:
                information: Dict = pickle.load(f)
                assert kwargs['iteration'] <= information['iteration']
                for l in kwargs['layers']:
                    assert l in information['layers']

                while True:
                    try:
                        #                 layer     algo
                        algo_result: Dict[str, Dict[str, Tuple[GNodeB, ENodeB, List[
                            DUserEquipment], List[GUserEquipment], List[EUserEquipment]]]] = pickle.load(f)
                        if graph_type == 'sys throughput - layer':
                            self.collect_sys_throughput_layer(kwargs['iteration'], algo_result)
                        elif graph_type == 'used percentage':
                            self.collect_used_percentage(kwargs['iteration'], algo_result)
                        elif graph_type == 'deployment':
                            self.collect_depolyment(kwargs['iteration'], algo_result)
                        elif graph_type == 'allocated ue':
                            self.collect_allocated_ue(kwargs['iteration'], algo_result)
                    except EOFError:
                        if graph_type == 'sys throughput - layer':
                            self.gen_sys_throughput_layer(kwargs['iteration'], kwargs['layers'], file_path)
                        elif graph_type == 'used percentage':
                            self.gen_used_percentage(kwargs['iteration'], kwargs['layers'], file_path)
                        elif graph_type == 'deployment':
                            self.gen_deployment(kwargs['iteration'], kwargs['layers'], file_path)
                        elif graph_type == 'allocated ue':
                            self.gen_allocated_ue(kwargs['iteration'], kwargs['layers'], file_path)
                        break

    # ==================================================================================================================
    def collect_sys_throughput_layer(self, iteration: int, result: Dict[str, Dict[str, Tuple[GNodeB, ENodeB, List[
        DUserEquipment], List[GUserEquipment], List[EUserEquipment]]]]):
        # collect_data: Dict[str, Dict[str, float]
        #                    layer     algo sum of system throughput
        self.frame_time: int = next(iter(next(iter(result.values())).values()))[0].frame.frame_time

        for layer in result:  # only one
            l: int = int(layer.replace('layer', ''))
            self._increase_iter(l, iteration)
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

        line_chart('',
                   'The number of gNB layer', ([str(i) for i in layers]),
                   'System throughput(Mbps)', avg_system_throughput,
                   output_file_path, {'iteration': iteration})

    # ==================================================================================================================
    def collect_used_percentage(self, iteration: int, result: Dict[str, Dict[str, Tuple[GNodeB, ENodeB, List[
        DUserEquipment], List[GUserEquipment], List[EUserEquipment]]]]):
        # collect_data: Dict[str, Dict[str, [int,        int]]
        #                    layer     algo  used BU     number of BU in gNBs
        for max_layer_str in result:  # only one
            l: int = int(max_layer_str.replace('layer', ''))
            self._increase_iter(l, iteration)
            for algo in result[max_layer_str]:
                gnb: GNodeB = result[max_layer_str][algo][0]
                assert l == gnb.frame.max_layer

                count_used_bu: int = 0
                for layer in range(gnb.frame.max_layer):
                    for i in gnb.frame.layer[layer].bu_status:
                        for j in i:
                            count_used_bu += 1 if j else 0

                count_bu: int = gnb.frame.frame_time * gnb.frame.frame_freq * gnb.frame.max_layer
                try:
                    self.collect_data[l][algo][0] += count_used_bu
                    self.collect_data[l][algo][1] += count_bu
                except KeyError:
                    self.collect_data[l][algo] = [count_used_bu, count_bu]

    def gen_used_percentage(self, iteration: int, layers: List[int], output_file_path: str):
        # x_labels: List[str]
        #                max layer
        #           e.g. ['1 layer', '2 layer', '3 layer']
        # percentages: Dict[str, List[float]]
        #                   algo      percentage
        #              e.g. {'DC-RA': [0.98, 0.55, 0.32], 'Intuitive': [0.97, 0.44, 0.22]}
        x_labels: List[str] = []
        percentages: Dict[str, List[float]] = {}
        for layer in self.collect_data:
            if layer in layers:
                x_labels.append(str(layer) + ' layer')
                for algo in self.collect_data[layer]:
                    percent: float = self.collect_data[layer][algo][0] / self.collect_data[layer][algo][1]
                    assert 0.0 <= percent <= 1.0, 'Error in counting used BU.'
                    try:
                        percentages[algo].append(percent)
                    except KeyError:
                        percentages[algo] = [percent]

        bar_chart('Frame used',
                  'The number of layer in a gNB', x_labels,
                  'Percentage(%)', percentages,
                  output_file_path, {'iteration': iteration})

    # ==================================================================================================================
    def collect_depolyment(self, iteration: int, result: Dict[str, Dict[str, Tuple[GNodeB, ENodeB, List[
        DUserEquipment], List[GUserEquipment], List[EUserEquipment]]]]):
        # collect_data: Dict[str, Dict[str, Dict[str, Any]]
        #                    layer     algo      nb   [nb_radius, nb_coordinate]
        #                                        ue   [[ue.x, ue.y], ...]
        for layer in result:  # only one
            l: int = int(layer.replace('layer', ''))
            self._increase_iter(l, iteration)
            for algo in result[layer]:
                try:
                    self.collect_data[l][algo]['allocated_ue'].extend(self.purge_ue(
                        result[layer][algo][2] + result[layer][algo][3] + result[layer][algo][4]))
                except KeyError:
                    self.collect_data[l][algo] = {
                        'nb_info': [result[layer][algo][0].radius,  # gNB
                                    [result[layer][algo][0].coordinate.x, result[layer][algo][0].coordinate.y],
                                    result[layer][algo][1].radius,  # eNB
                                    [result[layer][algo][1].coordinate.x, result[layer][algo][1].coordinate.y]
                                    ],
                        'allocated_ue': self.purge_ue(
                            result[layer][algo][2] + result[layer][algo][3] + result[layer][algo][4])}
        return True

    @staticmethod
    def purge_ue(ue_list: List[UserEquipment]) -> List[Tuple[UEType, float, float]]:
        purged_ue: List[Tuple[UEType, float, float]] = []
        for ue in ue_list:
            if ue.is_allocated:
                purged_ue.append((ue.ue_type, ue.coordinate.x, ue.coordinate.y))
        return purged_ue

    def gen_deployment(self, iteration: int, layers: List[int], output_file_path: str):
        for layer in self.collect_data:
            if layer in layers:
                for algo in self.collect_data[layer]:
                    gnb_radius: float = self.collect_data[layer][algo]['nb_info'][0]
                    gnb_coordinate: List[float] = self.collect_data[layer][algo]['nb_info'][1]
                    enb_radius: float = self.collect_data[layer][algo]['nb_info'][2]
                    enb_coordinate: List[float] = self.collect_data[layer][algo]['nb_info'][3]
                    x = [gnb_coordinate[0], enb_coordinate[0]]
                    y = [gnb_coordinate[1], enb_coordinate[1]]
                    color = ['r'] * 2
                    x, y, color = self._ue_deployment(self.collect_data[layer][algo]['allocated_ue'], x, y, color)
                    scatter_chart(f'The deployment of {layer} layer gNBs, eNBs, and UEs({algo})',
                                  x, y, color,
                                  (-enb_radius, gnb_coordinate[0] + gnb_radius), (-enb_radius, enb_radius),
                                  f'{output_file_path}/deployment_{layer}_{algo}',
                                  {'iteration': iteration})

    @staticmethod
    def _ue_deployment(all_ue: List[Tuple[UEType, float, float]],
                       x: List[float], y: List[float], color: List[str]) -> Tuple[List[float], List[float], List[str]]:
        c = ['b', 'g', 'm']
        for ue in all_ue:
            x.append(ue[1])
            y.append(ue[2])
            if ue[0] == UEType.D:
                color.append(c[0])
            elif ue[0] == UEType.G:
                color.append(c[1])
            elif ue[0] == UEType.E:
                color.append(c[2])
            else:
                raise AssertionError
        return x, y, color

    # ==================================================================================================================
    def collect_allocated_ue(self, iteration: int, result: Dict[str, Dict[str, Tuple[GNodeB, ENodeB, List[
        DUserEquipment], List[GUserEquipment], List[EUserEquipment]]]]):
        # collect_data: Dict[str, Dict[str, Dict[str, int]]
        #                    layer     algo,     ue   num of allocated ue
        for layer in result:  # only one
            l: int = int(layer.replace('layer', ''))
            self._increase_iter(l, iteration)
            for algo in result[layer]:
                try:
                    self.count_allocated_ue(result[layer][algo][2], result[layer][algo][3], result[layer][algo][4],
                                            self.collect_data[l][algo])
                except KeyError:
                    self.collect_data[l][algo] = {'dUE_in_gNB': 0, 'dUE_in_eNB': 0, 'dUE_cross_BS': 0,
                                                  'eUE': 0, 'gUE': 0}
                    self.count_allocated_ue(result[layer][algo][2], result[layer][algo][3], result[layer][algo][4],
                                            self.collect_data[l][algo])

    @staticmethod
    def count_allocated_ue(due_list: List[DUserEquipment], gue_list: List[GUserEquipment],
                           eue_list: List[EUserEquipment], collect_data):
        for due in due_list:
            if due.cross_nb:
                collect_data['dUE_cross_BS'] += 1
            elif len(due.gnb_info.rb) > 0:
                collect_data['dUE_in_gNB'] += 1
            elif len(due.enb_info.rb) > 0:
                collect_data['dUE_in_eNB'] += 1
        for gue in gue_list:
            if gue.is_allocated:
                collect_data['gUE'] += 1
        for eue in eue_list:
            if eue.is_allocated:
                collect_data['eUE'] += 1

    def gen_allocated_ue(self, iteration: int, layers: List[int], output_file_path: str):
        for layer in self.collect_data:
            if layer in layers:
                for algo in self.collect_data[layer]:
                    self.collect_data[layer][algo]['total'] = 0
                    for ue in self.collect_data[layer][algo]:
                        if ue == 'total':
                            continue
                        self.collect_data[layer][algo][ue] /= iteration
                        self.collect_data[layer][algo]['total'] += self.collect_data[layer][algo][ue]
        with open(f'{output_file_path}/avg_num_of_allocated_ue.txt', 'w') as f:
            import pprint
            f.write(pprint.pformat(self.collect_data))

    # ==================================================================================================================

    def _increase_iter(self, key: Union[str, int], iteration: int):
        try:
            if self.count_iter[key] >= iteration:
                return True
            else:
                self.count_iter[key] += 1
        except KeyError:
            self.count_iter[key] = 1
            self.collect_data[key] = {}

    @staticmethod
    def _read_data(pickle_data: Dict[str, Dict[str, List[
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
