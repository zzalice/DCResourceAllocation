from typing import List, Tuple, Union

from src.resource_allocation.ds.eutran import EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GUserEquipment
from src.resource_allocation.ds.ue import UserEquipment
from utils.assertion import assert_throughput


def divide_ue(ue_list: Tuple[UserEquipment, ...], is_assert: bool = True) -> Tuple[
                Tuple[Union[GUserEquipment, DUserEquipment, EUserEquipment], ...], Tuple[
                      Union[GUserEquipment, DUserEquipment, EUserEquipment], ...]]:
    allocated_ue: List = []
    unallocated_ue: List = []
    for ue in ue_list:
        if ue.is_allocated:
            if is_assert:
                assert_throughput(ue)
            allocated_ue.append(ue)
        else:
            unallocated_ue.append(ue)
    return tuple(allocated_ue), tuple(unallocated_ue)


def calc_system_throughput(ue_allocated: Tuple[UserEquipment, ...], is_assert: bool = True) -> float:
    system_throughput: float = 0.0
    for ue in ue_allocated:
        if is_assert:
            assert_throughput(ue)
        system_throughput += ue.throughput
    return system_throughput  # bit per frame


def calc_system_throughput_uncategorized_ue(ue_list: Tuple[UserEquipment, ...]) -> float:
    allocated_ue: Tuple[UserEquipment, ...] = divide_ue(ue_list)[0]
    return calc_system_throughput(allocated_ue, is_assert=False)  # bit per frame


def bpframe_to_mbps(throughput: float, frame_time: int) -> float:
    """
    Unit converter.
    :param throughput: Bit per frame.
    :param frame_time: Number of BU in time domain.
    :return: Mbps
    """
    return (throughput / 1000_000) * (1000 // (frame_time // 8))    # Mbps
