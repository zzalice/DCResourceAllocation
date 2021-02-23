from typing import Dict, List, Optional, Tuple, Union

from src.resource_allocation.ds.util_enum import E_MCS, G_MCS


class MaxSubarray:
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

    def max_subarray(self, array: List[Union[G_MCS, E_MCS]]) -> Tuple[
                     int, int, Optional[Union[G_MCS, E_MCS]], Optional[Union[G_MCS, E_MCS]]]:
        """
        To cut part of the allocated RB to the other BS for dUE.
        :param array: The MCS of the RBs of ONE UE in ONE BS.
        :return: The index range of the RBs to move to the other BS,
                 the MCS of the better half, and the MCS of the lower half.
        """
        assert array, "Input empty list."
        assert len(set(type(mcs) for mcs in array)) == 1, "The input MCS should belong to a BS."
        mcs_right, throughput_right = self.subarray(array[1:])
        max_throughput: Dict = {'idx': 1,
                                'mcs-left': array[0],
                                'mcs-right': mcs_right,
                                'throughput': array[0].value + throughput_right}

        mcs_left: Union[G_MCS, E_MCS] = max_throughput['mcs-left']
        idx: int = 1
        for mcs in array[1:]:
            idx += 1
            if mcs.value < mcs_left.value:
                mcs_left = mcs
            throughput_left: float = mcs_left.value * idx
            mcs_right, throughput_right = self.subarray(array[idx:])
            throughput = throughput_left + throughput_right
            if throughput >= max_throughput['throughput']:
                max_throughput['idx'] = idx
                max_throughput['mcs-left'] = mcs_left
                max_throughput['mcs-right'] = mcs_right
                max_throughput['throughput'] = throughput
        if max_throughput['mcs-right'] is None:
            # if (the input list len == 1) OR (the cut is at the end of the MCS list, a.k.a. not cutting)
            return -1, -1, None, None
        elif max_throughput['mcs-left'].value < max_throughput['mcs-right'].value:
            # remove left half
            assert 0 <= max_throughput['idx'] < idx
            assert max_throughput['mcs-right'] != max_throughput['mcs-left']
            return 0, max_throughput['idx'], max_throughput['mcs-right'], max_throughput['mcs-left']
        elif max_throughput['mcs-left'].value > max_throughput['mcs-right'].value:
            # if right half has lower MCS
            # remove right half
            assert 0 < max_throughput['idx'] < idx
            return max_throughput['idx'], idx, max_throughput['mcs-left'], max_throughput['mcs-right']
        elif max_throughput['mcs-left'] == max_throughput['mcs-right']:
            # no cut may increase resource efficiency
            return -1, -1, None, None
        else:
            raise ValueError(f'Input:{array} Max throughput:{max_throughput}')

    @staticmethod
    def subarray(subarray: List[Union[G_MCS, E_MCS]]) -> Tuple[Union[None, G_MCS, E_MCS], float]:
        if not subarray:
            return None, 0.0
        min_mcs: Union[G_MCS, E_MCS] = min(subarray, key=lambda m: m.value)
        throughput: float = min_mcs.value * len(subarray)
        return min_mcs, throughput
