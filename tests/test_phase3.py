import pytest


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
    layer_g_0.allocate_zone(zone)
    assert len(gue.gnb_info.rb) == 38
    return gue


@pytest.fixture()
def due(gnb, enb, layer_g_0, layer_e):
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
def channel_model(gnb, enb):
    from src.channel_model.sinr import ChannelModel
    return ChannelModel({"g_freq": gnb.frame.frame_freq,
                         "e_freq": enb.frame.frame_freq,
                         "co_bandwidth": 25})


@pytest.fixture()
def phase3(channel_model, gnb, enb, gue):
    from src.resource_allocation.algo.phase3 import Phase3
    return Phase3(channel_model, gnb, enb, ((gue,), (), ()), ((), (), ()))


def test_adjust_mcs(phase3, gue, due, gnb, enb):
    from src.resource_allocation.ds.util_enum import SINRtoMCS
    from src.resource_allocation.ds.util_enum import G_MCS
    from src.resource_allocation.ds.util_enum import E_MCS

    # gue
    phase3.channel_model.sinr_ue(gue)
    phase3.adjust_mcs(gue)
    old_rb = gue.gnb_info.rb[0]
    for rb in gue.gnb_info.rb[1:]:
        assert old_rb.sinr >= rb.sinr
        old_rb = rb
    assert SINRtoMCS.sinr_to_mcs(gue.gnb_info.rb[-1].sinr, gue.gnb_info.nb_type) == gue.gnb_info.mcs
    assert len(gue.gnb_info.rb) * gue.gnb_info.mcs.value == gue.throughput
    assert gue.throughput >= gue.request_data_rate
    assert gue.throughput <= gue.request_data_rate + gue.gnb_info.mcs.value

    # due
    phase3.adjust_mcs(due)
    old_rb = due.gnb_info.rb[0]
    for rb in due.gnb_info.rb[1:]:
        assert old_rb.sinr >= rb.sinr
        old_rb = rb
    assert SINRtoMCS.sinr_to_mcs(due.gnb_info.rb[-1].sinr, gnb.nb_type) == due.gnb_info.mcs
    assert len(due.gnb_info.rb) * due.gnb_info.mcs.value + len(due.enb_info.rb) * due.enb_info.mcs.value == due.throughput
    assert due.throughput >= due.request_data_rate
    assert due.throughput <= due.request_data_rate + due.gnb_info.mcs.value
    assert due.throughput <= due.request_data_rate + due.enb_info.mcs.value
    assert len(due.gnb_info.rb) == 3
    assert len(due.enb_info.rb) == 2
    assert due.gnb_info.mcs == G_MCS.CQI6_QPSK
    assert due.enb_info.mcs == E_MCS.CQI5_QPSK


def test_throughput_ue(phase3, gue):
    assert phase3.throughput_ue([]) == 0.0
