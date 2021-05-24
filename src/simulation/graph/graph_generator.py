import json
import os
import re
from datetime import datetime
from os import walk
from typing import Dict, List, Tuple, Union

from main_gen_data_bw import GnbMhzBuConvertor
from src.resource_allocation.algo.utils import bpframe_to_mbps, calc_system_throughput_json, divide_ue_json
from src.resource_allocation.ds.util_enum import UEType
from src.simulation.graph.util_graph import bar_chart, bar_chart_grouped_stacked, line_chart, scatter_chart
from src.simulation.utils import fairness_index_json

"""           layer/ue  algo       gNB   eNB   dUE         gUE         eUE"""
RESULT = Dict[str, Dict[str, Tuple[Dict, Dict, List[Dict], List[Dict], List[Dict]]]]


class GraphGenerator:
    def __init__(self, graph_type: str, topic_parameter: List[int], iteration: int, algorithm: Tuple[str, ...],
                 folder_result: Tuple[str], **kwargs):
        self.graph_type: str = graph_type
        self.topic_parameter_int: List[int] = topic_parameter
        self.topic_parameter_str: List[str] = self.append_parameter_description()
        self.iteration: int = iteration
        self.algorithm: Tuple[str, ...] = algorithm
        self.output_file_path: List[str] = []
        for f in folder_result:
            self.output_file_path.append(f'{os.path.dirname(__file__)}/{f}')

        # parameters for graph generating usage
        self.data = {}
        self.data2 = {}
        self.frame_time: int = -1

        self.main(kwargs)

    def main(self, kwargs):
        for file_path in self.output_file_path:
            # gather data
            files_result: List[str] = self.input_result_files(f'{file_path}/result')
            for file_result in files_result:
                self.read_result(f'{file_path}/result', file_result, kwargs)

            # draw graphs
            self.gen_graph(file_path, kwargs)
        return True

    def read_result(self, file_path: str, file_result: str, kwargs):
        result_file_path: str = f'{file_path}/{file_result}'
        try:
            with open(result_file_path, 'r') as f:
                algo_result: RESULT = json.load(f)
                self.collect_data(algo_result, file_path, kwargs)
        except ValueError:
            print(result_file_path)
            raise ValueError
        return True

    def collect_data(self, algo_result: RESULT, file_path: str, kwargs):
        if '- throughput' in self.graph_type:
            try:
                self.collect_sys_throughput(algo_result, kwargs['collect_unallo_ue'])
            except KeyError:
                self.collect_sys_throughput(algo_result)
        elif ' - allocated ue' in self.graph_type:
            self.collect_allocated_ue(algo_result)
        elif self.graph_type == ' - INI':
            self.collect_ini(algo_result)
        elif ' - fairness' in self.graph_type:
            self.collect_fairness(algo_result)
        elif self.graph_type == 'layer - used percentage':
            self.collect_used_percentage(algo_result)
        elif self.graph_type == 'layer - deployment':
            self.collect_deployment(algo_result)
        elif self.graph_type == 'NOMA':
            self.collect_noma(kwargs['layer_or_ue'], kwargs['algorithm'], algo_result)
        elif self.graph_type == 'CQI':
            self.collect_ue_cqi(kwargs['layer_or_ue'], kwargs['algorithm'], algo_result, file_path)
        else:
            raise AssertionError('Undefined graph type.')

    def gen_graph(self, file_path: str, kwargs):
        if '- throughput' in self.graph_type:
            try:
                self.gen_sys_throughput(file_path, kwargs['collect_unallo_ue'])
            except KeyError:
                self.gen_sys_throughput(file_path)
        elif ' - allocated ue' in self.graph_type:
            self.gen_allocated_ue(file_path)
        elif self.graph_type == ' - INI':
            self.gen_ini(file_path)
        elif ' - fairness' in self.graph_type:
            self.gen_fairness(file_path)
        elif self.graph_type == 'layer - used percentage':
            self.gen_used_percentage(file_path)
        elif self.graph_type == 'layer - deployment':
            self.gen_deployment(file_path)
        elif self.graph_type == 'NOMA':
            self.gen_noma_overlap_status(kwargs['algorithm'], file_path)
        elif self.graph_type == 'CQI':
            self.gen_ue_cqi(file_path)
        else:
            raise AssertionError('Undefined graph type.')

    # ==================================================================================================================
    def collect_sys_throughput(self, result: RESULT, collect_unallocated_ue: bool = False):
        # collect_data:  Dict[Union[str, int], Dict[str, float]]
        #                          layer/#ue   algo sum of system throughput
        # collect_data2: Dict[Union[str, int], Dict[str, float]]
        #                          layer/#ue   algo sum of #unallocated ue
        topic, algo = self._topic_and_algo(result)
        self.first_data(topic)

        self.frame_time: int = result[topic][algo][0]['frame']['frame_time']
        allocated_ue, unallocated_ue = divide_ue_json(result[topic][algo][2] + result[topic][algo][3] +
                                                      result[topic][algo][4])
        if algo not in self.data[topic]:  # first time
            self.data[topic][algo] = 0.0
        if collect_unallocated_ue and algo not in self.data2[topic]:  # first time
            self.data2[topic][algo] = 0.0
        self.data[topic][algo] += calc_system_throughput_json(allocated_ue)
        if collect_unallocated_ue:
            self.data2[topic][algo] += len(unallocated_ue)
        return True

    def gen_sys_throughput(self, output_file_path: str, collect_unallocated_ue: bool = False):
        self.gen_avg_sys_throughput(output_file_path)

        if collect_unallocated_ue:
            self.gen_unallocated_ue(output_file_path)

    def gen_avg_sys_throughput(self, output_file_path: str):
        avg_system_throughput: Dict[str, List[float]] = {algo: [] for algo in self.algorithm}
        #                           algo      avg throughput of each layer
        for t in self.topic_parameter_str:
            for algo in self.algorithm:
                self.data[t][algo] /= self.iteration
                assert self.frame_time > 0
                self.data[t][algo] = bpframe_to_mbps(self.data[t][algo], self.frame_time)
                avg_system_throughput[algo].append(self.data[t][algo])

        x_label: str = self._x_label()
        scale_x: List[str] = self._x_scale(self.topic_parameter_int)
        line_chart('', x_label, scale_x,
                   'System throughput(Mbps)', avg_system_throughput,
                   output_file_path, {'iteration': self.iteration})

    def gen_unallocated_ue(self, output_file_path: str):
        avg_unallocated_ue: Dict[str, List[float]] = {algo: [] for algo in next(iter(self.data2.values()))}
        #                        algo      avg unallocated ue
        for t in self.topic_parameter_str:
            for algo in self.data2[t]:
                self.data2[t][algo] /= self.iteration
                avg_unallocated_ue[algo].append(self.data2[t][algo])

        x_label: str = self._x_label()
        scale_x: List[str] = self._x_scale(self.topic_parameter_int)
        y_label: str = 'The number of unallocated UE'
        bar_chart('', x_label, scale_x, y_label, avg_unallocated_ue,
                  output_file_path, {'iteration': self.iteration})

    # ==================================================================================================================
    def collect_used_percentage(self, result: RESULT):
        # collect_data: Dict[str, Dict[str, [int,        int]]
        #                    layer     algo  used BU     number of BU in gNBs
        topic, algo = self._topic_and_algo(result)
        self.first_data(topic)
        gnb: Dict = result[topic][algo][0]

        count_used_bu: int = 0
        for layer in range(gnb['frame']['max_layer']):
            for i in gnb['frame']['layer'][layer]['bu_status']:
                for j in i:
                    count_used_bu += 1 if j else 0

        count_bu: int = gnb['frame']['frame_time'] * gnb['frame']['frame_freq'] * gnb['frame']['max_layer']
        try:
            self.data[topic][algo][0] += count_used_bu
            self.data[topic][algo][1] += count_bu
        except KeyError:
            self.data[topic][algo] = [count_used_bu, count_bu]

    def gen_used_percentage(self, output_file_path: str):
        # percentages: Dict[str, List[float]]
        #                   algo      percentage
        #              e.g. {'DC-RA': [0.98, 0.55, 0.32], 'Baseline': [0.97, 0.44, 0.22]}
        percentages: Dict[str, List[float]] = {algo: [] for algo in self.algorithm}
        for layer in self.topic_parameter_str:
            for algo in self.algorithm:
                percent: float = self.data[layer][algo][0] / self.data[layer][algo][1]
                assert 0.0 <= percent <= 1.0, 'Error in counting used BU.'
                percentages[algo].append(percent)

        x_label: str = self._x_label()
        x_scale: List[str] = self._x_scale(self.topic_parameter_int)
        y_label: str = 'Resource Usage(%)'
        bar_chart('Resource Efficiency', x_label, x_scale, y_label, percentages,
                  output_file_path, {'iteration': self.iteration})

    # ==================================================================================================================
    def collect_deployment(self, result: RESULT):
        # collect_data: Dict[str, Dict[str, Dict[str, Any]]
        #                    layer     algo      nb   [nb_radius, nb_coordinate]
        #                                        ue   [[ue.x, ue.y], ...]
        layer, algo = self._topic_and_algo(result)
        self.first_data(layer)
        try:
            self.data[layer][algo]['allocated_ue'].extend(
                self.purge_ue(result[layer][algo][2] + result[layer][algo][3] + result[layer][algo][4]))
        except KeyError:
            self.data[layer][algo] = {
                'nb_info': [result[layer][algo][0]['radius'],  # gNB
                            [result[layer][algo][0]['x'], result[layer][algo][0]['y']],
                            result[layer][algo][1]['radius'],  # eNB
                            [result[layer][algo][1]['x'], result[layer][algo][1]['y']]
                            ],
                'allocated_ue': self.purge_ue(
                    result[layer][algo][2] + result[layer][algo][3] + result[layer][algo][4])}
        return True

    @staticmethod
    def purge_ue(ue_list: List[Dict]) -> List[Tuple[UEType, float, float]]:
        purged_ue: List[Tuple[UEType, float, float]] = []
        for ue in ue_list:
            if ue['is_allocated']:
                purged_ue.append((ue['ue_type'], ue['x'], ue['y']))
        return purged_ue

    def gen_deployment(self, output_file_path: str):
        for layer in self.topic_parameter_str:
            for algo in self.algorithm:
                gnb_radius: float = self.data[layer][algo]['nb_info'][0]
                gnb_coordinate: List[float] = self.data[layer][algo]['nb_info'][1]
                enb_radius: float = self.data[layer][algo]['nb_info'][2]
                enb_coordinate: List[float] = self.data[layer][algo]['nb_info'][3]
                x = [gnb_coordinate[0], enb_coordinate[0]]
                y = [gnb_coordinate[1], enb_coordinate[1]]
                color = ['r'] * 2
                x, y, color = self._ue_deployment(self.data[layer][algo]['allocated_ue'], x, y, color)
                l: str = layer.replace('layer', '')
                scatter_chart(f'The deployment of {l} layer gNBs, eNBs, and UE({algo})',
                              x, y, color,
                              (-enb_radius, gnb_coordinate[0] + gnb_radius), (-enb_radius, enb_radius),
                              output_file_path, {'iteration': self.iteration})

    @staticmethod
    def _ue_deployment(all_ue: List[Tuple[UEType, float, float]],
                       x: List[float], y: List[float], color: List[str]) -> Tuple[List[float], List[float], List[str]]:
        c = ['b', 'g', 'm']
        for ue in all_ue:
            x.append(ue[1])
            y.append(ue[2])
            if ue[0] == UEType.D.name:
                color.append(c[0])
            elif ue[0] == UEType.G.name:
                color.append(c[1])
            elif ue[0] == UEType.E.name:
                color.append(c[2])
            else:
                raise AssertionError
        return x, y, color

    # ==================================================================================================================
    def collect_allocated_ue(self, result: RESULT):
        # collect_data: Dict[str, Dict[str, Dict[str, int]]
        #                    topic     algo,     ue   num of allocated ue
        topic, algo = self._topic_and_algo(result)
        self.first_data(topic)
        try:
            self.count_allocated_ue(result[topic][algo][2], result[topic][algo][3], result[topic][algo][4],
                                    self.data[topic][algo])
        except KeyError:
            self.data[topic][algo] = {'dUE_in_gNB': 0, 'dUE_in_eNB': 0, 'dUE_cross_BS': 0,
                                      'eUE': 0, 'gUE': 0, 'total': 0}
            self.count_allocated_ue(result[topic][algo][2], result[topic][algo][3], result[topic][algo][4],
                                    self.data[topic][algo])

    @staticmethod
    def count_allocated_ue(due_list: List[Dict], gue_list: List[Dict], eue_list: List[Dict], collect_data):
        for due in due_list:
            if due['cross_nb']:
                collect_data['dUE_cross_BS'] += 1
            elif due['gnb_info']['mcs']:
                assert due['is_allocated'], 'Algorithm error.'
                collect_data['dUE_in_gNB'] += 1
            elif due['enb_info']['mcs']:
                assert due['is_allocated'], 'Algorithm error.'
                collect_data['dUE_in_eNB'] += 1
        for gue in gue_list:
            if gue['is_allocated']:
                collect_data['gUE'] += 1
        for eue in eue_list:
            if eue['is_allocated']:
                collect_data['eUE'] += 1
        collect_data['total'] = collect_data['dUE_cross_BS'] + collect_data['dUE_in_gNB'] + \
            collect_data['dUE_in_eNB'] + collect_data['gUE'] + collect_data['eUE']

    def gen_allocated_ue(self, output_file_path: str):
        for topic in self.topic_parameter_str:
            for algo in self.algorithm:
                for ue in self.data[topic][algo]:
                    self.data[topic][algo][ue] /= self.iteration

        self.gen_all_allocated_ue(output_file_path)
        self.gen_allocated_due(output_file_path)
        self.gen_total_allocated_ue(output_file_path)

    def gen_all_allocated_ue(self, output_file_path: str):
        ue_label = ['eUE', 'dUE_in_eNB', 'gUE', 'dUE_in_gNB',
                    'dUE_cross_BS']  # The display order of bar stack in the form of Dict name.

        num_of_allo_ue: Dict[str, List[List[float]]] = {}  # algo(str) -> layers(list) -> UE(float)
        for algo in self.algorithm:
            num_of_allo_ue[algo] = []  # layers(list) -> UE(float)
            for layer in self.topic_parameter_str:
                num_of_allo_ue[algo].append([])
                for ue in ue_label:
                    num_of_allo_ue[algo][-1].append(self.data[layer][algo][ue])

        x_label: str = self._x_label()
        x_scale: List[str] = self._x_scale(self.topic_parameter_int)
        bar_chart_grouped_stacked('The Allocated UE', x_label, x_scale,
                                  'The Number of Allocated UE', ue_label, num_of_allo_ue,
                                  output_file_path, {'iteration': self.iteration}, self.algorithm)

    def gen_allocated_due(self, output_file_path: str):
        num_of_dc_ue: Dict[str, List[float]] = {algo: [] for algo in self.algorithm}
        for layer in self.topic_parameter_str:
            for algo in self.algorithm:
                num_of_dc_ue[algo].append(self.data[layer][algo]['dUE_cross_BS'])

        x_label: str = self._x_label()
        x_scale: List[str] = self._x_scale(self.topic_parameter_int)
        y_label: str = 'The Number of Allocated DC UE'
        bar_chart('The Allocated Cross BS UE', x_label, x_scale, y_label, num_of_dc_ue,
                  output_file_path, {'iteration': self.iteration})

    def gen_total_allocated_ue(self, output_file_path: str):
        num_of_total_ue: Dict[str, List[float]] = {algo: [] for algo in self.algorithm}
        for layer in self.topic_parameter_str:
            for algo in self.algorithm:
                num_of_total_ue[algo].append(self.data[layer][algo]['total'])

        x_label: str = self._x_label()
        x_scale: List[str] = self._x_scale(self.topic_parameter_int)
        y_label: str = 'The Number of Total Allocated UE'
        bar_chart('The Total Allocated UE', x_label, x_scale, y_label, num_of_total_ue,
                  output_file_path, {'iteration': self.iteration})

    # ==================================================================================================================
    def collect_noma(self, layer_or_ue: List[str], algorithm: List[str], result: RESULT):
        # collect_data: Dict[str, List[List[List[List[int]]], ...]]
        #                    algo iter layer freq time CQI index, '0' for empty
        for topic in result:  # only one. e.g. '300ue' or '1layer'
            if topic not in layer_or_ue:
                raise AssertionError("The json file name doesn't match the data saved inside.")
            for algo in result[topic]:
                if algo not in algorithm:
                    raise AssertionError("The json file name doesn't match the data saved inside.")
                self.first_data(topic)
                gnb: Dict = result[topic][algo][0]
                try:
                    self.data[topic][algo].append(self.collect_cqi(gnb))
                except KeyError:
                    self.data[topic][algo] = [self.collect_cqi(gnb)]
                try:
                    assert self.data[topic]['gnb_info'] == {'max_layer': gnb['frame']['max_layer'],
                                                            'freq': gnb['frame']['frame_freq'],
                                                            'time': gnb['frame']['frame_time']
                                                            }, 'The result will be incomparable.'
                except KeyError:
                    self.data[topic]['gnb_info'] = {'max_layer': gnb['frame']['max_layer'],
                                                    'freq': gnb['frame']['frame_freq'],
                                                    'time': gnb['frame']['frame_time']}

    @staticmethod
    def collect_cqi(gnb: Dict) -> List[List[List[List[int]]]]:
        cqi: List[List[List[List[int]]]] = [
            [[[] for _ in range(gnb['frame']['frame_time'])] for _ in range(gnb['frame']['frame_freq'])] for _ in
            range(gnb['frame']['max_layer'])]
        for layer in range(gnb['frame']['max_layer']):
            for freq in range(gnb['frame']['frame_freq']):
                for time in range(gnb['frame']['frame_time']):
                    bu: Dict = gnb['frame']['layer'][layer]['bu'][freq][time]
                    if bu['within_rb']:
                        cqi[layer][freq][time]: int = bu['within_rb']['mcs']
                    else:
                        cqi[layer][freq][time]: int = 0
        return cqi

    def gen_noma_overlap_status(self, algorithm: List[str], output_file_path: str):
        assert self.data, "Can't find layer_or_ue."

        # X: The overlapped layer, 0 ~ frame.max_layer. Y: The number of BU / the number of BU in a layer, float
        data_count_layer: Dict[str, List[int]] = {}
        #                      algo layer(count overlapped UE)
        # X: The overlapped layer, 0 ~ frame.max_layer. Y: The number of BU using curtain CQI
        data_count_bu: Dict[str, List[List[int]]] = {}
        #                   algo layer CQI
        cqi = self.get_cqi(output_file_path, 'gNB')

        # data
        for topic in self.data:
            for algo in self.data[topic]:
                if algo not in algorithm:
                    continue
                data_count_layer[algo] = [0 for _ in range(self.data[topic]['gnb_info']['max_layer'] + 1)]
                data_count_bu[algo] = [[0 for _ in range(cqi[1] - cqi[0] + 1)] for _ in
                                       range(self.data[topic]['gnb_info']['max_layer'])]
                for i in range(self.iteration):
                    frame: List[List[List[List[int]]]] = self.data[topic][algo][i]
                    for f in range(self.data[topic]['gnb_info']['freq']):
                        for t in range(self.data[topic]['gnb_info']['time']):
                            count_lapped: int = 0
                            for l in range(self.data[topic]['gnb_info']['max_layer']):
                                if frame[l][f][t] > 0:  # BU in layer l is used
                                    count_lapped += 1
                            data_count_layer[algo][count_lapped] += 1  # tmp_count of UE lap on BU(f, t)

                            for l in range(self.data[topic]['gnb_info']['max_layer']):
                                if frame[l][f][t] > 0:  # BU in layer l is used
                                    data_count_bu[algo][count_lapped - 1][frame[l][f][t] - 1 - cqi[0]] += 1

                count_bu_flat: int = self.data[topic]['gnb_info']['freq'] * self.data[topic]['gnb_info']['time']
                for x in range(self.data[topic]['gnb_info']['max_layer'] + 1):
                    data_count_layer[algo][x] /= (count_bu_flat * self.iteration)
                for x in range(self.data[topic]['gnb_info']['max_layer']):
                    for c in range(cqi[1] - cqi[0] + 1):
                        data_count_bu[algo][x][c] /= self.iteration
                assert False not in [data_count_layer[algo][x] <= 1 for x in
                                     range(len(data_count_layer[algo]))], 'Data gathering error.'

            bar_chart(f'Frame overlap of {topic}',
                      'The number of overlapped UE', [i for i in range(self.data[topic]['gnb_info']['max_layer'] + 1)],
                      'Percentage of BU(%)', data_count_layer,
                      output_file_path, {'iteration': self.iteration, 'layer_or_ue': topic})
            bar_chart_grouped_stacked(f'The MCS used in a frame of {topic}',
                                      'The number of overlapped UE',
                                      [str(i + 1) for i in range(self.data[topic]['gnb_info']['max_layer'])],
                                      'The number BU', ['CQI' + str(i) for i in range(cqi[0], cqi[1] + 1)],
                                      data_count_bu,
                                      output_file_path, {'iteration': self.iteration, 'layer_or_ue': topic},
                                      algorithm, color_gradient=True)

    # ==================================================================================================================
    def collect_ue_cqi(self, layer_or_ue: List[str], algorithm: List[str], result: RESULT,
                       output_file_path: str):
        # collect_data: Dict[str, Dict[str, List[int]]]
        #                    algo      NB   CQI  number of allocated ue using the CQI
        for topic in result:  # only one. e.g. '300ue' or '1layer'
            if topic not in layer_or_ue:
                raise AssertionError("The json file name doesn't match the data saved inside.")
            for algo in result[topic]:
                if algo not in algorithm:
                    raise AssertionError("The json file name doesn't match the data saved inside.")
                self.first_data(topic)
                gnb_cqi: List[int] = self.get_cqi(output_file_path, 'gNB')
                enb_cqi: List[int] = self.get_cqi(output_file_path, 'eNB')
                try:
                    self._collect_ue_cqi(topic, algo, gnb_cqi, enb_cqi,
                                         result[topic][algo][2], result[topic][algo][3], result[topic][algo][4])
                except KeyError:
                    self.data[topic][algo] = {'gNB': [0 for _ in range(gnb_cqi[1] - gnb_cqi[0] + 1)],
                                              'eNB': [0 for _ in range(enb_cqi[1] - enb_cqi[0] + 1)]}
                    self._collect_ue_cqi(topic, algo, gnb_cqi, enb_cqi,
                                         result[topic][algo][2], result[topic][algo][3], result[topic][algo][4])

    def _collect_ue_cqi(self, topic: str, algo: str, gnb_cqi: List[int], enb_cqi: List[int],
                        due_list: List[Dict], gue_list: List[Dict], eue_list: List[Dict]):
        # gNB
        for ue in filter(lambda x: x.is_allocated, due_list + gue_list):
            if ue['ue_type'] == UEType.D and not ue['gnb_info']['rb']:  # dUE not allocated to gNB
                continue
            assert ue['gnb_info']['mcs'], "UE status wasn't updated."
            self.data[topic][algo]['gNB'][ue['gnb_info']['mcs'] - gnb_cqi[0]] += 1

        # eNB
        for ue in filter(lambda x: x.is_allocated, due_list + eue_list):
            if ue['ue_type'] == UEType.D and not ue['enb_info']['rb']:  # dUE not allocated to eNB
                continue
            assert ue['enb_info']['mcs'], "UE status wasn't updated."
            self.data[topic][algo]['eNB'][ue['enb_info']['mcs'] - enb_cqi[0]] += 1

    def gen_ue_cqi(self, output_file_path: str):
        # avg
        gnb_cqi_data: Dict[str, List[float]] = {}
        enb_cqi_data: Dict[str, List[float]] = {}
        for topic in self.data:
            for algo in self.data[topic]:
                gnb_cqi_data[algo] = []
                enb_cqi_data[algo] = []
                for nb in self.data[topic][algo]:
                    for ue_of_cqi in self.data[topic][algo][nb]:
                        ue_of_cqi /= self.iteration
                        (gnb_cqi_data[algo] if nb == 'gNB' else enb_cqi_data[algo]).append(ue_of_cqi)

            # draw two graphs
            gnb_cqi: List[int] = self.get_cqi(output_file_path, 'gNB')
            enb_cqi: List[int] = self.get_cqi(output_file_path, 'eNB')
            bar_chart(f'The CQI in {topic}',
                      'The available CQI in gNB', [str(i) for i in range(gnb_cqi[0], gnb_cqi[1] + 1)],
                      'The number of allocated UE', gnb_cqi_data,
                      output_file_path, {'iteration': self.iteration, 'layer_or_ue': topic})
            bar_chart(f'The CQI in {topic}',
                      'The available CQI in eNB', [str(i) for i in range(enb_cqi[0], enb_cqi[1] + 1)],
                      'The number of allocated UE', enb_cqi_data,
                      output_file_path, {'iteration': self.iteration, 'layer_or_ue': topic})

    # ==================================================================================================================
    def collect_fairness(self, result: RESULT):
        # collect_data: Dict[str, Dict[str, float]]
        #                    topic     algo sum of fairness
        topic, algo = self._topic_and_algo(result)
        self.first_data(topic)

        fairness: float = fairness_index_json(result[topic][algo][2] + result[topic][algo][3] + result[topic][algo][4])
        try:
            self.data[topic][algo] += fairness
        except KeyError:
            self.data[topic][algo] = fairness
        return True

    def gen_fairness(self, output_file_path: str):
        avg_fairness: Dict[str, List[float]] = {algo: [] for algo in self.algorithm}
        for t in self.topic_parameter_str:
            for algo in self.algorithm:
                avg_fairness[algo].append(self.data[t][algo] / self.iteration)

        x_label: str = self._x_label()
        scale_x: List[str] = self._x_scale(self.topic_parameter_int)
        line_chart('', x_label, scale_x, "Jain's Fairness Index", avg_fairness,
                   output_file_path, {'iteration': self.iteration})

    # ==================================================================================================================
    def collect_ini(self, result: RESULT):
        """
        Includes Inter-Carrier Interference in eNB and INI in gNB.
        eNB happens in co-channel frequency, which will be considered when going through gNB.
        Count the number of BU that has ICI.
        """
        # collect_data: Dict[str, Dict[str, int]]
        #                    topic     algo ICI
        topic, algo = self._topic_and_algo(result)
        self.first_data(topic)

        gnb: Dict = result[topic][algo][0]
        for i in range(gnb['frame']['frame_freq']):
            for j in range(gnb['frame']['frame_time']):
                if algo not in self.data[topic]:  # first time, new dictionary
                    self.data[topic][algo] = 0
                if len(gnb['frame']['layer'][0]['bu'][i][j]['lapped_numerology']) > 1:  # happens ICI
                    self.data[topic][algo] += 1

    def gen_ini(self, output_file_path: str):
        avg_ini: Dict[str, List[float]] = {algo: [] for algo in self.algorithm}
        for t in self.topic_parameter_str:
            for algo in self.algorithm:
                avg_ini[algo].append(self.data[t][algo] / self.iteration)

        x_label: str = self._x_label()
        scale_x: List[str] = self._x_scale(self.topic_parameter_int)
        y_label: str = 'The Average Number of BU with ICI'
        bar_chart('', x_label, scale_x, y_label, avg_ini,
                  output_file_path, {'iteration': self.iteration})

    # ==================================================================================================================
    def _topic_and_algo(self, result: RESULT) -> Tuple[str, str]:
        topic: str = list(result.keys())[0]
        algo: str = list(result[topic].keys())[0]
        if topic not in self.topic_parameter_str or algo not in self.algorithm:
            raise AssertionError("The json file name doesn't match the data saved inside.")
        return topic, algo

    def append_parameter_description(self) -> List[str]:
        if 'layer - ' in self.graph_type:
            topic_description: str = 'layer'
        elif 'proportion due - ' in self.graph_type:
            topic_description: str = 'p_due'
        elif 'ue - ' in self.graph_type:
            topic_description: str = 'ue'
        elif 'gnb bw - ' in self.graph_type:
            topic_description: str = 'bw_gnb'
        elif 'cochannel bw - ' in self.graph_type:
            topic_description: str = 'bw_co'
        else:
            raise AssertionError("Undefined graph type.")
        return [str(i) + topic_description for i in self.topic_parameter_int]

    def _x_label(self) -> str:
        if 'layer - ' in self.graph_type:
            x_label: str = 'The number of layers in gNB'
        elif 'proportion due - ' in self.graph_type:
            x_label: str = 'The Proportion of dUE'
        elif 'ue - ' in self.graph_type:
            x_label: str = 'The Number of UE'
        elif 'gnb bw - ' in self.graph_type:
            x_label: str = 'The Bandwidth of gNB(MHz)'
        elif 'cochannel bw - ' in self.graph_type:
            x_label: str = 'The Bandwidth of Sharing Spectrum(MHz)'
        else:
            raise AssertionError("Undefined graph type.")
        return x_label

    def _x_scale(self, parameter: List[int]) -> List[str]:
        if 'proportion due - ' in self.graph_type:
            scale_x: List[str] = [str(i / 100) for i in parameter]
        elif ('layer - ' in self.graph_type) or ('ue - ' in self.graph_type):
            scale_x: List[str] = [str(i) for i in parameter]
        elif ('gnb bw - ' in self.graph_type) or ('cochannel bw - ' in self.graph_type):
            scale_x: List[str] = [str(GnbMhzBuConvertor.bu_to_mhz(i)) for i in parameter]  # MHz
        else:
            raise AssertionError("The graph type isn't defined.")
        return scale_x

    def first_data(self, topic: Union[str, int]):
        if topic not in self.data:
            self.data[topic] = {}
            self.data2[topic] = {}

    @staticmethod
    def get_cqi(output_file_path: str, nb: str = 'gNB') -> List[int]:
        nb_cqi: str = re.search(nb + 'CQI(\\d+)CQI(\\d+)', output_file_path).group()
        find_all = re.findall('CQI(\\d+)', nb_cqi)
        return [int(find_all.pop(0)), int(find_all.pop(0))]

    def input_result_files(self, directory: str) -> List[str]:
        """
        Read only the require results.
        Raise assertion if the file is not found.
        :param directory: The directory to result files.
        :return: A list of result.json to read. That are within the iteration
        """
        filenames = next(walk(directory))[2]
        result_file_to_read: List[str] = [f'topic{i}_iter{j}_algo{k}.json'
                                          for i in self.topic_parameter_str
                                          for j in range(self.iteration)
                                          for k in self.algorithm]
        for i in result_file_to_read:
            if i not in filenames:
                raise AssertionError(f"Can't find the result of {i}.")
        return result_file_to_read
