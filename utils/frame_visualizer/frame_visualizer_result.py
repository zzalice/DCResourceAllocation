import pickle
from typing import Dict, List

from src.resource_allocation.algo.utils import calc_system_throughput, divide_ue
from utils.frame_visualizer.frame_visualizer import visualize


def visualize_result(file_path_to_visualize: str, algo: List[str], layer_str: str, num_iter: int):
    file_name = file_path_to_visualize + '/result'
    with open(file_name + ".P", "rb") as f:
        information = pickle.load(f)
        while num_iter:
            try:
                data: Dict[str, Dict] = pickle.load(f)  # {'1layer': {'DC-RA': [gNB, eNB, dUE, gUE, eUE],
                #                                                     'Intuitive': [gNB, eNB, dUE, gUE, eUE]}}
                num_iter = run_visualize(data, layer_str, num_iter, algo, file_name)
            except EOFError:
                break


def run_visualize(data, layer_str, num_iter, algo, file_name):
    if next(iter(data)) == layer_str:
        num_iter -= 1
        for a in algo:
            try:
                d = data[layer_str][a]  # [gNB, eNB, dUE, gUE, eUE]

                due_allocated, due_unallocated = divide_ue(d[2], True)
                gue_allocated, gue_unallocated = divide_ue(d[3], True)
                eue_allocated, eue_unallocated = divide_ue(d[4], True)
                throughput = calc_system_throughput(gue_allocated + due_allocated + eue_allocated, True)

                visualize(f'{file_name}_{a}_{layer_str}_{num_iter}',
                          [a], [d[0].frame], [d[1].frame], [throughput],  # stage, gFrame, eFrame, system_throughput
                          [{"allocated": gue_allocated, "unallocated": gue_unallocated}],
                          [{"allocated": due_allocated, "unallocated": due_unallocated}],
                          [{"allocated": eue_allocated, "unallocated": eue_unallocated}])
            except KeyError:
                pass
    return num_iter


if __name__ == '__main__':
    file_path: str = '../../src/simulation/graph/0408-231425avg_deploy/gNBCQI1CQI15_eNBCQI1CQI15'

    algorithm: List[str] = ['DC-RA', 'FRSA', 'MSEMA', 'Baseline']
    layer_or_ue: str = '460ue'  # '1layer'
    iteration: int = 1

    visualize_result(file_path, algorithm, layer_or_ue, iteration)
