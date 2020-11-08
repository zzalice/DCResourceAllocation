from src.resource_allocation.ds.util_enum import Numerology
from src.resource_allocation.ds.frame import Frame
from src.resource_allocation.ds.ngran import GUserEquipment
from src.resource_allocation.ds.eutran import ENodeB
from src.resource_allocation.ds.ngran import GNodeB

e_frame = Frame(time=16, freq=32, max_layer=1, nodeb=ENodeB())
g_frame = Frame(time=32, freq=48, max_layer=3, nodeb=GNodeB())
g_ue_list = [GUserEquipment(request_data_rate=123, candidate_set=Numerology.gen_candidate_set()) for _ in range(5)]
for i, gue in enumerate(g_ue_list):
    gue.set_numerology(Numerology[f'N{i}'])

for i, gue in enumerate(g_ue_list):
    g_frame.layer[0].allocate_resource_block(i * 8, i, gue)
