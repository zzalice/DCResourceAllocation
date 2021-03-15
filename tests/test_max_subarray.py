from src.resource_allocation.algo.max_subarray import MaxSubarray
from src.resource_allocation.ds.util_enum import G_MCS


def test_max_subarray():
    assert MaxSubarray().max_subarray([G_MCS.CQI14, G_MCS.CQI14, G_MCS.CQI12, G_MCS.CQI12, G_MCS.CQI2, G_MCS.CQI2, G_MCS.CQI2, G_MCS.CQI2]) == {'rm_from': 4, 'rm_to': 8, 'new_mcs': G_MCS.CQI12, 'lower_mcs': G_MCS.CQI2}
    assert MaxSubarray().max_subarray([G_MCS.CQI5, G_MCS.CQI4, G_MCS.CQI2, G_MCS.CQI3, G_MCS.CQI3, G_MCS.CQI3]) == {'rm_from': 2, 'rm_to': 6, 'new_mcs': G_MCS.CQI4, 'lower_mcs': G_MCS.CQI2}
    assert MaxSubarray().max_subarray([G_MCS.CQI3, G_MCS.CQI1, G_MCS.CQI2, G_MCS.CQI7, G_MCS.CQI5]) == {'rm_from': 0, 'rm_to': 3, 'new_mcs': G_MCS.CQI5, 'lower_mcs': G_MCS.CQI1}
    assert MaxSubarray().max_subarray([G_MCS.CQI5, G_MCS.CQI4, G_MCS.CQI2, G_MCS.CQI3, G_MCS.CQI2, G_MCS.CQI7, G_MCS.CQI6]) == {'rm_from': 0, 'rm_to': 5, 'new_mcs': G_MCS.CQI6, 'lower_mcs': G_MCS.CQI2}
    assert MaxSubarray().max_subarray([G_MCS.CQI5, G_MCS.CQI4, G_MCS.CQI3, G_MCS.CQI3, G_MCS.CQI2, G_MCS.CQI5]) == {'rm_from': 2, 'rm_to': 6, 'new_mcs': G_MCS.CQI4, 'lower_mcs': G_MCS.CQI2}
    assert MaxSubarray().max_subarray([G_MCS.CQI2, G_MCS.CQI2, G_MCS.CQI2, G_MCS.CQI5, G_MCS.CQI2]) is None
    assert MaxSubarray().max_subarray([G_MCS.CQI3]) is None
    assert MaxSubarray().max_subarray([G_MCS.CQI2, G_MCS.CQI2, G_MCS.CQI2, G_MCS.CQI2, G_MCS.CQI2, G_MCS.CQI2]) is None
    assert MaxSubarray().max_subarray([G_MCS.CQI2, G_MCS.CQI2]) is None
    try:
        assert MaxSubarray().max_subarray([])
    except AssertionError:
        pass
