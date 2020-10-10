from frame import Frame
from ngran import GUserEquipment
from util_enum import Numerology

e_frame = Frame(time=16, freq=32)

g_frame = Frame(time=32, freq=48, max_layer=3)
gues = [GUserEquipment() for i in range(5)]
for i, gue in enumerate(gues):
    gue.set_numerology(Numerology[f'N{i}'])

for i, gue in enumerate(gues):
    g_frame.layer[0].allocate_resource_block(i * 8, i, gue)
