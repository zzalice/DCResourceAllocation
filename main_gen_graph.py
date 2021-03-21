from typing import List

from src.simulation.graph.graph_generator import GraphGenerator
from src.simulation.iteration import IterateAlgo

if __name__ == '__main__':
    """
    MCS parameter can be set in resource_allocation/ds/util_enum.py
    and record in IterateAlgo output pickle.
    """
    f_data: str = '0321-174019avg_deploy'
    f_mcs: str = 'gNBCQI1CQI15_eNBCQI1CQI15'
    i: int = 10

    # ---Graphs for ue---
    ut: List[int] = [60, 80, 100, 120, 140, 160, 180, 200]
    # IterateAlgo(iteration=i, folder_data=f_data).iter_ue(total_ue=ut)
    GraphGenerator(iteration=i, total_ue=ut, graph_type='increasing ue', folder_result=(f'{f_data}/{f_mcs}',))

    # ---Graphs for layer---
    # l: List[int] = [1, 2, 3, 4, 5]
    # IterateAlgo(iteration=i, folder_data=f_data).iter_layer(layers=l)
    # GraphGenerator(iteration=i, layers=l, graph_type='sys throughput - layer', folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(iteration=i, layers=l, graph_type='used percentage', folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(iteration=i, layers=l, graph_type='deployment', folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(iteration=i, layers=l, graph_type='allocated ue', folder_result=(f'{f_data}/{f_mcs}',))
