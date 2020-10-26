from src.resource_allocation.ds.eutran import EUserEquipment
from src.resource_allocation.ds.frame import Frame
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.resource_allocation.ds.util_enum import E_MCS, G_MCS, Numerology
from src.resource_allocation.ds.zone import Zone

if __name__ == '__main__':
    print('DC Resource Allocation')

    g_nb = GNodeB()
    g_ue = GUserEquipment(12345, (Numerology.gen_candidate_set()))
    g_ue.set_numerology(Numerology.N0)
    e_ue = EUserEquipment(56789, (Numerology.N0,))
    e_ue.set_numerology(Numerology.N0)
    d_ue = DUserEquipment(123, Numerology.gen_candidate_set(exclude=(Numerology.N1, Numerology.N3)))
    d_ue.set_numerology(Numerology.N0)

    tmp_zone = Zone((g_ue, d_ue), g_nb)

    g_ue.assign_mcs(G_MCS.QPSK_2)
    e_ue.assign_mcs(E_MCS.WORST)
    d_ue.assign_mcs(G_MCS.QPSK_2)
    d_ue.assign_mcs(E_MCS.WORST)

    n0_freq = Numerology.N0.freq

    g_frame = Frame(80, 32, 3)
    g_frame.layer[0].allocate_resource_block(1, 3, g_ue)

    print(g_ue.gnb_info.num_of_rb)
