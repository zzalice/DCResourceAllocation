import pickle
from typing import Tuple

from src.resource_allocation.algo.utils import calc_system_throughput, divide_ue
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment


def visualize_phase_uncategorized_ue(file_path: str, mode: str, title: str, gnb: GNodeB, enb: ENodeB,
                                     gue_list: Tuple[GUserEquipment, ...], due_list: Tuple[DUserEquipment, ...],
                                     eue_list: Tuple[EUserEquipment, ...], is_assert: bool = True):
    gue_allocated, gue_unallocated = divide_ue(gue_list, is_assert)
    due_allocated, due_unallocated = divide_ue(due_list, is_assert)
    eue_allocated, eue_unallocated = divide_ue(eue_list, is_assert)

    visualize_phase(file_path, mode, title, gnb, enb, gue_allocated, due_allocated, eue_allocated, gue_unallocated,
                    due_unallocated, eue_unallocated, is_assert)


def visualize_phase(file_path: str, mode: str, title: str, gnb: GNodeB, enb: ENodeB,
                    gue_allocated: Tuple[GUserEquipment, ...] = (), due_allocated: Tuple[DUserEquipment, ...] = (),
                    eue_allocated: Tuple[EUserEquipment, ...] = (), gue_unallocated: Tuple[GUserEquipment, ...] = (),
                    due_unallocated: Tuple[DUserEquipment, ...] = (), eue_unallocated: Tuple[EUserEquipment, ...] = (),
                    is_assert: bool = True):
    gue_allocated = tuple(gue_allocated)
    due_allocated = tuple(due_allocated)
    eue_allocated = tuple(eue_allocated)
    gue_unallocated = tuple(gue_unallocated)
    due_unallocated = tuple(due_unallocated)
    eue_unallocated = tuple(eue_unallocated)
    with open(file_path, mode) as f:
        pickle.dump([title,
                     gnb.frame, enb.frame,
                     calc_system_throughput(gue_allocated + due_allocated + eue_allocated, is_assert=is_assert),
                     {"allocated": gue_allocated, "unallocated": gue_unallocated},
                     {"allocated": due_allocated, "unallocated": due_unallocated},
                     {"allocated": eue_allocated, "unallocated": eue_unallocated}],
                    f)
