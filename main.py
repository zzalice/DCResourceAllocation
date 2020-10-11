from resource_allocation.zone import Zone
from resource_allocation.frame import Frame
from resource_allocation.eutran import EUserEquipment
from resource_allocation.ngran import GUserEquipment, DUserEquipment
from resource_allocation.util_enum import Numerology, MCS_E, MCS_G

if __name__ == '__main__':
    print('DC Resource Allocation')

    gue = GUserEquipment(12345, (Numerology.gen_candidate_set()))
    gue.set_numerology(Numerology.N0)

    eue = EUserEquipment(56789, (Numerology.N0,))
    eue.set_numerology(Numerology.N0)

    due = DUserEquipment(123, Numerology.gen_candidate_set(exclude=(Numerology.N1, Numerology.N3)))
    due.set_numerology(Numerology.N0)

    abc = Zone((gue, eue, due), 123, 80, 80)

    gue.assign_mcs(MCS_G.QPSK_2)
    eue.assign_mcs(MCS_E.WORST)
    due.assign_mcs(MCS_G.QPSK_2)
    due.assign_mcs(MCS_E.WORST)

    aaa = Numerology.N0.height

    gframe = Frame()
    gframe.layer[0].allocate_resource_block(1, 3, gue)

    print(gue.gnb_info.mcs.calc_required_rb_count(123456))

