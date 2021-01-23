from typing import List, Tuple, Union

from src.resource_allocation.ds.eutran import EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GUserEquipment
from src.resource_allocation.ds.ue import UserEquipment


def divide_ue(ue_list: Tuple[UserEquipment, ...]) -> Tuple[
                Tuple[Union[GUserEquipment, DUserEquipment, EUserEquipment], ...], Tuple[
                      Union[GUserEquipment, DUserEquipment, EUserEquipment], ...]]:
    allocated_ue: List = []
    unallocated_ue: List = []
    for ue in ue_list:
        if ue.is_allocated:
            allocated_ue.append(ue)
        else:
            unallocated_ue.append(ue)
    return tuple(allocated_ue), tuple(unallocated_ue)


def calc_system_throughput(ue_allocated: Tuple[UserEquipment]) -> float:
    system_throughput: float = 0.0
    for ue in ue_allocated:
        system_throughput += ue.throughput
    return system_throughput  # bit per frame
