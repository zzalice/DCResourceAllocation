import pickle
from typing import Dict

import pytest

from src.channel_model.sinr import ChannelModel
from src.resource_allocation.algo.phase3 import Phase3
from src.resource_allocation.algo.space import Space
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.resource_allocation.ds.util_enum import E_MCS, G_MCS, LTEResourceBlock, Numerology, SINRtoMCS
from src.resource_allocation.ds.util_type import Coordinate
from src.resource_allocation.ds.zone import Zone

visualize_the_algo = True


def visualize_file(mode: str, title: str, phase3: Phase3):
    if visualize_the_algo:
        with open("../utils/frame_visualizer/vis_test_phase3" + ".P", mode) as file:
            pickle.dump([title,
                         phase3.gnb.frame, phase3.enb.frame, 0,
                         {"allocated": phase3.gue_allocated, "unallocated": phase3.gue_unallocated},
                         {"allocated": phase3.due_allocated, "unallocated": phase3.due_unallocated},
                         {"allocated": phase3.eue_allocated, "unallocated": phase3.eue_unallocated}],
                        file)


@pytest.fixture(scope="module")
def enb():
    return ENodeB(coordinate=Coordinate(0.0, 0.0), radius=0.5)


@pytest.fixture(scope="module")
def gnb():
    return GNodeB(coordinate=Coordinate(0.4, 0.0), radius=0.1)


@pytest.fixture(scope="module")
def gue(gnb, enb):
    gue = GUserEquipment(820, [Numerology.N1, Numerology.N2], Coordinate(0.45, 0.0))  # CQI 15
    gue.register_nb(enb, gnb)
    gue.set_numerology(Numerology.N2)
    zone: Zone = Zone((gue,), gnb)
    gnb.frame.layer[0].allocate_zone(zone)  # (0, 0) to (35, 15)
    assert len(gue.gnb_info.rb) == 38
    return gue


@pytest.fixture(scope="module")
def due_gnb(enb, gnb):
    due = DUserEquipment(264, [Numerology.N1, Numerology.N2], Coordinate(0.5, 0.0))
    due.register_nb(enb, gnb)
    due.set_numerology(Numerology.N2)
    g_sinr = 10
    for i in range(40, 47, due.numerology_in_use.freq):
        for j in range(0, gnb.frame.frame_time, due.numerology_in_use.time):
            rb = gnb.frame.layer[0].allocate_resource_block(i, j, due)
            rb.sinr = g_sinr  # CQI 7~4
            g_sinr -= 0.5
    assert len(due.gnb_info.rb) == 8
    return due


@pytest.fixture(scope="module")
def eue(gnb, enb):
    eue = EUserEquipment(395, [LTEResourceBlock.E], Coordinate(0.45, 0.0))
    eue.register_nb(enb, gnb)
    e_sinr = 6.4
    for i in range(20, 25, eue.numerology_in_use.freq):
        for j in range(0, enb.frame.frame_time, eue.numerology_in_use.time):
            rb = enb.frame.layer[0].allocate_resource_block(i, j, eue)
            rb.sinr = e_sinr  # CQI 7~5, 3個CQI7, 4個CQI6, 4個CQI5
            e_sinr += 0.4
    assert len(eue.enb_info.rb) == 10
    return eue


@pytest.fixture(scope="module")
def due_enb(gnb, enb):
    due = DUserEquipment(395, [Numerology.N2], Coordinate(0.45, 0.0))
    due.register_nb(enb, gnb)
    e_sinr = 10
    for i in range(25, 30, LTEResourceBlock.E.freq):
        for j in range(0, enb.frame.frame_time, LTEResourceBlock.E.time):
            rb = enb.frame.layer[0].allocate_resource_block(i, j, due)
            rb.sinr = e_sinr  # CQI 7~5, 3個CQI7, 4個CQI6, 4個CQI5
            e_sinr -= 0.4
    assert len(due.enb_info.rb) == 10
    assert len(due.gnb_info.rb) == 0
    return due


