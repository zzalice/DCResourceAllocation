from resource_allocation.enum import E_MCS, G_MCS, Numerology
from resource_allocation.eutran import EUserEquipment
from resource_allocation.frame import Frame
from resource_allocation.ngran import DUserEquipment, GUserEquipment
from resource_allocation.zone import Zone

if __name__ == '__main__':
    print('DC Resource Allocation')

    gue = GUserEquipment(12345, (Numerology.gen_candidate_set()))
    gue.set_numerology(Numerology.N0)

    eue = EUserEquipment(56789, (Numerology.N0,))
    eue.set_numerology(Numerology.N0)

    due = DUserEquipment(123, Numerology.gen_candidate_set(exclude=(Numerology.N1, Numerology.N3)))
    due.set_numerology(Numerology.N0)

    abc = Zone((gue, eue, due), 123, 80, 80)

    gue.assign_mcs(G_MCS.QPSK_2)
    eue.assign_mcs(E_MCS.WORST)
    due.assign_mcs(G_MCS.QPSK_2)
    due.assign_mcs(E_MCS.WORST)

    aaa = Numerology.N0.height

    gframe = Frame()
    gframe.layer[0].allocate_resource_block(1, 3, gue)

    print(gue.gnb_info.mcs.calc_required_rb_count(123456))
