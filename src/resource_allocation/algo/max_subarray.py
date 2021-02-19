from typing import Dict, List, Tuple, Union

from src.resource_allocation.ds.util_enum import E_MCS, G_MCS


class MaxSubarray:
    """
    Find the cut of an array into two half with highest throughput.
    Remove the half with lower CQI.

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
                                                                int, int, Union[G_MCS, E_MCS], Union[G_MCS, E_MCS]]:
        """
        To cut part of the allocated RB to the other BS for dUE.
        :param array: The MCS of the RBs of ONE UE in ONE BS.
        :return: The index range of the RBs to move to the other BS,
                 the MCS of the better half, and the MCS of the lower half.
        """
        assert array, "Input empty list."
        max_throughput: Dict = {'idx': 1, 'cqi-left': array[0], 'cqi-right': (self.subarray(array[1:]))[0],
                                'throughput': array[0].value + (self.subarray(array[1:]))[1]}

        cqi_left: Union[G_MCS, E_MCS] = max_throughput['cqi-left']
        idx: int = 1
        for cqi in array[1:]:
            idx += 1
            if cqi.value < cqi_left.value:
                cqi_left = cqi
            throughput_left: float = cqi_left.value * idx
            cqi_right, throughput_right = self.subarray(array[idx:])
            throughput = throughput_left + throughput_right
            if throughput >= max_throughput['throughput']:
                max_throughput['idx'] = idx
                max_throughput['cqi-left'] = cqi_left
                max_throughput['cqi-right'] = cqi_right
                max_throughput['throughput'] = throughput
        if not max_throughput['cqi-right'] or max_throughput['cqi-left'].value >= max_throughput['cqi-right'].value:
            # if the input list len == 1 OR right half has lower MCS
            # remove right half
            assert max_throughput['idx'] <= idx
            return max_throughput['idx'], idx, max_throughput['cqi-left'], max_throughput['cqi-right']
        else:
            # remove left half
            assert 0 <= max_throughput['idx']
            return 0, max_throughput['idx'], max_throughput['cqi-right'], max_throughput['cqi-left']

    @staticmethod
    def subarray(subarray: List[Union[G_MCS, E_MCS]]) -> Tuple[Union[None, G_MCS, E_MCS], float]:
        if not subarray:
            return None, 0.0
        min_cqi: Union[G_MCS, E_MCS] = subarray[0]
        for m in subarray:
            min_cqi = m if m.value < min_cqi.value else min_cqi
        throughput: float = min_cqi.value * len(subarray)
        return min_cqi, throughput
