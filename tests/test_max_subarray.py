from src.resource_allocation.algo.max_subarray import MaxSubarray
from src.resource_allocation.ds.util_enum import G_MCS


def test_max_subarray():
    assert MaxSubarray().max_subarray([G_MCS.CQI5_QPSK, G_MCS.CQI4_QPSK, G_MCS.CQI2_QPSK, G_MCS.CQI3_QPSK, G_MCS.CQI3_QPSK, G_MCS.CQI3_QPSK]) == (2, 6, G_MCS.CQI4_QPSK, G_MCS.CQI2_QPSK)
    assert MaxSubarray().max_subarray([G_MCS.CQI3_QPSK, G_MCS.CQI1_QPSK, G_MCS.CQI2_QPSK, G_MCS.CQI7_16QAM, G_MCS.CQI5_QPSK]) == (0, 3, G_MCS.CQI5_QPSK, G_MCS.CQI1_QPSK)
    assert MaxSubarray().max_subarray([G_MCS.CQI5_QPSK, G_MCS.CQI4_QPSK, G_MCS.CQI2_QPSK, G_MCS.CQI3_QPSK, G_MCS.CQI2_QPSK, G_MCS.CQI7_16QAM, G_MCS.CQI6_QPSK]) == (0, 5, G_MCS.CQI6_QPSK, G_MCS.CQI2_QPSK)
    assert MaxSubarray().max_subarray([G_MCS.CQI2_QPSK, G_MCS.CQI2_QPSK, G_MCS.CQI2_QPSK, G_MCS.CQI5_QPSK, G_MCS.CQI2_QPSK]) == (5, 5, G_MCS.CQI2_QPSK, None)
    assert MaxSubarray().max_subarray([G_MCS.CQI3_QPSK]) == (1, 1, G_MCS.CQI3_QPSK, None)
    assert MaxSubarray().max_subarray([G_MCS.CQI5_QPSK, G_MCS.CQI4_QPSK, G_MCS.CQI3_QPSK, G_MCS.CQI3_QPSK, G_MCS.CQI2_QPSK, G_MCS.CQI5_QPSK]) == (2, 6, G_MCS.CQI4_QPSK, G_MCS.CQI2_QPSK)