import pickle

import pytest

visualize_the_algo = True


@pytest.fixture
def enb():
    from src.resource_allocation.ds.util_type import Coordinate
    from src.resource_allocation.ds.eutran import ENodeB
    return ENodeB(coordinate=Coordinate(0.0, 0.0), radius=0.5)


@pytest.fixture()
def gnb():
    from src.resource_allocation.ds.ngran import GNodeB
    from src.resource_allocation.ds.util_type import Coordinate
    return GNodeB(coordinate=Coordinate(0.4, 0.0), radius=0.1)


@pytest.fixture()
def layer_g_0(gnb):
    return gnb.frame.layer[0]


@pytest.fixture()
def layer_e(enb):
    return enb.frame.layer[0]


@pytest.fixture()
def gue(gnb, enb, layer_g_0):
    from src.resource_allocation.ds.ngran import GUserEquipment
    from src.resource_allocation.ds.util_enum import Numerology
    from src.resource_allocation.ds.util_type import Coordinate
    from src.resource_allocation.ds.zone import Zone

    gue = GUserEquipment(820, [Numerology.N1, Numerology.N2], Coordinate(0.45, 0.0))
    gue.register_nb(enb, gnb)
    gue.set_numerology(Numerology.N2)
    zone: Zone = Zone((gue,), gnb)
    layer_g_0.allocate_zone(zone)  # (0, 0) to (35, 15)
    assert len(gue.gnb_info.rb) == 38
    return gue


@pytest.fixture()
def due_gnb(enb, gnb, layer_g_0):
    pass
    from src.resource_allocation.ds.ngran import DUserEquipment
    from src.resource_allocation.ds.util_enum import Numerology
    from src.resource_allocation.ds.util_type import Coordinate
    due = DUserEquipment(264, [Numerology.N1, Numerology.N2], Coordinate(0.5, 0.0))
    due.register_nb(enb, gnb)
    due.set_numerology(Numerology.N2)
    g_sinr = 10
    for i in range(40, 47, due.numerology_in_use.freq):
        for j in range(0, gnb.frame.frame_time, due.numerology_in_use.time):
            rb = layer_g_0.allocate_resource_block(i, j, due)
            rb.sinr = g_sinr  # CQI 7~4
            g_sinr -= 0.5
    assert len(due.gnb_info.rb) == 8
    return due


@pytest.fixture()
def eue(gnb, enb, layer_e):
    from src.resource_allocation.ds.eutran import EUserEquipment
    from src.resource_allocation.ds.util_enum import LTEResourceBlock
    from src.resource_allocation.ds.util_type import Coordinate
    eue = EUserEquipment(395, [LTEResourceBlock.E], Coordinate(0.45, 0.0))
    eue.register_nb(enb, gnb)
    e_sinr = 6.4
    for i in range(20, 25, eue.numerology_in_use.freq):
        for j in range(0, enb.frame.frame_time, eue.numerology_in_use.time):
            rb = layer_e.allocate_resource_block(i, j, eue)
            rb.sinr = e_sinr  # CQI 7~5, 3個CQI7, 4個CQI6, 4個CQI5
            e_sinr += 0.4
    assert len(eue.enb_info.rb) == 10
    return eue


@pytest.fixture()
def due_enb(gnb, enb, layer_e):
    from src.resource_allocation.ds.ngran import DUserEquipment
    from src.resource_allocation.ds.util_enum import Numerology
    from src.resource_allocation.ds.util_type import Coordinate
    from src.resource_allocation.ds.util_enum import LTEResourceBlock
    due = DUserEquipment(395, [Numerology.N2], Coordinate(0.45, 0.0))
    due.register_nb(enb, gnb)
    e_sinr = 10
    for i in range(25, 30, LTEResourceBlock.E.freq):
        for j in range(0, enb.frame.frame_time, LTEResourceBlock.E.time):
            rb = layer_e.allocate_resource_block(i, j, due)
            rb.sinr = e_sinr  # CQI 7~5, 3個CQI7, 4個CQI6, 4個CQI5
            e_sinr -= 0.4
    assert len(due.enb_info.rb) == 10
    assert len(due.gnb_info.rb) == 0
    return due


