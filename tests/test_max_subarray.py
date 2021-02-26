from src.resource_allocation.algo.max_subarray import MaxSubarray
from src.resource_allocation.ds.util_enum import G_MCS


def test_max_subarray():
    assert MaxSubarray().max_subarray([G_MCS.CQI14_64QAM, G_MCS.CQI14_64QAM, G_MCS.CQI12_64QAM, G_MCS.CQI12_64QAM, G_MCS.CQI2_QPSK, G_MCS.CQI2_QPSK, G_MCS.CQI2_QPSK, G_MCS.CQI2_QPSK]) == {'rm_from': 4, 'rm_to': 8, 'new_mcs': G_MCS.CQI12_64QAM, 'lower_mcs': G_MCS.CQI2_QPSK}
    assert MaxSubarray().max_subarray([G_MCS.CQI5_QPSK, G_MCS.CQI4_QPSK, G_MCS.CQI2_QPSK, G_MCS.CQI3_QPSK, G_MCS.CQI3_QPSK, G_MCS.CQI3_QPSK]) == {'rm_from': 2, 'rm_to': 6, 'new_mcs': G_MCS.CQI4_QPSK, 'lower_mcs': G_MCS.CQI2_QPSK}
    assert MaxSubarray().max_subarray([G_MCS.CQI3_QPSK, G_MCS.CQI1_QPSK, G_MCS.CQI2_QPSK, G_MCS.CQI7_16QAM, G_MCS.CQI5_QPSK]) == {'rm_from': 0, 'rm_to': 3, 'new_mcs': G_MCS.CQI5_QPSK, 'lower_mcs': G_MCS.CQI1_QPSK}
    assert MaxSubarray().max_subarray([G_MCS.CQI5_QPSK, G_MCS.CQI4_QPSK, G_MCS.CQI2_QPSK, G_MCS.CQI3_QPSK, G_MCS.CQI2_QPSK, G_MCS.CQI7_16QAM, G_MCS.CQI6_QPSK]) == {'rm_from': 0, 'rm_to': 5, 'new_mcs': G_MCS.CQI6_QPSK, 'lower_mcs': G_MCS.CQI2_QPSK}
    assert MaxSubarray().max_subarray([G_MCS.CQI5_QPSK, G_MCS.CQI4_QPSK, G_MCS.CQI3_QPSK, G_MCS.CQI3_QPSK, G_MCS.CQI2_QPSK, G_MCS.CQI5_QPSK]) == {'rm_from': 2, 'rm_to': 6, 'new_mcs': G_MCS.CQI4_QPSK, 'lower_mcs': G_MCS.CQI2_QPSK}
    assert MaxSubarray().max_subarray([G_MCS.CQI2_QPSK, G_MCS.CQI2_QPSK, G_MCS.CQI2_QPSK, G_MCS.CQI5_QPSK, G_MCS.CQI2_QPSK]) is None
    assert MaxSubarray().max_subarray([G_MCS.CQI3_QPSK]) is None
    assert MaxSubarray().max_subarray([G_MCS.CQI2_QPSK, G_MCS.CQI2_QPSK, G_MCS.CQI2_QPSK, G_MCS.CQI2_QPSK, G_MCS.CQI2_QPSK, G_MCS.CQI2_QPSK]) is None
    assert MaxSubarray().max_subarray([G_MCS.CQI2_QPSK, G_MCS.CQI2_QPSK]) is None
    try:
        assert MaxSubarray().max_subarray([])
    except AssertionError:
        pass
