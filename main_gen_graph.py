from typing import List, Tuple

from main_gen_data_bw import GnbMhzBuConvertor
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
    f_data: str = '0602-111803L_'  # <-- change
    f_mcs: str = 'gNBCQI1CQI7_eNBCQI1CQI7'  # <-- change
    i: int = 100  # <-- change
    algo: Tuple[str, ...] = ('DC-RA', 'FRSA', 'MSEMA', 'Baseline')  # <-- change

    to_start_over: bool = False  # <-- change

    # ---Graphs for layer---
    l = [1, 2, 3, 4, 5]  # <-- change
    # IterateAlgo(iteration=i, algorithm=algo, folder_data=f_data, to_start_over=to_start_over).iter_layer(l)
    # GraphGenerator(graph_type='layer - throughput', topic_parameter=l, iteration=i, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(graph_type='layer - resource utility', topic_parameter=l, iteration=i, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(graph_type='layer - INI', topic_parameter=l, iteration=i, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(graph_type='layer - satisfaction', topic_parameter=l, iteration=i, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(graph_type='layer - fairness', topic_parameter=l, iteration=i, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(graph_type='layer - allocated ue', topic_parameter=l, iteration=i, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))

    # ---Graphs for ue---
    ut = [j for j in range(200, 601, 100)]  # <-- change
    # IterateAlgo(iteration=i, algorithm=algo, folder_data=f_data, to_start_over=to_start_over).iter_ue(ut)
    # GraphGenerator(graph_type='ue - throughput', collect_unallo_ue=False, topic_parameter=ut, iteration=i, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(graph_type='ue - satisfaction', topic_parameter=ut, iteration=i, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(graph_type='ue - fairness', topic_parameter=ut, iteration=i, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(graph_type='ue - allocated ue', topic_parameter=ut, iteration=i, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))

    # ---Graphs for due to all---
    p_due = [j for j in range(10, 91, 20)]  # <-- change
    # IterateAlgo(iteration=i, algorithm=algo, folder_data=f_data, to_start_over=to_start_over).iter_due_to_all(p_due)
    # GraphGenerator(graph_type='proportion due - throughput', topic_parameter=p_due, iteration=i, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(graph_type='proportion due - satisfaction', topic_parameter=p_due, iteration=i, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(graph_type='proportion due - fairness', topic_parameter=p_due, iteration=i, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(graph_type='proportion due - allocated ue', topic_parameter=p_due, iteration=i, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))

    # ---Graphs for gNB bandwidth---
    gnb_bw = [j for j in range(10, 61, 10)]  # <-- change
    gnb_bw = [GnbMhzBuConvertor.mhz_to_bu(i) for i in gnb_bw]
    # IterateAlgo(iteration=i, algorithm=algo, folder_data=f_data, to_start_over=to_start_over).iter_gnb_bw(gnb_bw)
    # GraphGenerator(graph_type='gnb bw - throughput', topic_parameter=gnb_bw, iteration=i, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(graph_type='gnb bw - INI', topic_parameter=gnb_bw, iteration=i, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(graph_type='gnb bw - satisfaction', topic_parameter=gnb_bw, iteration=i, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(graph_type='gnb bw - fairness', topic_parameter=gnb_bw, iteration=i, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(graph_type='gnb bw - allocated ue', topic_parameter=gnb_bw, iteration=i, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))

    # ---Graphs for co-channel bandwidth---
    co_bw = [j for j in range(0, 36, 5)]  # <-- change
    co_bw = [GnbMhzBuConvertor.mhz_to_bu(i) for i in co_bw]
    # IterateAlgo(iteration=i, algorithm=algo, folder_data=f_data, to_start_over=to_start_over).iter_cochannel(co_bw)
    # GraphGenerator(graph_type='cochannel bw - throughput', topic_parameter=co_bw, iteration=i, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(graph_type='cochannel bw - resource utility', topic_parameter=co_bw, iteration=i, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(graph_type='cochannel bw - satisfaction', topic_parameter=co_bw, iteration=i, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(graph_type='cochannel bw - fairness', topic_parameter=co_bw, iteration=i, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(graph_type='cochannel bw - allocated ue', topic_parameter=co_bw, iteration=i, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))

    # ---Graphs for CQI/NOMA---            # FIXME: add topic_parameter
    l_or_u: int = 0  # 0 for layer, 1 for ue     <-- change
    layer_or_ue: List[str] = layer_or_ue(l_or_u, l, ut)
    # GraphGenerator(graph_type='NOMA', layer_or_ue=layer_or_ue, iteration=i, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(graph_type='CQI', layer_or_ue=layer_or_ue, iteration=i, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))

    # ---Graph for QoS and Deployment---
    t_p: List[int] = l  # <-- change  l, ut, p_due, gnb_bw, co_bw
    topic: str = 'layer'  # <-- change  'layer', 'ue', 'proportion due', 'gnb bw', 'cochannel bw'
    # GraphGenerator(graph_type=f'{topic} - deployment', topic_parameter=t_p, iteration=i, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))
    graph_of = [0, 1, 2, 3, 4, 5, 6]  # <-- change  0:all ue, 1:gNB, 2:eNB, 3:dUE, 4:cross dUE, 5:gUE, 6:eUE
    # GraphGenerator(graph_type=f'{topic} - QoS', graph_of_ue=graph_of, topic_parameter=t_p, iteration=i, algorithm=algo, folder_result=(f'{f_data}/{f_mcs}',))

