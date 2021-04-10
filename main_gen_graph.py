from typing import List

from src.simulation.graph.graph_generator import GraphGenerator
from src.simulation.iteration import IterateAlgo

if __name__ == '__main__':
    """
    MCS parameter can be set in resource_allocation/ds/util_enum.py
    and record in IterateAlgo output pickle.
    """
    f_data: str = '0410-010147avg_deploy'  # <-- change
    f_mcs: str = 'gNBCQI1CQI15_eNBCQI1CQI15'  # <-- change
    i: int = 10  # <-- change

    # ---Graphs for ue---
    ut: List[int] = [60, 80, 100, 120, 140, 160, 180, 200]  # <-- change
    IterateAlgo(iteration=i, folder_data=f_data).iter_ue(total_ue=ut)
    GraphGenerator(iteration=i, total_ue=ut, graph_type='increasing ue', folder_result=(f'{f_data}/{f_mcs}',))

    # ---Graphs for layer---
    # l: List[int] = [1, 2, 3, 4, 5]  # <-- change
    # IterateAlgo(iteration=i, folder_data=f_data).iter_layer(layers=l)
    # GraphGenerator(iteration=i, layers=l, graph_type='sys throughput - layer', folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(iteration=i, layers=l, graph_type='used percentage', folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(iteration=i, layers=l, graph_type='deployment', folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(iteration=i, layers=l, graph_type='allocated ue', folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(iteration=i, layers=l, graph_type='total_allocated_ue', folder_result=(f'{f_data}/{f_mcs}',))

    # ---Graphs for NOMA and INI---
    # layer_or_ue: str = '300ue'  # '300ue' or '3layer' <-- change
    # algo: List[str] = ['DC-RA', 'FRSA', 'MSEMA', 'Intuitive']
    # GraphGenerator(iteration=i, layer_or_ue=layer_or_ue, algorithm=algo, graph_type='NOMA', folder_result=(f'{f_data}/{f_mcs}',))
