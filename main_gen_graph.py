from typing import List, Tuple

from main_gen_data_bw import gnb_mhz_to_bu
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
    f_data: str = '0509-190047BWGNB_'  # <-- change
    f_mcs: str = 'gNBCQI1CQI15_eNBCQI1CQI15'  # <-- change
    ir: Tuple[int, int] = (0, 99)  # <-- change
    algo: Tuple[str, ...] = ('DC-RA', 'FRSA', 'MSEMA', 'Baseline')  # <-- change

    to_start_over: bool = False  # <-- change

    i: int = ir[1] - ir[0] + 1

    # ---Graphs for layer---
    l: List[int] = [1, 2, 3, 4, 5]  # <-- change
    # IterateAlgo(iteration=i, algorithm=algo, folder_data=f_data, to_start_over=to_start_over).iter_layer(l)
    # GraphGenerator(graph_type='layer - throughput', topic_parameter=l, iter_range=ir, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(graph_type='used percentage', topic_parameter=l, iter_range=ir, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(graph_type='allocated ue', topic_parameter=l, iter_range=ir, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(graph_type='total_allocated_ue', topic_parameter=l, iter_range=ir, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(graph_type='layer - fairness', topic_parameter=l, iter_range=ir, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(graph_type='deployment', topic_parameter=l, iter_range=ir, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))

    # ---Graphs for ue---
    ut: List[int] = [300, 400, 500, 600, 700, 800, 900]  # <-- change
    # IterateAlgo(iteration=i, algorithm=algo, folder_data=f_data, to_start_over=to_start_over).iter_ue(ut)
    # GraphGenerator(graph_type='ue - throughput', collect_unallo_ue=False, topic_parameter=ut, iter_range=ir, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(graph_type='ue - fairness', topic_parameter=ut, iter_range=ir, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))

    # ---Graphs for due to all---
    p_due: List[int] = [j for j in range(10, 91, 10)]  # <-- change
    # IterateAlgo(iteration=i, algorithm=algo, folder_data=f_data, to_start_over=to_start_over).iter_due_to_all(p_due)
    # GraphGenerator(graph_type='proportion due - throughput', topic_parameter=p_due, iter_range=ir, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(graph_type='proportion due - fairness', topic_parameter=p_due, iter_range=ir, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))

    # ---Graphs for gNB bandwidth---
    gnb_bw = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]  # <-- change
    gnb_bw = [gnb_mhz_to_bu(i) for i in gnb_bw]
    # IterateAlgo(iteration=i, algorithm=algo, folder_data=f_data, to_start_over=to_start_over).iter_gnb_bw(gnb_bw)
    # GraphGenerator(graph_type='gnb bw - throughput', topic_parameter=gnb_bw, iter_range=ir, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(graph_type='gnb bw - INI', topic_parameter=gnb_bw, iter_range=ir, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(graph_type='gnb bw - fairness', topic_parameter=gnb_bw, iter_range=ir, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))

    # ---Graphs for co-channel bandwidth---
    cochannel_bw = [j for j in range(5, 51, 5)]  # <-- change
    cochannel_bw = [gnb_mhz_to_bu(i) for i in cochannel_bw]
    # IterateAlgo(iteration=i, algorithm=algo, folder_data=f_data, to_start_over=to_start_over).iter_cochannel(cochannel_bw)
    # GraphGenerator(graph_type='cochannel bw - throughput', topic_parameter=cochannel_bw, iter_range=ir, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(graph_type='cochannel bw - fairness', topic_parameter=cochannel_bw, iter_range=ir, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))

    # ---Graphs for CQI/NOMA---            # TODO: add topic_parameter
    l_or_u: int = 0  # 0 for layer, 1 for ue     <-- change
    layer_or_ue: List[str] = layer_or_ue(l_or_u, l, ut)
    # GraphGenerator(graph_type='NOMA', layer_or_ue=layer_or_ue, iter_range=ir, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(graph_type='CQI', layer_or_ue=layer_or_ue, iter_range=ir, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))
