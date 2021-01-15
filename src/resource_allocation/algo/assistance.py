from typing import List, Tuple

from src.resource_allocation.ds.ue import UserEquipment


def divid_ue(ue_list: Tuple[UserEquipment, ...]) -> Tuple[
                           Tuple[UserEquipment, ...], Tuple[UserEquipment, ...]]:
    allocated_ue: List = []
    unallocated_ue: List = []
    for ue in ue_list:
        if ue.is_allocated:
            allocated_ue.append(ue)
        else:
            unallocated_ue.append(ue)
    return tuple(allocated_ue), tuple(unallocated_ue)


def calc_system_throughput(ue_allocated: List[UserEquipment]) -> float:
    system_throughput: float = 0.0
    for ue in ue_allocated:
        system_throughput += ue.throughput
    return system_throughput    # bit per frame
