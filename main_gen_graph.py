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
    layer_or_ue: int = 0  # 0 for layer, 1 for ue     <-- change
    algo: List[str] = ['DC-RA', 'FRSA', 'MSEMA', 'Intuitive']  # <-- change

    if layer_or_ue == 0:
        layer_or_ue: List[str] = [str(x) + 'layer' for x in l]
    elif layer_or_ue == 1:
        layer_or_ue: List[str] = [str(x) + 'ue' for x in ut]
    else:
        raise AssertionError
    for l_o_u in layer_or_ue:
        GraphGenerator(iteration=i, layer_or_ue=l_o_u, algorithm=algo, graph_type='NOMA', folder_result=(f'{f_data}/{f_mcs}',))
