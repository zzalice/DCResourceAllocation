from src.simulation.graph.graph_generator import GraphGenerator
from src.simulation.iteration import IterateAlgo

if __name__ == '__main__':
    """
    MCS parameter can be set in resource_allocation/ds/util_enum.py
    and record in IterateAlgo output pickle.
    """
    # IterateAlgo().iter_layer(folder_data='0315-094335small', iteration=10, layers=[1, 2, 3, 4, 5])

    # GraphGenerator(folder_result=('0315-094335small/gNBCQI1CQI15_eNBCQI1CQI15',), iteration=10, layers=[2, 3, 4], graph_type='sys throughput - layer')
    GraphGenerator(folder_result=('0315-094335small/gNBCQI1CQI15_eNBCQI1CQI15',), iteration=10, layers=[1, 2, 3, 4, 5], graph_type='used percentage')
    # GraphGenerator(times=10, folder='standard').gen_deployment('/Users/hscc/Downloads/Papers/simulation/standard/dcra_intuitive.P')
    # GraphGenerator(times=10, folder=['standard', 'radius_05km', 'large_radius']).gen_avg_allocated_ue(
    #     ['/Users/hscc/Downloads/Papers/simulation/', '/dcra_intuitive.P'])
