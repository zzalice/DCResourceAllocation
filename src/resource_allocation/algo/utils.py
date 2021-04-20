from typing import List, Tuple, Union

from src.resource_allocation.ds.eutran import EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GUserEquipment
from src.resource_allocation.ds.ue import UserEquipment
from src.resource_allocation.ds.util_enum import NodeBType, UEType
from utils.assertion import assert_throughput

UE = Union[GUserEquipment, DUserEquipment, EUserEquipment, UserEquipment]


def divide_ue(ue_list: Tuple[UE, ...], is_assert: bool = True) -> Tuple[Tuple[UE, ...], Tuple[UE, ...]]:
    allocated_ue: List[UE] = []
    unallocated_ue: List[UE] = []
    for ue in ue_list:
        if ue.is_allocated:
            if is_assert:
                assert_throughput(ue)
            allocated_ue.append(ue)
        else:
            unallocated_ue.append(ue)
    return tuple(allocated_ue), tuple(unallocated_ue)


def calc_system_throughput(ue_allocated: Tuple[UE, ...], is_assert: bool = True) -> float:
    system_throughput: float = 0.0
    for ue in ue_allocated:
        if is_assert:
            assert_throughput(ue)
        system_throughput += ue.throughput
    return system_throughput  # bit per frame


def calc_system_throughput_uncategorized_ue(ue_list: Tuple[UE, ...]) -> float:
    allocated_ue: Tuple[UE, ...] = divide_ue(ue_list)[0]
    return calc_system_throughput(allocated_ue, is_assert=False)  # bit per frame


def bpframe_to_mbps(throughput: float, frame_time: int) -> float:
    """
    Unit converter.
    :param throughput: Bit per frame.
    :param frame_time: Number of BU in time domain.
    :return: Mbps
    """
    return (throughput / 1000_000) * (1000 // (frame_time // 8))  # Mbps


def sort_by_channel_quality(ue_list: List[UE], nb_type: NodeBType) -> List[UE]:
    ue_list.sort(key=lambda x: x.request_data_rate, reverse=True)
    if nb_type == NodeBType.G:
        assert UEType.E not in [ue.ue_type for ue in ue_list]
        ue_list.sort(key=lambda x: x.coordinate.distance_gnb)
    elif nb_type == NodeBType.E:
        assert UEType.G not in [ue.ue_type for ue in ue_list]
        ue_list.sort(key=lambda x: x.coordinate.distance_enb)
    else:
        raise AssertionError
    return ue_list
