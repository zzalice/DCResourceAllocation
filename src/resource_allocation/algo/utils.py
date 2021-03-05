from typing import List, Tuple, Union

from src.resource_allocation.ds.eutran import EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GUserEquipment
from src.resource_allocation.ds.ue import UserEquipment


def divide_ue(ue_list: Tuple[UserEquipment, ...], assert_throughput: bool = True) -> Tuple[
                Tuple[Union[GUserEquipment, DUserEquipment, EUserEquipment], ...], Tuple[
                      Union[GUserEquipment, DUserEquipment, EUserEquipment], ...]]:
    allocated_ue: List = []
    unallocated_ue: List = []
    for ue in ue_list:
        if ue.is_allocated:
            if assert_throughput:
                if hasattr(ue, 'gnb_info'):
                    if ue.gnb_info.mcs:
                        assert ue.gnb_info.rb, "There is MCS but no RB(s)"
                        assert (ue.gnb_info.mcs.value <= rb.mcs.value for rb in ue.gnb_info.rb)
                    else:
                        assert ue.gnb_info.mcs is None and not ue.gnb_info.rb, "The MCS is not up-to-date."
                if hasattr(ue, 'enb_info'):
                    if ue.enb_info.mcs:
                        assert ue.enb_info.rb, "There is MCS but no RB(s)"
                        assert (ue.enb_info.mcs.value <= rb.mcs.value for rb in ue.enb_info.rb)
                    else:
                        assert ue.enb_info.mcs is None and not ue.enb_info.rb, "The MCS is not up-to-date."

                assert ue.throughput == ue.calc_throughput()
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
