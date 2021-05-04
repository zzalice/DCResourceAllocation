from typing import List, Tuple

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
    f_data: str = '0503-231059test_json'  # <-- change
    f_mcs: str = 'gNBCQI1CQI15_eNBCQI1CQI15'  # <-- change
    i: int = 100  # <-- change
    algo: Tuple[str, ...] = ('DC-RA', 'FRSA', 'MSEMA', 'Baseline')  # <-- change

    # ---Graphs for ue---
    ut: List[int] = [300, 400, 500, 600, 700, 800, 900]  # <-- change
    IterateAlgo(iteration=i, folder_data=f_data).iter_ue(total_ue=ut)
    GraphGenerator(graph_type='increasing ue', collect_unallo_ue=True, total_ue=ut, iteration=i, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))

    # ---Graphs for due to all---
    p_due: List[int] = [i for i in range(10, 91, 10)]  # <-- change
    # IterateAlgo(iteration=i, folder_data=f_data).iter_due_to_all(due_proportion=p_due)
    # GraphGenerator(graph_type='due to all', percentage=p_due, iteration=i, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))

    # ---Graphs for layer---
    l: List[int] = [1, 2, 3, 4, 5]  # <-- change
    # IterateAlgo(iteration=i, folder_data=f_data).iter_layer(layers=l)
    # GraphGenerator(graph_type='sys throughput - layer', layers=l, iteration=i, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(graph_type='used percentage', layers=l, iteration=i, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(graph_type='deployment', layers=l, iteration=i, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(graph_type='allocated ue', layers=l, iteration=i, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(graph_type='total_allocated_ue', layers=l, iteration=i, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))

    # ---Graphs for CQI/NOMA---
    l_or_u: int = 0  # 0 for layer, 1 for ue     <-- change
    layer_or_ue: List[str] = layer_or_ue(l_or_u, l, ut)
    # GraphGenerator(graph_type='NOMA', layer_or_ue=layer_or_ue, iteration=i, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(graph_type='CQI', layer_or_ue=layer_or_ue, iteration=i, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))
