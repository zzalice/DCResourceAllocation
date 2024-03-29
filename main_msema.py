import os
from datetime import datetime
from typing import Tuple

from main_mcuphm import mcup_hm
from src.resource_allocation.algo.algo_msema import Msema
from src.resource_allocation.algo.new_ue_list import SimpleDC
from src.resource_allocation.algo.utils import divide_ue
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.simulation.data.data_loader import DataLoader
from utils.pickle_generator import visualize_phase_uncategorized_ue


def msema_rb_ra(data_set: str, visualize_the_algo: bool = False) -> Tuple[
    GNodeB, ENodeB, Tuple[DUserEquipment, ...], Tuple[GUserEquipment, ...], Tuple[EUserEquipment, ...]]:
    dirname = os.path.dirname(__file__)
    file_name_vis = "vis_msema_" + datetime.today().strftime('%Y%m%d') + ".P"
    visualization_file_path = os.path.join(dirname, 'utils/frame_visualizer', file_name_vis)

    data_set_file_path = os.path.join(dirname, 'src/simulation/data', data_set + '.json')
    g_nb, e_nb, channel_model, g_ue_list, d_ue_list, e_ue_list, gue_qos, eue_qos, _, _ = DataLoader().run(
        data_set_file_path)

    # main
    # DC user association
    gnb_sc_ue_list, enb_sc_ue_list, dc_ue_list = mcup_hm(g_nb, e_nb, g_ue_list, d_ue_list, e_ue_list, gue_qos, eue_qos)

    # gNB resource allocation
    Msema(g_nb, channel_model, ()).allocate_ue_list(dc_ue_list + gnb_sc_ue_list)

    # eNB resource allocation
    gnb_sc_allocated, _ = divide_ue(gnb_sc_ue_list)
    dc_ue_allocated, _ = divide_ue(dc_ue_list)
    SimpleDC(e_nb, dc_ue_allocated + enb_sc_ue_list, dc_ue_allocated + gnb_sc_allocated, channel_model
             ).allocate(allow_lower_mcs=False)

    if visualize_the_algo:
        visualize_phase_uncategorized_ue(visualization_file_path, 'wb',
                                         "MSEMA", g_nb, e_nb, g_ue_list, d_ue_list, e_ue_list)

    return g_nb, e_nb, d_ue_list, g_ue_list, e_ue_list


if __name__ == '__main__':
    file_path: str = '0409-215232debug/300ue/0'
    msema_rb_ra(file_path, visualize_the_algo=True)
