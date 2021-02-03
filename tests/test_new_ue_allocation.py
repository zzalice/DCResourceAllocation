import pytest

from src.channel_model.sinr import ChannelModel
from src.resource_allocation.algo.new_ue_allocation import AllocateUE
from src.resource_allocation.ds.eutran import ENodeB
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.resource_allocation.ds.space import Space
from src.resource_allocation.ds.util_enum import LTEResourceBlock, Numerology
from src.resource_allocation.ds.util_type import Coordinate


@pytest.fixture
def enb():
    return ENodeB(coordinate=Coordinate(0.0, 0.0), radius=0.5)


@pytest.fixture
def gnb():
    return GNodeB(coordinate=Coordinate(0.4, 0.0), radius=0.1)


@pytest.fixture
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


@pytest.fixture
def space_g0_0_0_3_15(gnb):
    return Space(gnb.frame.layer[0], 0, 0, 3, 15)


@pytest.fixture
def space_g0_4_0_5_15(gnb):
    return Space(gnb.frame.layer[0], 4, 0, 5, 15)


@pytest.fixture
def space_g0_6_0_7_15(gnb):
    return Space(gnb.frame.layer[0], 6, 0, 7, 15)


@pytest.fixture
def space_g0_8_0_11_15(gnb):
    return Space(gnb.frame.layer[0], 8, 0, 11, 15)


@pytest.fixture
def space_e_0_0_1_15(enb):
    return Space(enb.frame.layer[0], 0, 0, 1, 15)


@pytest.fixture
def space_e_2_0_2_15(enb):
    return Space(enb.frame.layer[0], 2, 0, 2, 15)


@pytest.fixture
def space_e_3_0_4_15(enb):
    return Space(enb.frame.layer[0], 3, 0, 4, 15)


@pytest.fixture
def space_e_5_0_5_15(enb):
    return Space(enb.frame.layer[0], 5, 0, 5, 15)


@pytest.fixture
def gue(gnb, enb):
    gue = GUserEquipment(2407, [Numerology.N1], Coordinate(0.45, 0.0))  # 3個G_MCS CQI 15
    gue.register_nb(enb, gnb)
    gue.set_numerology(gue.candidate_set[-1])
    return gue


@pytest.fixture
def due(enb, gnb):
    due = DUserEquipment(4012, [Numerology.N1], Coordinate(0.5, 0.0))  # 5個G_MCS CQI 15
    due.register_nb(enb, gnb)
    due.set_numerology(due.candidate_set[-1])
    return due


@pytest.fixture
def due_2(enb, gnb):
    due = DUserEquipment(4012, [Numerology.N1], Coordinate(0.5, 0.0))  # 5個G_MCS CQI 15
    due.register_nb(enb, gnb)
    due.set_numerology(due.candidate_set[-1])
    return due


@pytest.fixture
def due_3(enb, gnb):
    due = DUserEquipment(4012, [Numerology.N1], Coordinate(0.5, 0.0))  # 5個G_MCS CQI 15
    due.register_nb(enb, gnb)
    due.set_numerology(due.candidate_set[-1])
    return due


@pytest.fixture
def due_enb(enb, gnb):
    due = DUserEquipment(1399, [Numerology.N1], Coordinate(0.5, 0.0))  # 3個E_MCS CQI 15
    due.register_nb(enb, gnb)
    due.set_numerology(due.candidate_set[-1])
    return due


@pytest.fixture
def due_enb_2(enb, gnb):
    due = DUserEquipment(1399, [Numerology.N1], Coordinate(0.5, 0.0))  # 3個E_MCS CQI 15
    due.register_nb(enb, gnb)
    due.set_numerology(due.candidate_set[-1])
    return due


@pytest.fixture
def eue(enb, gnb):
    eue = DUserEquipment(1399, [LTEResourceBlock.E], Coordinate(0.5, 0.0))  # 3個E_MCS CQI 15
    eue.register_nb(enb, gnb)
    eue.set_numerology(eue.candidate_set[-1])
    return eue


@pytest.fixture
def eue_2(enb, gnb):
    eue = DUserEquipment(1399, [LTEResourceBlock.E], Coordinate(0.5, 0.0))  # 3個E_MCS CQI 15
    eue.register_nb(enb, gnb)
    eue.set_numerology(eue.candidate_set[-1])
    return eue


def test_new_ue(channel_model, space_g0_0_0_3_15, space_g0_4_0_5_15, space_g0_6_0_7_15, space_g0_8_0_11_15,
                space_e_0_0_1_15, space_e_2_0_2_15,
                gue, due, due_2, due_3, eue, eue_2):
    """"""
    # 理論上所有UE CQI都會是15
    """ [test] 一個空間就滿足QoS """
    assert AllocateUE(gue, (space_g0_0_0_3_15,), channel_model).allocate() is True
    assert AllocateUE(eue, (space_e_0_0_1_15,), channel_model).allocate() is True

    """ [test] 一個空間無法滿足QoS """
    assert AllocateUE(due, (space_g0_4_0_5_15,), channel_model).allocate() is False
    assert AllocateUE(eue_2, (space_e_2_0_2_15,), channel_model).allocate() is False

    """ [test] 多個空間可以滿足QoS """
    # assert AllocateUE(due, (space_g0_0_0_3_15, space_g0_4_0_5_15), channel_model).allocate() is True
    assert AllocateUE(due_2, (space_g0_6_0_7_15, space_g0_8_0_11_15), channel_model).allocate() is True


def test_small_step_undo():
    """"""
    """ [test] 跟自己重疊時會刪掉剛新增的RB，並繼續嘗試下一個RB/空間 """
    """ [test] 遇到CQI=0的RB時，刪除這個RB，並繼續嘗試下一個RB/空間 """
    # 要先解掉那個TODO


def test_new_ue_numerology_restore(channel_model, space_e_3_0_4_15, space_e_5_0_5_15, due_enb, due_enb_2):
    """"""
    """ [test] 一個空間就滿足QoS """
    assert AllocateUE(due_enb, (space_e_3_0_4_15,), channel_model).allocate() is True

    """ [test] 一個空間無法滿足QoS """
    assert AllocateUE(due_enb_2, (space_e_5_0_5_15,), channel_model).allocate() is False
