from typing import Dict, List, Optional, Tuple, Union

from src.resource_allocation.ds.nodeb import ENBInfo, GNBInfo
from src.resource_allocation.ds.undo import Undo
from src.resource_allocation.ds.util_enum import E_MCS, G_MCS


class MaxSubarray(Undo):
    """
    Find the cut of an array into two half with highest throughput.
    Remove the half with lower MCS(CQI).

    :return: the range of the RBs to remove with lower MCS.

    e.g.
    Input: [5,4,2,3,3,3]
    [5,4], [2,3,3,3] has the highest throughput 4*2 + 2*4 = 16
    Output: 2 6   # remove right part of the input list, from index 2 to the end

    e.g.
    Input: [3,1,2,7,5]
    [3,1,2], [7,5] has the highest throughput 1*3 + 5*2 = 13
    Output: 0 3   # remove left part of the input list, from the start of the list to index 3

    e.g.
    Input: [5,4,2,3,2,7,6]
    [5,4,2,3,2], [7,6] has the highest throughput 2*5 + 6*2 = 22
    Output: 0 5

    e.g.
    Input: [5, 4, 3, 3, 2, 5]
    [5, 4], [3, 3, 2, 5] 4*2 + 2*4 = 16
    [5, 4, 3, 3], [2, 5] 3*4 + 2*2 = 16   # return the later cut
    Output: 4 6

    e.g.
    Input: [2,2,2,5,2]
    Output: 5 5

    e.g.
    Input: [3]
    Output: 1 1
    """
    def __init__(self, ue_nb_info: Union[GNBInfo, ENBInfo]):
        super().__init__()
        assert ue_nb_info.rb, "Input empty list."
        self.ue_nb_info: Union[GNBInfo, ENBInfo] = ue_nb_info
        self.ue_nb_info.rb.sort(key=lambda x: x.j_start)  # sort by time
        self.ue_nb_info.rb.sort(key=lambda x: x.i_start)  # sort by freq
        self.ue_nb_info.rb.sort(key=lambda x: x.layer.layer_index)  # sort by layer
        self.mcs_list: Union[List[G_MCS], List[E_MCS]] = [rb.mcs for rb in self.ue_nb_info.rb]

        # The index range of the RBs to move to the other BS
        self.rm_from: int = -1
        self.rm_to: int = -1

        self.new_mcs: Optional[G_MCS, E_MCS] = None     # the MCS of the better half
        self.lower_mcs: Optional[G_MCS, E_MCS] = None   # the MCS of the lower half

    def max_subarray(self) -> bool:
        mcs_right, throughput_right = self.subarray(self.mcs_list[1:])
        max_throughput: Dict = {'idx': 1,
                                'mcs-left': self.mcs_list[0],
                                'mcs-right': mcs_right,
                                'throughput': self.mcs_list[0].value + throughput_right}

        mcs_left: Union[G_MCS, E_MCS] = max_throughput['mcs-left']
        idx: int = 1
        for mcs in self.mcs_list[1:]:
            idx += 1
            if mcs.value < mcs_left.value:
                mcs_left = mcs
            throughput_left: float = mcs_left.value * idx
            mcs_right, throughput_right = self.subarray(self.mcs_list[idx:])
            throughput = throughput_left + throughput_right
            if throughput >= max_throughput['throughput']:
                max_throughput['idx'] = idx
                max_throughput['mcs-left'] = mcs_left
                max_throughput['mcs-right'] = mcs_right
                max_throughput['throughput'] = throughput

        if max_throughput['mcs-right'] is None:
            # if (the input list len == 1) OR (the cut is at the end of the MCS list, a.k.a. not cutting)
            return False
        elif max_throughput['mcs-left'].value < max_throughput['mcs-right'].value:
            # remove left half
            assert 0 <= max_throughput['idx'] < idx
            self.rm_from = 0
            self.rm_to = max_throughput['idx']
            self.new_mcs = max_throughput['mcs-right']
            self.lower_mcs = max_throughput['mcs-left']
            return True
        elif max_throughput['mcs-left'].value > max_throughput['mcs-right'].value:
            # remove right half
            assert 0 < max_throughput['idx'] < idx
            self.rm_from = max_throughput['idx']
            self.rm_to = idx
            self.new_mcs = max_throughput['mcs-left']
            self.lower_mcs = max_throughput['mcs-right']
            return True
        elif max_throughput['mcs-left'] == max_throughput['mcs-right']:
            # no cut may increase resource efficiency
            return False
        else:
            raise ValueError(f'Input:{self.mcs_list} Max throughput:{max_throughput}')

    @staticmethod
    def subarray(subarray: List[Union[G_MCS, E_MCS]]) -> Tuple[Union[None, G_MCS, E_MCS], float]:
        if not subarray:
            return None, 0.0
        min_mcs: Union[G_MCS, E_MCS] = min(subarray, key=lambda m: m.value)
        throughput: float = min_mcs.value * len(subarray)
        return min_mcs, throughput

    @Undo.undo_func_decorator
    def remove_rbs(self):
        assert self.rm_to > self.rm_from > -1 and self.new_mcs and self.lower_mcs
        # remove the RBs that makes MCS worst
        from_l_or_r: int = 0 if self.rm_from == 0 else -1  # remove left half when rm_to == 0 else right
        for _ in range(self.rm_to - self.rm_from):
            self.append_undo(lambda rb=self.ue_nb_info.rb[from_l_or_r]: rb.undo(),
                             lambda rb=self.ue_nb_info.rb[from_l_or_r]: rb.purge_undo())
            self.ue_nb_info.rb[from_l_or_r].remove_rb()
        self.append_undo(lambda origin=self.ue_nb_info.mcs: setattr(self.ue_nb_info, 'mcs', origin))
        self.ue_nb_info.update_mcs()
        return True
