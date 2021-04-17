import os
import pickle
import re
from datetime import datetime
from typing import Any, Dict, List, Tuple, Union

from src.resource_allocation.algo.utils import bpframe_to_mbps, calc_system_throughput, divide_ue
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.frame import BaseUnit
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.resource_allocation.ds.ue import UserEquipment
from src.resource_allocation.ds.util_enum import UEType
from src.simulation.graph.util_graph import bar_chart, bar_chart_grouped_stacked, line_chart, scatter_chart

RESULT = Dict[str, Dict[str, Tuple[GNodeB, ENodeB, List[DUserEquipment], List[GUserEquipment], List[EUserEquipment]]]
]  # layer/ue    algo


class GraphGenerator:
    def __init__(self, folder_result: Tuple[str], graph_type: str, **kwargs):
        self.output_file_path: List[str] = []
        for f in folder_result:
            self.output_file_path.append(f'{os.path.dirname(__file__)}/{f}')

        # parameters for graph generating usage
        self.collect_data = {}
        self.collect_data2 = {}
        self.count_iter = {}
        if graph_type == 'sys throughput - layer' or graph_type == 'increasing ue':
            self.frame_time: int = -1

        # main
        for file_path in self.output_file_path:
            file_result: str = f'{file_path}/result.P'
            with open(file_result, 'rb') as f:
                information: Dict = pickle.load(f)
                assert kwargs['iteration'] <= information['iteration']
                try:
                    for l in kwargs['layers']:
                        assert l in information['layers']
                except KeyError:
                    pass

                while True:
                    try:
                        algo_result: RESULT = pickle.load(f)
                        if graph_type == 'sys throughput - layer' or graph_type == 'due to all':
                            self.collect_sys_throughput(kwargs['iteration'], algo_result)
                        elif graph_type == 'increasing ue':
                            self.collect_sys_throughput(kwargs['iteration'], algo_result, kwargs['collect_unallo_ue'])
                        elif graph_type == 'used percentage':
                            self.collect_used_percentage(kwargs['iteration'], algo_result)
                        elif graph_type == 'deployment':
                            self.collect_deployment(kwargs['iteration'], algo_result)
                        elif graph_type == 'allocated ue' or graph_type == 'total_allocated_ue':
                            self.collect_allocated_ue(kwargs['iteration'], algo_result)
                        elif graph_type == 'NOMA':
                            self.collect_noma(kwargs['iteration'], kwargs['layer_or_ue'], kwargs['algorithm'],
                                              algo_result)
                    except EOFError:
                        if graph_type == 'sys throughput - layer':
                            self.gen_sys_throughput_layer(kwargs['iteration'], kwargs['layers'], file_path)
                        elif graph_type == 'increasing ue':
                            self.gen_sys_throughput_increasing_ue(kwargs['iteration'], kwargs['total_ue'], kwargs['collect_unallo_ue'], file_path)
                        elif graph_type == 'due to all':
                            self.gen_due_to_all(kwargs['iteration'], kwargs['percentage'], file_path)
                        elif graph_type == 'used percentage':
                            self.gen_used_percentage(kwargs['iteration'], kwargs['layers'], file_path)
                        elif graph_type == 'deployment':
                            self.gen_deployment(kwargs['iteration'], kwargs['layers'], file_path)
                        elif graph_type == 'allocated ue':
                            self.gen_allocated_ue(kwargs['iteration'], kwargs['layers'], file_path,
                                                  ue_label=('eUE', 'dUE_in_eNB', 'gUE', 'dUE_in_gNB', 'dUE_cross_BS'))
                        elif graph_type == 'total_allocated_ue':
                            self.gen_allocated_ue(kwargs['iteration'], kwargs['layers'], file_path,
                                                  ue_label=('total',))
                        elif graph_type == 'NOMA':
                            self.gen_noma_overlap_status(kwargs['iteration'], kwargs['layer_or_ue'], kwargs['algorithm'], file_path)
                        break

    # ==================================================================================================================
    def collect_sys_throughput(self, iteration: int, result: RESULT, collect_unallocated_ue: bool = False):
        # collect_data:  Dict[Union[str, int], Dict[str, float]]
        #                          layer/#ue   algo sum of system throughput
        # collect_data2: Dict[Union[str, int], Dict[str, float]]
        #                          layer/#ue   algo sum of #unallocated ue
        self.frame_time: int = next(iter(next(iter(result.values())).values()))[0].frame.frame_time

        for layer_or_total_ue in result:  # only one
            l_or_u: int = int(re.sub('[^0-9]', '', layer_or_total_ue))
            if not self._increase_iter(l_or_u, iteration):
                return True
            for algo in result[layer_or_total_ue]:
                allocated_ue, unallocated_ue = divide_ue(result[layer_or_total_ue][algo][2] +
                                                         result[layer_or_total_ue][algo][3] +
                                                         result[layer_or_total_ue][algo][4])
                try:
                    self.collect_data[l_or_u][algo] += calc_system_throughput(allocated_ue)
                    if collect_unallocated_ue:
                        self.collect_data2[l_or_u][algo] += len(unallocated_ue)
                except KeyError:
                    self.collect_data[l_or_u][algo] = calc_system_throughput(allocated_ue)
                    if collect_unallocated_ue:
                        self.collect_data2[l_or_u][algo] = len(unallocated_ue)
        return True

    def calc_avg_sys_throughput(self, topic: List[int], iteration: int) -> Dict[str, List[float]]:
        avg_system_throughput: Dict[str, List[float]] = {algo: [] for algo in next(iter(self.collect_data.values()))}
        #                           algo      avg throughput of each layer
        for t in topic:
            for algo in self.collect_data[t]:
                assert self.count_iter[t] == iteration
                self.collect_data[t][algo] /= iteration
                assert self.frame_time > 0
                self.collect_data[t][algo] = bpframe_to_mbps(self.collect_data[t][algo], self.frame_time)
                avg_system_throughput[algo].append(self.collect_data[t][algo])
        return avg_system_throughput

    def gen_unallocated_ue(self, total_ue: List[int], iteration: int, output_file_path: str):
        avg_unallocated_ue: Dict[str, List[float]] = {algo: [] for algo in next(iter(self.collect_data2.values()))}
        #                        algo      avg unallocated ue
        for t in total_ue:
            for algo in self.collect_data2[t]:
                self.collect_data2[t][algo] /= iteration
                avg_unallocated_ue[algo].append(self.collect_data2[t][algo])
        bar_chart('',
                  'The number of UE', total_ue,
                  'The number of unallocated UE', avg_unallocated_ue,
                  f'{output_file_path}/unallocatedUE_numOfUE_{datetime.today().strftime("%m%d-%H%M")}',
                  {'iteration': iteration})

    def gen_sys_throughput_layer(self, iteration: int, layers: List[int], output_file_path: str):
        for i in range(len(layers) - 1):
            assert layers[i] < layers[i + 1], 'Not in order.'

        avg_system_throughput: Dict[str, List[float]] = self.calc_avg_sys_throughput(layers, iteration)

        line_chart('',
                   'The number of gNB layer', ([str(i) for i in layers]),
                   'System throughput(Mbps)', avg_system_throughput,
                   output_file_path, {'iteration': iteration})

    def gen_sys_throughput_increasing_ue(self, iteration: int, total_ue: List[int], collect_unallocated_ue: bool,
                                         output_file_path: str):
        avg_system_throughput: Dict[str, List[float]] = self.calc_avg_sys_throughput(total_ue, iteration)

        line_chart('',
                   'Number of UEs', ([str(i) for i in total_ue]),
                   'System throughput(Mbps)', avg_system_throughput,
                   output_file_path, {'iteration': iteration})

        if collect_unallocated_ue:
            self.gen_unallocated_ue(total_ue, iteration, output_file_path)

    def gen_due_to_all(self, iteration: int, due_to_all: List[int], output_file_path: str):
        avg_system_throughput: Dict[str, List[float]] = self.calc_avg_sys_throughput(due_to_all, iteration)

        line_chart('',
                   'The proportion of dUE to total UE', ([str(i / 100) for i in due_to_all]),
                   'System throughput(Mbps)', avg_system_throughput,
                   output_file_path, {'iteration': iteration})

    # ==================================================================================================================
    def collect_used_percentage(self, iteration: int, result: RESULT):
        # collect_data: Dict[str, Dict[str, [int,        int]]
        #                    layer     algo  used BU     number of BU in gNBs
        for max_layer_str in result:  # only one
            l: int = int(max_layer_str.replace('layer', ''))
            if not self._increase_iter(l, iteration):
                return True
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

        x_label: str = 'The number of layer in a gNB'
        y_label: str = 'Frame Usage(%)'
        bar_chart('Frame used', x_label, x_labels, y_label, percentages,
                  f'{output_file_path}/{x_label}_{y_label}_{datetime.today().strftime("%m%d-%H%M")}',
                  {'iteration': iteration})

    # ==================================================================================================================
    def collect_deployment(self, iteration: int, result: RESULT):
        # collect_data: Dict[str, Dict[str, Dict[str, Any]]
        #                    layer     algo      nb   [nb_radius, nb_coordinate]
        #                                        ue   [[ue.x, ue.y], ...]
        for layer in result:  # only one
            l: int = int(layer.replace('layer', ''))
            if not self._increase_iter(l, iteration):
                return True
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
                                  f'{output_file_path}/deployment_{layer}_{algo}_{datetime.today().strftime("%m%d-%H%M")}',
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
    def collect_allocated_ue(self, iteration: int, result: RESULT):
        # collect_data: Dict[str, Dict[str, Dict[str, int]]
        #                    layer     algo,     ue   num of allocated ue
        for layer in result:  # only one
            l: int = int(layer.replace('layer', ''))
            if not self._increase_iter(l, iteration):
                return True
            for algo in result[layer]:
                try:
                    self.count_allocated_ue(result[layer][algo][2], result[layer][algo][3], result[layer][algo][4],
                                            self.collect_data[l][algo])
                except KeyError:
                    self.collect_data[l][algo] = {'dUE_in_gNB': 0, 'dUE_in_eNB': 0, 'dUE_cross_BS': 0,
                                                  'eUE': 0, 'gUE': 0, 'total': 0}
                    self.count_allocated_ue(result[layer][algo][2], result[layer][algo][3], result[layer][algo][4],
                                            self.collect_data[l][algo])

    @staticmethod
    def count_allocated_ue(due_list: List[DUserEquipment], gue_list: List[GUserEquipment],
                           eue_list: List[EUserEquipment], collect_data):
        for due in due_list:
            if due.cross_nb:
                collect_data['dUE_cross_BS'] += 1
                collect_data['total'] += 1
            elif len(due.gnb_info.rb) > 0:
                collect_data['dUE_in_gNB'] += 1
                collect_data['total'] += 1
            elif len(due.enb_info.rb) > 0:
                collect_data['dUE_in_eNB'] += 1
                collect_data['total'] += 1
        for gue in gue_list:
            if gue.is_allocated:
                collect_data['gUE'] += 1
                collect_data['total'] += 1
        for eue in eue_list:
            if eue.is_allocated:
                collect_data['eUE'] += 1
                collect_data['total'] += 1

    def gen_allocated_ue(self, iteration: int, layers: List[int], output_file_path: str,
                         ue_label: Tuple[str, ...],
                         algo_label: Tuple[str, ...] = ('DC-RA', 'FRSA', 'MSEMA', 'Intuitive')):
        """
        :param iteration:
        :param layers: The display order of the number of layers in gNB
        :param output_file_path:
        :param ue_label: The display order of bar stack in the form of Dict name.
        :param algo_label: The display order of algorithm
        """
        collect_data: Dict[str, Dict[int, Dict[str, float]]] = {}
        #                  algo      layer     ue   avg allocated ue
        for layer in self.collect_data:
            if layer in layers:
                for algo in self.collect_data[layer]:
                    for ue in self.collect_data[layer][algo]:
                        self.collect_data[layer][algo][ue] /= iteration
                    try:
                        collect_data[algo][layer] = self.collect_data[layer][algo]
                    except KeyError:
                        collect_data[algo] = {layer: self.collect_data[layer][algo]}

        num_of_allo_ue: Dict[str, List[List[float]]] = {}  # algo(str) -> layers(list) -> UEs(float)
        for algo in algo_label:
            num_of_allo_ue[algo] = []  # layers(list) -> UEs(float)
            for layer in layers:
                num_of_allo_ue[algo].append([])
                for ue in ue_label:
                    num_of_allo_ue[algo][-1].append(collect_data[algo][layer][ue])

        bar_chart_grouped_stacked('The allocated UEs', 'The number of layers in gNB', 'The number of allocated UE',
                                  f'{output_file_path}/num_of_allocated_ue_{datetime.today().strftime("%m%d-%H%M")}',
                                  {'iteration': iteration}, num_of_allo_ue, [str(i) for i in layers], ue_label,
                                  algo_label)

    # ==================================================================================================================
    def collect_noma(self, iteration: int, layer_or_ue: str, algorithm: List[str], result: RESULT):
        # collect_data: Dict[str, List[List[List[List[int]]], ...]]
        #                    algo iter layer freq time CQI index, '0' for empty
        for topic in result:  # only one. e.g. '300ue' or '1layer'
            if topic != layer_or_ue:
                continue
            if not self._increase_iter(topic, iteration):
                return True
            try:
                del self.collect_data[topic]
            except KeyError:
                pass
            for algo in result[topic]:
                if algo not in algorithm:
                    continue
                gnb: GNodeB = result[topic][algo][0]
                try:
                    self.collect_data[algo].append(self.collect_cqi(gnb))
                except KeyError:
                    self.collect_data[algo] = [self.collect_cqi(gnb)]
                try:
                    assert self.collect_data['gnb_info'] == {'max_layer': gnb.frame.max_layer,
                                                             'freq': gnb.frame.frame_freq, 'time': gnb.frame.frame_time
                                                             }, 'The result will be incomparable.'
                except KeyError:
                    self.collect_data['gnb_info'] = {'max_layer': gnb.frame.max_layer,
                                                     'freq': gnb.frame.frame_freq, 'time': gnb.frame.frame_time}

    @staticmethod
    def collect_cqi(gnb: GNodeB) -> List[List[List[List[int]]]]:
        cqi: List[List[List[List[int]]]] = [
            [[[] for _ in range(gnb.frame.frame_time)] for _ in range(gnb.frame.frame_freq)] for _ in
            range(gnb.frame.max_layer)]
        for layer in range(gnb.frame.max_layer):
            for freq in range(gnb.frame.frame_freq):
                for time in range(gnb.frame.frame_time):
                    bu: BaseUnit = gnb.frame.layer[layer].bu[freq][time]
                    if bu.within_rb:
                        cqi[layer][freq][time]: int = int(bu.within_rb.mcs.name[3:])
                    else:
                        cqi[layer][freq][time]: int = 0
        return cqi

    def gen_noma_overlap_status(self, iteration: int, layer_or_ue: str, algorithm: List[str], output_file_path: str):
        assert self.collect_data, "Can't find layer_or_ue."

        # X: The overlapped layer, 0 ~ frame.max_layer. Y: The number of BU / the number of BU in a layer, float
        data_count_layer: Dict[str, List[int]] = {}
        #                      algo layer(count overlapped UE)
        # X: The overlapped layer, 0 ~ frame.max_layer. Y: The number of BU using curtain CQI
        data_count_bu: Dict[str, List[List[int]]] = {}
        #                   algo layer CQI
        gnb_cqi: str = re.search('gNBCQI(\\d+)CQI(\\d+)', output_file_path).group()
        cqi = [int(re.findall('CQI(\\d+)', gnb_cqi).pop(0)), int(re.findall('CQI(\\d+)', gnb_cqi).pop(1))]

        # data
        for algo in self.collect_data:
            if algo not in algorithm:
                continue
            data_count_layer[algo] = [0 for _ in range(self.collect_data['gnb_info']['max_layer'] + 1)]
            data_count_bu[algo] = [[0 for _ in range(cqi[1] - cqi[0] + 1)] for _ in
                                   range(self.collect_data['gnb_info']['max_layer'])]
            for i in range(iteration):
                frame: List[List[List[List[int]]]] = self.collect_data[algo][i]
                for f in range(self.collect_data['gnb_info']['freq']):
                    for t in range(self.collect_data['gnb_info']['time']):
                        count_lapped: int = 0
                        for l in range(self.collect_data['gnb_info']['max_layer']):
                            if frame[l][f][t] > 0:  # BU in layer l is used
                                count_lapped += 1
                        data_count_layer[algo][count_lapped] += 1  # tmp_count of UEs lap on BU(f, t)

                        for l in range(self.collect_data['gnb_info']['max_layer']):
                            if frame[l][f][t] > 0:  # BU in layer l is used
                                data_count_bu[algo][count_lapped - 1][frame[l][f][t] - 1 - cqi[0]] += 1

            count_bu_flat: int = self.collect_data['gnb_info']['freq'] * self.collect_data['gnb_info']['time']
            for x in range(self.collect_data['gnb_info']['max_layer'] + 1):
                data_count_layer[algo][x] /= (count_bu_flat * iteration)
            for x in range(self.collect_data['gnb_info']['max_layer']):
                for c in range(cqi[1] - cqi[0] + 1):
                    data_count_bu[algo][x][c] /= iteration
            assert False not in [data_count_layer[algo][x] <= 1 for x in range(len(data_count_layer[algo]))], 'Data gathering error.'

        bar_chart(f'Frame overlap of {layer_or_ue}',
                  'The number of overlapped UE', [i for i in range(self.collect_data['gnb_info']['max_layer'] + 1)],
                  'Percentage of BU(%)', data_count_layer,
                  f'{output_file_path}/noma_lap_{layer_or_ue}_{datetime.today().strftime("%m%d-%H%M")}',
                  {'iteration': iteration, 'layer_or_ue': layer_or_ue})
        bar_chart_grouped_stacked(f'The MCS used in a frame of {layer_or_ue}',
                                  'The number of overlapped UE', 'The number BU',
                                  f'{output_file_path}/noma_mcs_{layer_or_ue}_{datetime.today().strftime("%m%d-%H%M")}',
                                  {'iteration': iteration, 'layer_or_ue': layer_or_ue},
                                  data_count_bu,
                                  [str(i + 1) for i in range(self.collect_data['gnb_info']['max_layer'])],
                                  ['CQI' + str(i) for i in range(cqi[0], cqi[1] + 1)], algorithm, color_gradient=True)

    # ==================================================================================================================
    def _increase_iter(self, key: Union[str, int], iteration: int) -> bool:
        """
        Monitors the iteration.
        :param key: Layer, number of UE, etc.
        :param iteration: The limit of the iteration.
        :return: If returns False means the iteration of data collection has reached the request.
        """
        try:
            if self.count_iter[key] >= iteration:
                return False
            else:
                self.count_iter[key] += 1
                return True
        except KeyError:
            self.count_iter[key] = 1
            self.collect_data[key] = {}
            self.collect_data2[key] = {}
            return True
