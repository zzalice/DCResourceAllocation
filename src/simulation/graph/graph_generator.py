from typing import Any, Dict, List, Tuple

from main import dc_resource_allocation
from main_intuitive import intuitive_resource_allocation
from src.resource_allocation.algo.utils import bpframe_to_mbps, calc_system_throughput_uncategorized_ue
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.simulation.graph.util_graph import line_chart

if __name__ == '__main__':
    time: int = 3
    max_layers: List[int] = [1, 2, 3]
    result: Dict[str, List[Tuple[GNodeB, ENodeB, List[DUserEquipment], List[GUserEquipment], List[EUserEquipment]]]] = {
        'DC-RA': [], 'Intuitive': []}
    avg_system_throughput: Dict[str, List[Any]] = {'DC-RA': [0.0 for _ in range(len(max_layers))],
                                                   'Intuitive': [0.0 for _ in range(len(max_layers))]}
    for l in range(len(max_layers)):
        data_set_file_path: str = f'hotspot/{max_layers[l]}layer/'
        for i in range(time):
            result['DC-RA'].append(dc_resource_allocation(data_set_file_path + str(i)))
            result['Intuitive'].append(intuitive_resource_allocation(data_set_file_path + str(i)))

            # sum system throughput
            for data in avg_system_throughput:
                avg_system_throughput[data][l] += calc_system_throughput_uncategorized_ue(
                    result[data][-1][2] + result[data][-1][3] + result[data][-1][4])

        # avg system throughput
        for data in avg_system_throughput:
            avg_system_throughput[data][l] /= time
            avg_system_throughput[data][l] = bpframe_to_mbps(avg_system_throughput[data][l],
                                                             result[data][-1][0].frame.frame_time)

    line_chart('', 'The number of gNB layer', max_layers, 'System throughput(Mbps)', avg_system_throughput, 'system_throughput')
