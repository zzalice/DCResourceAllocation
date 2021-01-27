from typing import List, Tuple, Union

from src.resource_allocation.ds.eutran import EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GUserEquipment
from src.resource_allocation.ds.ue import UserEquipment


def divide_ue(ue_list: Tuple[UserEquipment, ...], phase: str = "") -> Tuple[
                Tuple[Union[GUserEquipment, DUserEquipment, EUserEquipment], ...], Tuple[
                      Union[GUserEquipment, DUserEquipment, EUserEquipment], ...]]:
    allocated_ue: List = []
    unallocated_ue: List = []
    for ue in ue_list:
        if ue.is_allocated:
            if phase == "phase3":
                throughput: float = 0.0
                if hasattr(ue, 'gnb_info') and ue.gnb_info.rb:
                    throughput += ue.gnb_info.mcs.value * ue.gnb_info.rb
                if hasattr(ue, 'enb_info') and ue.enb_info.rb:
                    throughput += ue.enb_info.mcs.value * ue.enb_info.rb
                assert ue.throughput == throughput
                assert ue.throughput >= ue.request_data_rate
            allocated_ue.append(ue)
        else:
            unallocated_ue.append(ue)
    return tuple(allocated_ue), tuple(unallocated_ue)


def calc_system_throughput(ue_allocated: Tuple[UserEquipment]) -> float:
    system_throughput: float = 0.0
    for ue in ue_allocated:
        system_throughput += ue.throughput
    return system_throughput  # bit per frame
