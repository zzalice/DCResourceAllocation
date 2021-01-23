import pickle

from datetime import datetime

from src.resource_allocation.algo.assistance import calc_system_throughput
from src.resource_allocation.algo.intuitive_algo import Intuitive

if __name__ == '__main__':
    data_set_file_path = "../src/resource_allocation/simulation/data/" + "data_generator" + ".P"

    with open(data_set_file_path, "rb") as file:
        g_nb, e_nb, cochannel_index, g_ue_list, d_ue_list, e_ue_list = pickle.load(file)

    intuitive: Intuitive = Intuitive(g_nb, e_nb, cochannel_index, g_ue_list, d_ue_list, e_ue_list)
    intuitive.algorithm()
    system_throughput: float = calc_system_throughput(
        tuple(intuitive.gue_allocated + intuitive.due_allocated + intuitive.eue_allocated))

    with open("../utils/frame_visualizer/vis_intuitive_" + datetime.today().strftime('%Y%m%d') + ".P", "wb") as file:
        pickle.dump(["intuitive",
                     g_nb.frame, e_nb.frame, system_throughput,
                     {"allocated": intuitive.gue_allocated, "unallocated": intuitive.gue_fail},
                     {"allocated": intuitive.due_allocated, "unallocated": intuitive.due_fail},
                     {"allocated": intuitive.eue_allocated, "unallocated": intuitive.eue_fail}],
                    file)
