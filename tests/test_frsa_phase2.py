import pytest

from src.resource_allocation.algo.frsa.frsa_phase2 import FRSAPhase2
from src.resource_allocation.ds.eutran import ENodeB
from src.resource_allocation.ds.ngran import GNodeB, GUserEquipment
from src.resource_allocation.ds.util_enum import Numerology
from src.resource_allocation.ds.util_type import Coordinate
from src.resource_allocation.ds.zone import Zone


@pytest.fixture(scope="module")
def gnb():
    return GNodeB(coordinate=Coordinate(0.4, 0.0), radius=0.1, frame_freq=50)


@pytest.fixture(scope="module")
def enb():
    return ENodeB(coordinate=Coordinate(0.0, 0.0), radius=0.5)


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
def z1(gnb, gue):
    z = Zone([gue], gnb)
    z._numerology = Numerology.N3
    z.zone_freq = 8
    return z


@pytest.fixture(scope="module")
def z2(gnb, gue):
    z = Zone([gue], gnb)
    z._numerology = Numerology.N2
    z.zone_freq = 20
    return z


@pytest.fixture(scope="module")
def z3(gnb, gue):
    z = Zone([gue], gnb)
    z._numerology = Numerology.N3
    z.zone_freq = 8
    return z


@pytest.fixture(scope="module")
def z4(gnb, gue):
    z = Zone([gue], gnb)
    z._numerology = Numerology.N0
    z.zone_freq = 21
    return z


@pytest.fixture(scope="module")
def z5(gnb, gue):
    z = Zone([gue], gnb)
    z._numerology = Numerology.N3
    z.zone_freq = 0
    return z


@pytest.fixture(scope="module")
def z6(gnb, gue):
    z = Zone([gue], gnb)
    z._numerology = Numerology.N3
    z.zone_freq = 16
    return z


@pytest.fixture(scope="module")
def z7(gnb, gue):
    z = Zone([gue], gnb)
    z._numerology = Numerology.N0
    z.zone_freq = 2
    return z


@pytest.fixture(scope="module")
def z8(gnb, gue):
    z = Zone([gue], gnb)
    z._numerology = Numerology.N3
    z.zone_freq = 16
    return z


@pytest.fixture(scope="module")
def z9(gnb, gue):
    z = Zone([gue], gnb)
    z._numerology = Numerology.N0
    z.zone_freq = 8
    return z


@pytest.fixture(scope="module")
def z10(gnb, gue):
    z = Zone([gue], gnb)
    z._numerology = Numerology.N0
    z.zone_freq = 10
    return z


@pytest.fixture(scope="module")
def z11(gnb, gue):
    z = Zone([gue], gnb)
    z._numerology = Numerology.N1
    z.zone_freq = 16
    return z


@pytest.fixture(scope="module")
def z12(gnb, gue):
    z = Zone([gue], gnb)
    z._numerology = Numerology.N0
    z.zone_freq = 8
    return z


@pytest.fixture(scope="module")
def frsa_phase2(gnb, z1, z2, z3, z4, z5, z6, z7, z8, z9, z10, z11, z12):
    z_list = [{'layer': 0, 'residual': 2, 'zones': [z2, z10, z8, z7]},
              {'layer': 1, 'residual': 5, 'zones': [z4, z12, z9, z1]},
              {'layer': 2, 'residual': 10, 'zones': [z3, z11, z6]}]
    return FRSAPhase2(gnb, z_list)


def test_calc_total_freq_space(frsa_phase2: FRSAPhase2):
    frsa_phase2.calc_total_freq_span()
    assert frsa_phase2.freq_span == [{Numerology.N0: 12, Numerology.N1: 0, Numerology.N2: 20, Numerology.N3: 16},
                                     {Numerology.N0: 37, Numerology.N1: 0, Numerology.N2: 0, Numerology.N3: 8},
                                     {Numerology.N0: 0, Numerology.N1: 16, Numerology.N2: 0, Numerology.N3: 24}]


def test_calc_dissimilarity(frsa_phase2: FRSAPhase2, gnb):
    assert frsa_phase2.calc_dissimilarity(0, Numerology.N0, frsa_phase2.freq_span) == (abs(12 - 37) + abs(12 - 0)) / 3
    assert frsa_phase2.calc_dissimilarity(0, Numerology.N1, frsa_phase2.freq_span) == (abs(0 - 0) + abs(0 - 16)) / 3
    assert frsa_phase2.calc_dissimilarity(0, Numerology.N2, frsa_phase2.freq_span) == (abs(20 - 0) + abs(20 - 0)) / 3
    assert frsa_phase2.calc_dissimilarity(0, Numerology.N3, frsa_phase2.freq_span) == (abs(16 - 8) + abs(16 - 24)) / 3

    assert frsa_phase2.calc_dissimilarity(1, Numerology.N0, frsa_phase2.freq_span) == (abs(37 - 12) + abs(37 - 0)) / 3
    assert frsa_phase2.calc_dissimilarity(1, Numerology.N1, frsa_phase2.freq_span) == (abs(0 - 0) + abs(0 - 16)) / 3
    assert frsa_phase2.calc_dissimilarity(1, Numerology.N2, frsa_phase2.freq_span) == (abs(0 - 20) + abs(0 - 0)) / 3
    assert frsa_phase2.calc_dissimilarity(1, Numerology.N3, frsa_phase2.freq_span) == (abs(8 - 16) + abs(8 - 24)) / 3
