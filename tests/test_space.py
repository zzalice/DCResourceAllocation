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
def space_0_0_15_15(layer_g_0):
    from src.resource_allocation.algo.space import Space
    return Space(layer_g_0, 0, 0, 15, 15)


@pytest.fixture()
def space_0_0_3_14(layer_g_0):
    from src.resource_allocation.algo.space import Space
    return Space(layer_g_0, 0, 0, 3, 14)


def test_next_rb(space_0_0_15_15):
    from src.resource_allocation.ds.util_enum import Numerology
    assert space_0_0_15_15.next_rb(0, 0, Numerology.N2) == (0, 4)
    assert space_0_0_15_15.next_rb(0, 12, Numerology.N2) == (4, 0)
    assert space_0_0_15_15.next_rb(12, 12, Numerology.N2) is None


def test_possible_numerology(space_0_0_3_14):
    from src.resource_allocation.ds.util_enum import Numerology
    assert space_0_0_3_14.numerology == [Numerology.N1, Numerology.N2]
    assert space_0_0_3_14.num_of_rb(Numerology.N1) == 2
    assert space_0_0_3_14.num_of_rb(Numerology.N2) == 3
