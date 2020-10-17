from src.resource_allocation.ds.enum import Numerology, E_MCS, G_MCS


class TestNumerology:
    numerology_count = 4  # from N1~N4

    def test_mu_and_size(self):
        for i in range(self.numerology_count + 1):
            numerology: Numerology = Numerology[f'N{i}']
            assert numerology.mu == i
            assert numerology.height == 2 ** i
            assert numerology.width == 2 ** (self.numerology_count - i)

    def test_gen_candidate_set(self):
        expected_candidate_set = [Numerology[f'N{i}'] for i in range(self.numerology_count + 1)]
        assert all([x in Numerology.gen_candidate_set() for x in expected_candidate_set])


class TestMCS:
    def test_calc_required_rb_count(self):
        assert E_MCS.WORST.calc_required_rb_count(100) == 1000  # ceil(100/0.1)
        assert G_MCS.QPSK_1.calc_required_rb_count(100) == 6  # ceil(100/19.90)

    def test_worst_mcs(self):
        assert E_MCS(None) == E_MCS.WORST  # TODO: remember to update
        assert G_MCS(None) == G_MCS.QPSK_1