@pytest.fixture(scope="module")
def due_cross_bs(gnb, enb):
    """這個UE跨基地台，adjust_mcs仍然能依據mcs efficiency移除較差的RB"""
    due = DUserEquipment(656, [Numerology.N1, Numerology.N2], Coordinate(0.48, 0.0))
    due.register_nb(enb, gnb)
    due.set_numerology(Numerology.N2)
    g_sinr = 7.6
    for i in range(50, 77, due.numerology_in_use.freq):
        for j in range(0, gnb.frame.frame_time, due.numerology_in_use.time):
            rb = gnb.frame.layer[0].allocate_resource_block(i, j, due)
            rb.sinr = g_sinr  # CQI 6: 3, CQI 5: 25
            g_sinr -= 0.1
    assert len(due.gnb_info.rb) == 28
    for i in range(0, 5, LTEResourceBlock.E.freq):
        for j in range(0, enb.frame.frame_time, LTEResourceBlock.E.time):
            rb = enb.frame.layer[0].allocate_resource_block(i, j, due)
            rb.sinr = 5  # CQI 5: 10
    assert len(due.enb_info.rb) == 10
    return due


@pytest.fixture(scope="module")
def gue_out_one(gnb, enb):
    """倒數第二的RB沒有out of range，所“暫時移除最差的RB”這個方法仍然能讓這個UE不被淘汰"""
    gue = GUserEquipment(22, [Numerology.N1], Coordinate(0.5, 0.0))
    gue.register_nb(enb, gnb)
    gue.set_numerology(Numerology.N1)
    g_sinr = -1
    for i in range(48, 50, gue.numerology_in_use.freq):
        for j in range(0, gnb.frame.frame_time, gue.numerology_in_use.time):
            rb = gnb.frame.layer[0].allocate_resource_block(i, j, gue)
            rb.sinr = g_sinr  # CQI 0~1
            g_sinr -= 1
    assert len(gue.gnb_info.rb) == 2
    return gue


@pytest.fixture(scope="module")
def gue_out_two(gnb, enb):
    """倒數兩個RB CQI都=0，out of range，即使有一個最好的RB能滿足QoS，用“暫時移除最差的RB”這個方法仍然會將這個UE剔除"""
    gue = GUserEquipment(22, [Numerology.N1], Coordinate(0.5, 0.0))
    gue.register_nb(enb, gnb)
    gue.set_numerology(Numerology.N1)
    g_sinr = -3
    for i in range(78, 84, gue.numerology_in_use.freq):
        for j in range(0, gnb.frame.frame_time, gue.numerology_in_use.time):
            rb = gnb.frame.layer[0].allocate_resource_block(i, j, gue)
            rb.sinr = g_sinr  # CQI 0~4
            g_sinr += 1
    assert len(gue.gnb_info.rb) == 6
    return gue


@pytest.fixture(scope="module")
def gue_moderate_1st(enb, gnb):
    gue = GUserEquipment(352, [Numerology.N2], Coordinate(0.5, 0.0))
    gue.register_nb(enb, gnb)
    gue.set_numerology(Numerology.N2)
    for i in range(84, 100, gue.numerology_in_use.freq):
        for j in range(0, gnb.frame.frame_time, gue.numerology_in_use.time):
            rb = gnb.frame.layer[0].allocate_resource_block(i, j, gue)
            rb.sinr = -1  # CQI 1
    assert len(gue.gnb_info.rb) == 16
    return gue


@pytest.fixture(scope="module")
def gue_moderate_2nd(enb, gnb):
    gue = GUserEquipment(352, [Numerology.N2], Coordinate(0.5, 0.0))
    gue.register_nb(enb, gnb)
    gue.set_numerology(Numerology.N2)
    for i in range(84, 100, gue.numerology_in_use.freq):
        for j in range(0, gnb.frame.frame_time, gue.numerology_in_use.time):
            rb = gnb.frame.layer[1].allocate_resource_block(i, j, gue)
            rb.sinr = -1  # CQI 1
    assert len(gue.gnb_info.rb) == 16
    return gue


@pytest.fixture(scope="module")
def gue_excellent(enb, gnb):
    gue = GUserEquipment(2956, [Numerology.N2], Coordinate(0.5, 0.0))
    gue.register_nb(enb, gnb)
    gue.set_numerology(Numerology.N2)
    for i in range(100, 103, gue.numerology_in_use.freq):
        for j in range(0, gnb.frame.frame_time, gue.numerology_in_use.time):
            rb = gnb.frame.layer[0].allocate_resource_block(i, j, gue)
            rb.sinr = 29  # CQI 14
    assert len(gue.gnb_info.rb) == 4
    return gue


