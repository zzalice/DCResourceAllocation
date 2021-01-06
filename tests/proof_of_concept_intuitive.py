import pickle

from src.resource_allocation.algo.intuitive_algo import Intuitive

if __name__ == '__main__':
    data_set_file_path = "../src/resource_allocation/simulation/data/" + "data_generator" + ".P"

    with open(data_set_file_path, "rb") as file:
        g_nb, e_nb, cochannel_index, g_ue_list, d_ue_list, e_ue_list = pickle.load(file)

    intuitive: Intuitive = Intuitive(g_nb, e_nb, cochannel_index, g_ue_list, d_ue_list, e_ue_list)
    intuitive.algorithm()
