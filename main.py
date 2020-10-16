from src.resource_allocation.ds.enum import E_MCS, G_MCS, Numerology
from src.resource_allocation.ds.eutran import EUserEquipment
from src.resource_allocation.ds.frame import Frame
from src.resource_allocation.ds.ngran import DUserEquipment, GUserEquipment
from src.resource_allocation.ds.zone import Zone

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