@pytest.fixture(scope="module")
def gue_bad(enb, gnb):
    ue = GUserEquipment(352, [Numerology.N2], Coordinate(0.5, 0.0))
    ue.register_nb(enb, gnb)
    ue.set_numerology(Numerology.N2)
    for i in range(171, 187, ue.numerology_in_use.freq):
        for j in range(0, gnb.frame.frame_time, ue.numerology_in_use.time):
            rb = gnb.frame.layer[0].allocate_resource_block(i, j, ue)
            rb.sinr = -1  # CQI 1
    assert len(ue.gnb_info.rb) == 16
    for rb in ue.gnb_info.rb:
        assert rb.mcs == G_MCS.CQI1_QPSK
    return ue


@pytest.fixture(scope="module")
def channel_model(gnb, enb):
    """先讓系統外的干擾=0，也就是沒有random基地台的干擾"""
    cochannel_bw = 25
    cm = ChannelModel({"g_freq": gnb.frame.frame_freq,
                       "e_freq": enb.frame.frame_freq,
                       "co_bandwidth": cochannel_bw})
    channel_bs = []
    for i in range(enb.frame.frame_freq + gnb.frame.frame_freq - cochannel_bw):
        channel_bs.append([])
    cm.channel_bs = tuple(channel_bs)
    return cm


@pytest.fixture(scope="module")
def phase3(channel_model, gnb, enb, gue, due_gnb, eue, due_enb, due_cross_bs, gue_out_one, gue_out_two,
           gue_moderate_1st, gue_moderate_2nd, gue_excellent, gue_bad):
    return Phase3(channel_model, gnb, enb,
                  ((gue, gue_out_one, gue_out_two, gue_moderate_1st, gue_moderate_2nd, gue_excellent, gue_bad),
                   (due_gnb, due_enb, due_cross_bs), (eue,)),
                  ((), (), ()))


def sorted_rb(rb_list):
    old_rb = rb_list[0]
    for rb in rb_list[1:]:
        assert old_rb.sinr >= rb.sinr
        old_rb = rb


def throughput_range(ue):
    gnb_throughput = 0.0
    enb_throughput = 0.0
    if hasattr(ue, 'gnb_info') and ue.gnb_info.rb:
        gnb_throughput = len(ue.gnb_info.rb) * ue.gnb_info.mcs.value
        assert ue.throughput <= ue.request_data_rate + ue.gnb_info.mcs.value
    if hasattr(ue, 'enb_info') and ue.enb_info.rb:
        enb_throughput = len(ue.enb_info.rb) * ue.enb_info.mcs.value
        assert ue.throughput <= ue.request_data_rate + ue.enb_info.mcs.value
    assert gnb_throughput + enb_throughput == ue.throughput
    assert ue.throughput >= ue.request_data_rate


