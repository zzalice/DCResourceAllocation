import pytest

from src.resource_allocation.ds.eutran import ENodeB
from src.resource_allocation.ds.ngran import GNodeB, GUserEquipment
from src.resource_allocation.ds.space import empty_space, next_rb_in_space, Space
from src.resource_allocation.ds.util_enum import LTEResourceBlock, Numerology
from src.resource_allocation.ds.util_type import Coordinate


@pytest.fixture
def enb():
    return ENodeB(coordinate=Coordinate(0.0, 0.0), radius=0.5)


@pytest.fixture()
def gnb():
    return GNodeB(coordinate=Coordinate(0.4, 0.0), radius=0.1)


@pytest.fixture()
def layer_g_0(gnb):
    return gnb.frame.layer[0]


@pytest.fixture()
def layer_e(enb):
    return enb.frame.layer[0]


@pytest.fixture()
def space_g_0_0_15_15(layer_g_0):
    return Space(layer_g_0, 0, 0, 15, 15)


@pytest.fixture()
def space_g_0_0_3_14(layer_g_0):
    return Space(layer_g_0, 0, 0, 3, 14)


@pytest.fixture()
def space_e_0_0_2_15(layer_e):
    return Space(layer_e, 0, 0, 2, 15)


def test_next_rb(space_g_0_0_15_15, space_e_0_0_2_15):
    assert space_g_0_0_15_15.next_rb(0, 0, Numerology.N2) == (0, 4)
    assert space_g_0_0_15_15.next_rb(0, 12, Numerology.N2) == (4, 0)
    assert space_g_0_0_15_15.next_rb(12, 12, Numerology.N2) is None

    assert space_e_0_0_2_15.next_rb(0, 0, LTEResourceBlock.E) == (0, 8)
    assert space_e_0_0_2_15.next_rb(0, 8, LTEResourceBlock.E) == (1, 0)
    assert space_e_0_0_2_15.next_rb(2, 8, LTEResourceBlock.E) is None

    assert space_g_0_0_15_15.next_rb(14, 14, Numerology.N2) is None
    assert space_g_0_0_15_15.next_rb(15, 15, Numerology.N2) is None


def test_possible_numerology(space_g_0_0_3_14, space_e_0_0_2_15):
    assert space_g_0_0_3_14.rb_type == [Numerology.N1, Numerology.N2]
    assert space_g_0_0_3_14.num_of_rb(Numerology.N1) == 2
    assert space_g_0_0_3_14.num_of_rb(Numerology.N2) == 3

    assert space_e_0_0_2_15.rb_type == [LTEResourceBlock.E]
    assert space_e_0_0_2_15.num_of_rb(LTEResourceBlock.E) == 6


def test_empty_space(enb, gnb, layer_e, layer_g_0):
    def coordinate(layer):
        spaces = empty_space(layer)
        coordinates = []
        for space in spaces:
            coordinates.append([space.starting_i, space.starting_j, space.ending_i, space.ending_j])
        return coordinates

    ''' [test] Empty eNB frame '''
    spaces_coordinate = coordinate(layer_e)
    assert spaces_coordinate == [[0, 0, enb.frame.frame_freq - 1, enb.frame.frame_time - 1]]

    ''' [test] Empty gNB frame '''
    spaces_coordinate = coordinate(layer_g_0)
    assert spaces_coordinate == [[0, 0, gnb.frame.frame_freq - 1, gnb.frame.frame_time - 1]]

    ''' [test] Fragmented layer '''
    # 0  ------****------
    # 1  ------****------
    # 2  ------****------
    # 3  ------****------
    # 4  ----------------
    # 5  ------****------
    # 6  ------****------
    # 7  ------****------
    # 8  ------****------
    # 9  ----------------
    # .  ................
    # 13 ----------------
    # 14 --****------****
    # 15 --****------****
    # 16 --****------****
    # 17 --****------****
    # 18 ----------------
    # 19 ----------------
    # 20 -********-------
    # 21 -********-------
    # 22 -********-------
    # 23 -********---****
    # 24 ------------****
    # 25 -------****-****
    # 26 ---********-****
    # 27 ---********-----
    # 28 ---********-----
    # 29 ---****---------
    # 30 ----------------
    # .  ................
    ue = GUserEquipment(352, [Numerology.N2], Coordinate(0.5, 0.0))
    ue.set_numerology(Numerology.N2)
    layer_g_0.allocate_resource_block(0, 6, ue)  # start(0, 6) end(3, 9)
    layer_g_0.allocate_resource_block(5, 6, ue)  # start(5, 6) end(8, 9)
    layer_g_0.allocate_resource_block(14, 2, ue)  # start(14, 2) end(17, 5)
    layer_g_0.allocate_resource_block(14, 12, ue)  # start(14, 12) end(17, 15)
    layer_g_0.allocate_resource_block(20, 1, ue)  # start(20, 1) end(23, 4)
    layer_g_0.allocate_resource_block(20, 5, ue)  # start(20, 5) end(23, 8)
    layer_g_0.allocate_resource_block(23, 12, ue)  # start(23, 12) end(26, 15)
    layer_g_0.allocate_resource_block(26, 3, ue)  # start(26, 3) end(29, 6)
    layer_g_0.allocate_resource_block(25, 7, ue)  # start(25, 7) end(28, 10)
    spaces_coordinate = coordinate(layer_g_0)
    frame_time = gnb.frame.frame_time - 1
    assert spaces_coordinate == [[0, 0, 3, 5], [0, 10, 3, frame_time],
                                 [4, 0, 4, frame_time],
                                 [5, 0, 8, 5], [5, 10, 8, frame_time],
                                 [9, 0, 13, frame_time],
                                 [14, 6, 17, 11],
                                 [18, 0, 19, frame_time],
                                 [30, 0, gnb.frame.frame_freq - 1, frame_time]]
    # These spaces are too small for any RB
    #                            [14, 0, 17, 1],
    #                            [20, 0, 23, 0], [20, 9, 22, frame_time],
    #                            [23, 9, 23, 11],
    #                            [24, 0, 24, 11],
    #                            [25, 0, 25, 6], [25, 11, 26, 11],
    #                            [26, 0, 29, 2],
    #                            [27, 11, 28, frame_time],
    #                            [29, 7, 29, frame_time],


def test_next_rb_in_space(enb, gnb, layer_g_0):
    assert next_rb_in_space(212, 8, Numerology.N2, layer_g_0, 212, 12, gnb.frame.frame_freq - 1, gnb.frame.frame_time - 1) == (212, 12)
    assert next_rb_in_space(212, 9, Numerology.N2, layer_g_0, 212, 12, gnb.frame.frame_freq - 1, gnb.frame.frame_time - 1) is None
    try:
        next_rb_in_space(212, 9, Numerology.N2, layer_g_0, 212, 12, gnb.frame.frame_freq, gnb.frame.frame_time)
    except AssertionError:
        pass

