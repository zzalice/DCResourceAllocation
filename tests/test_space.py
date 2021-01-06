import pytest

from src.resource_allocation.algo.space import Space
from src.resource_allocation.ds.eutran import ENodeB
from src.resource_allocation.ds.ngran import GNodeB
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
