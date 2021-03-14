from src.simulation.graph.graph_generator import GraphGenerator
from src.simulation.iteration import IterateAlgo

if __name__ == '__main__':
    # IterateAlgo().iter_layer(iteration=2, layers=[1, 2, 3], folder_data='large_radius')

    GraphGenerator(folder_result=('large_radius',), graph_type='sys throughput - layer', iteration=2, layers=[1, 2, 3])
    # GraphGenerator(times=10, folder='large_radius').gen_sys_throughput_layer(layers=[1, 2, 3])
    # GraphGenerator(times=10, folder='large_radius').gen_used_percentage('/Users/hscc/Downloads/Papers/simulation/large_radius/dcra_intuitive.P')
    # GraphGenerator(times=10, folder='standard').gen_deployment('/Users/hscc/Downloads/Papers/simulation/standard/dcra_intuitive.P')
    # GraphGenerator(times=10, folder=['standard', 'radius_05km', 'large_radius']).gen_avg_allocated_ue(
    #     ['/Users/hscc/Downloads/Papers/simulation/', '/dcra_intuitive.P'])
