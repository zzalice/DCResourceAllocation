from typing import List

from src.simulation.graph.graph_generator import GraphGenerator
from src.simulation.iteration import IterateAlgo


def layer_or_ue(l_o_u: int, layers: List[int], total_ues: List[int]) -> List[str]:
    if l_o_u == 0:
        l_o_u: List[str] = [str(x) + 'layer' for x in layers]
    elif l_o_u == 1:
        l_o_u: List[str] = [str(x) + 'ue' for x in total_ues]
    else:
        raise AssertionError
    return l_o_u


if __name__ == '__main__':
    """
    MCS parameter can be set in resource_allocation/ds/util_enum.py
    and record in IterateAlgo output pickle.
    """
    f_data: str = '0410-094738high_qos_700ue'  # <-- change
    f_mcs: str = 'gNBCQI5CQI7_eNBCQI5CQI7'  # <-- change
    i: int = 10  # <-- change

    # ---Graphs for ue---
    ut: List[int] = [300, 400, 500, 600, 700, 800, 900]  # <-- change
    # IterateAlgo(iteration=i, folder_data=f_data).iter_ue(total_ue=ut)
    # GraphGenerator(iteration=i, total_ue=ut, graph_type='increasing ue', collect_unallo_ue=True, folder_result=(f'{f_data}/{f_mcs}',))

    # ---Graphs for due to all---
    # p_due: List[int] = [i for i in range(10, 91, 10)]  # <-- change
    # IterateAlgo(iteration=i, folder_data=f_data).iter_due_to_all(due_proportion=p_due)
    # GraphGenerator(iteration=i, percentage=p_due, graph_type='due to all', folder_result=(f'{f_data}/{f_mcs}',))

    # ---Graphs for layer---
    l: List[int] = [1, 2, 3, 4, 5]  # <-- change
    # IterateAlgo(iteration=i, folder_data=f_data).iter_layer(layers=l)
    # GraphGenerator(iteration=i, layers=l, graph_type='sys throughput - layer', folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(iteration=i, layers=l, graph_type='used percentage', folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(iteration=i, layers=l, graph_type='deployment', folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(iteration=i, layers=l, graph_type='allocated ue', folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(iteration=i, layers=l, graph_type='total_allocated_ue', folder_result=(f'{f_data}/{f_mcs}',))

    # ---Graphs for CQI/NOMA---
    l_or_u: int = 0  # 0 for layer, 1 for ue     <-- change
    algo: List[str] = ['DC-RA', 'FRSA', 'MSEMA', 'Baseline']  # <-- change

    layer_or_ue: List[str] = layer_or_ue(l_or_u, l, ut)
    # GraphGenerator(iteration=i, graph_type='NOMA', layer_or_ue=layer_or_ue, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))
    GraphGenerator(iteration=i, graph_type='CQI', layer_or_ue=layer_or_ue, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))
