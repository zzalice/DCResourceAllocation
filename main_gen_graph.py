from src.simulation.graph.graph_generator import GraphGenerator

if __name__ == '__main__':
    # GraphGenerator(times=10, folder='large_radius').gen_sys_throughput_layer(layers=[1, 2, 3])
    GraphGenerator(times=10, folder='radius_05km').gen_used_percentage('src/simulation/graph/radius_05km/dcra_intuitive.P')