@pytest.fixture()
def due_cross_bs(gnb, enb, layer_g_0, layer_e):
    from src.resource_allocation.ds.ngran import DUserEquipment
    from src.resource_allocation.ds.util_type import Coordinate
    from src.resource_allocation.ds.util_enum import Numerology
    from src.resource_allocation.ds.util_enum import LTEResourceBlock
    due = DUserEquipment(656, [Numerology.N1, Numerology.N2], Coordinate(0.48, 0.0))
    due.register_nb(enb, gnb)
    due.set_numerology(Numerology.N2)
    g_sinr = 7.6
    for i in range(50, 77, due.numerology_in_use.freq):
        for j in range(0, gnb.frame.frame_time, due.numerology_in_use.time):
            rb = layer_g_0.allocate_resource_block(i, j, due)
            rb.sinr = g_sinr  # CQI 6: 3, CQI 5: 25
            g_sinr -= 0.1
    assert len(due.gnb_info.rb) == 28
    for i in range(0, 5, LTEResourceBlock.E.freq):
        for j in range(0, enb.frame.frame_time, LTEResourceBlock.E.time):
            rb = layer_e.allocate_resource_block(i, j, due)
            rb.sinr = 5  # CQI 5: 10
    assert len(due.enb_info.rb) == 10
    return due


@pytest.fixture()
def gue_out_one(gnb, enb, layer_g_0):
    from src.resource_allocation.ds.ngran import GUserEquipment
    from src.resource_allocation.ds.util_enum import Numerology
    from src.resource_allocation.ds.util_type import Coordinate
    gue = GUserEquipment(22, [Numerology.N1], Coordinate(0.5, 0.0))
    gue.register_nb(enb, gnb)
    gue.set_numerology(Numerology.N1)
    g_sinr = -1
    for i in range(48, 50, gue.numerology_in_use.freq):
        for j in range(0, gnb.frame.frame_time, gue.numerology_in_use.time):
            rb = layer_g_0.allocate_resource_block(i, j, gue)
            rb.sinr = g_sinr  # CQI 0~1
            g_sinr -= 1
    assert len(gue.gnb_info.rb) == 2
    return gue


@pytest.fixture()
def gue_out_two(gnb, enb, layer_g_0):
    from src.resource_allocation.ds.ngran import GUserEquipment
    from src.resource_allocation.ds.util_enum import Numerology
    from src.resource_allocation.ds.util_type import Coordinate
    gue = GUserEquipment(22, [Numerology.N1], Coordinate(0.5, 0.0))
    gue.register_nb(enb, gnb)
    gue.set_numerology(Numerology.N1)
    g_sinr = -3
    for i in range(78, 84, gue.numerology_in_use.freq):
        for j in range(0, gnb.frame.frame_time, gue.numerology_in_use.time):
            rb = layer_g_0.allocate_resource_block(i, j, gue)
            rb.sinr = g_sinr  # CQI 0~4
            g_sinr += 1
    assert len(gue.gnb_info.rb) == 6
    return gue


@pytest.fixture()
def due_is_hung(gnb, enb):
    pass


@pytest.fixture()
def channel_model(gnb, enb):
    from src.channel_model.sinr import ChannelModel
    return ChannelModel({"g_freq": gnb.frame.frame_freq,
                         "e_freq": enb.frame.frame_freq,
                         "co_bandwidth": 25})


