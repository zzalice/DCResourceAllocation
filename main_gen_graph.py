from src.simulation.graph.graph_generator import GraphGenerator


def main():
    pass


if __name__ == '__main__':
    GraphGenerator(times=500, folder='large_radius').gen_sys_throughput_layer(layers=[1, 2, 3])
