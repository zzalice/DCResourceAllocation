from typing import List

from src.simulation.graph.graph_generator import GraphGenerator
from src.simulation.iteration import IterateAlgo

if __name__ == '__main__':
    """
    MCS parameter can be set in resource_allocation/ds/util_enum.py
    and record in IterateAlgo output pickle.
    """
    f_data: str = '0317-100632small_frame50_moreUE'
    f_mcs: str = 'gNBCQI1CQI15_eNBCQI1CQI15'
    i: int = 10
    l: List[int] = [1, 2, 3, 4, 5]
    IterateAlgo().iter_layer(iteration=i, layers=l, folder_data=f_data)

    GraphGenerator(iteration=i, layers=l, graph_type='sys throughput - layer', folder_result=(f'{f_data}/{f_mcs}',))
    GraphGenerator(iteration=i, layers=l, graph_type='used percentage', folder_result=(f'{f_data}/{f_mcs}',))
    # GraphGenerator(times=10, folder='standard').gen_deployment('/Users/hscc/Downloads/Papers/simulation/standard/dcra_intuitive.P')
    # GraphGenerator(times=10, folder=['standard', 'radius_05km', 'large_radius']).gen_avg_allocated_ue(
    #     ['/Users/hscc/Downloads/Papers/simulation/', '/dcra_intuitive.P'])