@pytest.fixture()
def phase3(channel_model, gnb, enb, gue, due_gnb, eue, due_enb, due_cross_bs, gue_out_one, gue_out_two, due_is_hung):
    from src.resource_allocation.algo.phase3 import Phase3
    return Phase3(channel_model, gnb, enb,
                  ((gue, gue_out_one, gue_out_two), (due_gnb, due_enb, due_cross_bs, due_is_hung), (eue,)),
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


def test_adjust_mcs(phase3, gnb, enb, gue, due_gnb, eue, due_enb, due_cross_bs, gue_out_one, gue_out_two, due_is_hung):
    if visualize_the_algo:
        with open("../utils/frame_visualizer/vis_test_phase3" + ".P", "wb") as file:
            pickle.dump(["test_adjust_mcs",
                         gnb.frame, enb.frame, 0,
                         {"allocated": (gue, gue_out_one, gue_out_two), "unallocated": ()},
                         {"allocated": (due_gnb, due_enb, due_cross_bs, due_is_hung), "unallocated": ()},
                         {"allocated": (eue,), "unallocated": ()}],
                        file)

    from src.resource_allocation.ds.util_enum import SINRtoMCS
    from src.resource_allocation.ds.util_enum import G_MCS
    from src.resource_allocation.ds.util_enum import E_MCS

    # gue
    phase3.channel_model.sinr_ue(gue)
    phase3.adjust_mcs(gue)
    sorted_rb(gue.gnb_info.rb)
    assert SINRtoMCS.sinr_to_mcs(gue.gnb_info.rb[-1].sinr, gue.gnb_info.nb_type) == gue.gnb_info.mcs
    throughput_range(gue)

    # due cross BSs
    phase3.adjust_mcs(due_cross_bs)
    sorted_rb(due_cross_bs.gnb_info.rb)
    sorted_rb(due_cross_bs.enb_info.rb)
    assert SINRtoMCS.sinr_to_mcs(due_cross_bs.gnb_info.rb[-1].sinr, gnb.nb_type) == due_cross_bs.gnb_info.mcs
    assert SINRtoMCS.sinr_to_mcs(due_cross_bs.enb_info.rb[-1].sinr, enb.nb_type) == due_cross_bs.enb_info.mcs
    throughput_range(due_cross_bs)
    assert len(due_cross_bs.gnb_info.rb) == 3
    assert len(due_cross_bs.enb_info.rb) == 2
    assert due_cross_bs.gnb_info.mcs == G_MCS.CQI6_QPSK
    assert due_cross_bs.enb_info.mcs == E_MCS.CQI5_QPSK

    # due_gnb
    phase3.adjust_mcs(due_gnb)
    sorted_rb(due_gnb.gnb_info.rb)
    assert SINRtoMCS.sinr_to_mcs(due_gnb.gnb_info.rb[-1].sinr, gnb.nb_type) == due_gnb.gnb_info.mcs
    throughput_range(due_gnb)
    assert len(due_gnb.gnb_info.rb) == 2
    assert len(due_gnb.enb_info.rb) == 0
    assert due_gnb.gnb_info.mcs == G_MCS.CQI7_16QAM
    assert due_gnb.enb_info.mcs is None

    # eue
    phase3.adjust_mcs(eue)
    sorted_rb(eue.enb_info.rb)
    assert SINRtoMCS.sinr_to_mcs(eue.enb_info.rb[-1].sinr, enb.nb_type) == eue.enb_info.mcs
    throughput_range(eue)
    assert len(eue.enb_info.rb) == 4
    assert eue.enb_info.mcs == E_MCS.CQI6_QPSK

    # due_enb
    phase3.adjust_mcs(due_enb)
    sorted_rb(due_enb.enb_info.rb)
    assert SINRtoMCS.sinr_to_mcs(due_enb.enb_info.rb[-1].sinr, enb.nb_type) == due_enb.enb_info.mcs
    throughput_range(due_enb)
    assert len(due_enb.enb_info.rb) == 4
    assert len(due_enb.gnb_info.rb) == 0
    assert due_enb.enb_info.mcs == E_MCS.CQI6_QPSK
    assert due_enb.gnb_info.mcs is None

    # gue_out_one
    assert gue_out_one.is_allocated is True
    assert gue_out_one.is_to_recalculate_mcs is True
    phase3.adjust_mcs(gue_out_one)
    assert gue_out_one.is_allocated is True
    assert gue_out_one.is_to_recalculate_mcs is False
    assert len(gue_out_one.gnb_info.rb) == 1
    assert gue_out_one.gnb_info.mcs == G_MCS.CQI1_QPSK
    assert gue_out_one.throughput == G_MCS.CQI1_QPSK.value

    # gue_out_two
    assert gue_out_two.is_allocated is True
    assert gue_out_two.is_to_recalculate_mcs is True
    phase3.adjust_mcs(gue_out_two)
    assert gue_out_two.is_allocated is False
    assert gue_out_two.is_to_recalculate_mcs is False
    assert len(gue_out_two.gnb_info.rb) == 0
    assert gue_out_two.gnb_info.mcs is None
    assert gue_out_two.throughput == 0.0

    # hung


def test_calc_weight(phase3):
    pass
    # old_frame
    # phase3.calc_weight()
    # new_frame
    # assert old_frame == new_frame

    # test calc_num_bu


def test_allocated_ue_to_space():
    pass
    # UE overlapped with itself
    # running out of space
    # the mcs of new RB is lower than the mcs the UE is currently using
    # the ue moving to the space lower down a original UEs' MCS
    # the space is suitable for this ue     # return True


def test_matching():
    pass
    # one UE


def test_throughput_ue(phase3, gue):
    assert phase3.throughput_ue([]) == 0.0