def test_adjust_mcs(phase3, gue, due_gnb, eue, due_enb, due_cross_bs, gue_out_one, gue_out_two):
    visualize_file("wb", "test_adjust_mcs", phase3)

    # [test]gue
    phase3.channel_model.sinr_ue(gue)
    phase3.adjust_mcs(gue)
    sorted_rb(gue.gnb_info.rb)
    assert SINRtoMCS.sinr_to_mcs(gue.gnb_info.rb[-1].sinr, gue.gnb_info.nb_type) == gue.gnb_info.mcs
    throughput_range(gue)

    # [test]due cross BSs
    phase3.adjust_mcs(due_cross_bs)
    sorted_rb(due_cross_bs.gnb_info.rb)
    sorted_rb(due_cross_bs.enb_info.rb)
    assert SINRtoMCS.sinr_to_mcs(due_cross_bs.gnb_info.rb[-1].sinr, phase3.gnb.nb_type) == due_cross_bs.gnb_info.mcs
    assert SINRtoMCS.sinr_to_mcs(due_cross_bs.enb_info.rb[-1].sinr, phase3.enb.nb_type) == due_cross_bs.enb_info.mcs
    throughput_range(due_cross_bs)
    assert len(due_cross_bs.gnb_info.rb) == 3
    assert len(due_cross_bs.enb_info.rb) == 2
    assert due_cross_bs.gnb_info.mcs == G_MCS.CQI6_QPSK
    assert due_cross_bs.enb_info.mcs == E_MCS.CQI5_QPSK

    # [test]due_gnb
    phase3.adjust_mcs(due_gnb)
    sorted_rb(due_gnb.gnb_info.rb)
    assert SINRtoMCS.sinr_to_mcs(due_gnb.gnb_info.rb[-1].sinr, phase3.gnb.nb_type) == due_gnb.gnb_info.mcs
    throughput_range(due_gnb)
    assert len(due_gnb.gnb_info.rb) == 2
    assert len(due_gnb.enb_info.rb) == 0
    assert due_gnb.gnb_info.mcs == G_MCS.CQI7_16QAM
    assert due_gnb.enb_info.mcs is None

    # [test]eue
    phase3.adjust_mcs(eue)
    sorted_rb(eue.enb_info.rb)
    assert SINRtoMCS.sinr_to_mcs(eue.enb_info.rb[-1].sinr, phase3.enb.nb_type) == eue.enb_info.mcs
    throughput_range(eue)
    assert len(eue.enb_info.rb) == 4
    assert eue.enb_info.mcs == E_MCS.CQI6_QPSK

    # [test]due_enb
    phase3.adjust_mcs(due_enb)
    sorted_rb(due_enb.enb_info.rb)
    assert SINRtoMCS.sinr_to_mcs(due_enb.enb_info.rb[-1].sinr, phase3.enb.nb_type) == due_enb.enb_info.mcs
    throughput_range(due_enb)
    assert len(due_enb.enb_info.rb) == 4
    assert len(due_enb.gnb_info.rb) == 0
    assert due_enb.enb_info.mcs == E_MCS.CQI6_QPSK
    assert due_enb.gnb_info.mcs is None

    # [test]gue_out_one
    assert gue_out_one.is_allocated is True
    assert gue_out_one.is_to_recalculate_mcs is True
    phase3.adjust_mcs(gue_out_one)
    assert gue_out_one.is_allocated is True
    assert gue_out_one.is_to_recalculate_mcs is False
    assert len(gue_out_one.gnb_info.rb) == 1
    assert gue_out_one.gnb_info.mcs == G_MCS.CQI1_QPSK
    assert gue_out_one.throughput == G_MCS.CQI1_QPSK.value

    # [test]gue_out_two
    assert gue_out_two.is_allocated is True
    assert gue_out_two.is_to_recalculate_mcs is True
    phase3.adjust_mcs(gue_out_two)
    assert gue_out_two.is_allocated is False
    assert gue_out_two.is_to_recalculate_mcs is False
    assert len(gue_out_two.gnb_info.rb) == 0
    assert gue_out_two.gnb_info.mcs is None
    assert gue_out_two.throughput == 0.0

    # [test]ue overlapped, effected UEs

    # [test]hung

    visualize_file("ab+", "test_adjust_mcs_finish", phase3)


def space_restored(space: Space):
    for i in range(space.starting_i, space.ending_i + 1):
        for j in range(space.starting_j, space.ending_j + 1):
            assert space.layer.bu[i][j].is_used is False


