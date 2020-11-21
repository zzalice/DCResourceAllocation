from typing import List, Tuple

from src.resource_allocation.ds.ue import UserEquipment


def cluster_unallocated_ue(ue_list: Tuple[UserEquipment, ...]) -> Tuple[
                           Tuple[UserEquipment, ...], Tuple[UserEquipment, ...]]:
    allocated_ue: List = []
    unallocated_ue: List = []
    for ue in ue_list:
        if ue.is_allocated:
            allocated_ue.append(ue)
        else:
            unallocated_ue.append(ue)
    return tuple(allocated_ue), tuple(unallocated_ue)