def test_allocated_ue_to_space(phase3, gue_moderate_1st, gue_moderate_2nd, due_gnb, gue, gue_excellent):
    visualize_file("ab+", "test_allocated_ue_to_space", phase3)

    phase3.adjust_mcs(gue_moderate_1st)
    assert len(gue_moderate_1st.gnb_info.rb) == 16
    phase3.adjust_mcs(gue_moderate_2nd)
    assert len(gue_moderate_2nd.gnb_info.rb) == 16
    phase3.adjust_mcs(gue_excellent)
    assert len(gue_excellent.gnb_info.rb) == 4

    phase3.store()

    """ [test] UE overlapped with itself & next RB & running out of space
        兩個跟自己重疊的RB """
    space_lap_itself = Space(phase3.gnb.frame.layer[1], 40, 0, 43, 7)
    old_num_rb = len(due_gnb.gnb_info.rb)
    assert phase3.allocated_ue_to_space(due_gnb, space_lap_itself, due_gnb.gnb_info.mcs) is False  # 該call space.next_nb
    # # 測試space.next_rb是否被呼叫，Option 1
    # from unittest.mock import MagicMock
    # space_lap_itself.next_rb = MagicMock()
    # assert space_lap_itself.next_rb.called
    # # 測試space.next_rb是否被呼叫，Option 2
    # from mock import patch
    # with patch.object(space_lap_itself, 'next_rb') as mock:
    #     assert phase3.allocated_ue_to_space(due_gnb, space_lap_itself, due_gnb.gnb_info.mcs) is False
    #     mock.assert_called_once_with()
    phase3.restore(space_lap_itself)
    space_restored(space_lap_itself)
    assert len(due_gnb.gnb_info.rb) == old_num_rb

    """ [test] the mcs of new RB is lower than the mcs the UE is currently using & next RB & running out of space
        沒有跟自己重疊的空間，但是有跟別人重疊且SINR會很差的RB，自己的CQI=15 """
    space_bad_mcs = Space(phase3.gnb.frame.layer[1], 48, 0, 53, 7)
    old_num_rb = len(gue.gnb_info.rb)
    assert phase3.allocated_ue_to_space(gue, space_bad_mcs, gue.gnb_info.mcs) is False  # 該call space.next_nb
    phase3.restore(space_bad_mcs)
    space_restored(space_bad_mcs)
    assert len(gue.gnb_info.rb) == old_num_rb

    """ [test] the gUE moving to the space lower down two original UEs' MCS in gNB
        沒有跟自己重疊的空間，但是有跟別人重疊且別人的rx很小。自己的SINR=100(超級好)，重疊的人的原本CQI=5(保證重疊後一定會變差) 
        目前是失敗的，因為gue_moderate_1st, gue_moderate_2nd的SINR高達34，CQI 15"""
    # space_not_bad_for_me = Space(gnb.frame.layer[2], 84, 0, 100, 15)
    # assert phase3.allocated_ue_to_space(gue_excellent, space_not_bad_for_me, gue_excellent.gnb_info.mcs) is False
    # # 應呼叫phase3.effected_ue並讓gue_moderate_1st跟2nd傳入adjust_mcs
    # phase3.restore()

    """ [test] the space is suitable for this ue     # return True
        原本有跟人重疊(SINR小)，新空間沒跟人重疊(SINR大) """
    space_clean = Space(phase3.gnb.frame.layer[0], 104, 0, 130, 15)
    old_num_rb = len(gue_moderate_1st.gnb_info.rb)
    assert phase3.allocated_ue_to_space(gue_moderate_1st, space_clean, gue_moderate_1st.gnb_info.mcs) is True
    phase3.restore(space_clean)
    space_restored(space_clean)  # TODO: restore fail.
    assert len(gue_moderate_1st.gnb_info.rb) == old_num_rb

    """ [test]co-channel"""

    visualize_file("ab+", "test_allocated_ue_to_space_finish", phase3)


def test_calc_weight(phase3, gue_bad):
    for rb in gue_bad.gnb_info.rb:
        assert rb.mcs == G_MCS.CQI1_QPSK
    phase3.adjust_mcs(gue_bad)
    assert len(gue_bad.gnb_info.rb) == 16
    old_phase3 = phase3

    space_clean = Space(phase3.gnb.frame.layer[0], 104, 0, 130, 15)  # TODO: restore有成功的話，應該要能用
    space_random = Space(phase3.gnb.frame.layer[0], 131, 0, 170, 15)
    space_random_e = Space(phase3.enb.frame.layer[0], 5, 0, 19, 15)
    weight: Dict[str, Dict[str, float]] = phase3.calc_weight(gue_bad.gnb_info.mcs, [gue_bad],
                                                             (space_clean, space_random),
                                                             (space_random_e,))  # TODO: 加回space_clean

    """ [test] restore """
    assert old_phase3 is phase3
    assert len(gue_bad.gnb_info.rb) == 16  # TODO: restore fail
    space_restored(space_clean)
    space_restored(space_random)
    space_restored(space_random_e)

    """ [test] calc_num_bu """
    assert weight[str(gue_bad.uuid)][str(space_random.uuid)] >= 240  # 15*16，gue_bad少15個RB
    assert weight[str(gue_bad.uuid)].get(str(space_random_e.uuid)) is None


def test_matching():
    pass
    # one UE


def test_fixture(phase3, gnb, gue_bad):
    phase3.store()
    assert not phase3.gnb.frame.layer[2].bu[0][0].is_used
    assert not gnb.frame.layer[2].bu[0][0].is_used
    phase3.gnb.frame.layer[2].allocate_resource_block(0, 0, gue_bad)
    assert phase3.gnb.frame.layer[2].bu[0][0].is_used
    assert not gnb.frame.layer[2].bu[0][0].is_used  # 如果run整個test_phase3.py，會is_used return false
    phase3.restore()
    assert not phase3.gnb.frame.layer[2].bu[0][0].is_used
    assert not gnb.frame.layer[2].bu[0][0].is_used  # restore以後phase 3的gnb和創造phase3的gnb不再相同。call by sharing那類的特性，導致phase3.gnb和gnb不同步
