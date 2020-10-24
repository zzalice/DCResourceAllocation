from typing import List

from src.resource_allocation.ds.eutran import ENodeB
from src.resource_allocation.ds.ngran import GNodeB
from src.resource_allocation.ds.util_enum import Numerology
from src.resource_allocation.ds.util_type import Numerologies

if __name__ == '__main__':
    g_ue_count: int = 10
    d_ue_count: int = 10
    e_ue_count: int = 10

    # g_data_rate: List[int] = [random.randrange(1_200, 3_000_000 + 1, 1_200) for i in range(g_ue_count)]
    # g_numerology: List[Numerologies] = [Numerology.gen_candidate_set(random_select=True) for i in range(g_ue_count)]
    # RE: replace `: \([0-9]+, [0-9]+\)>`
    g_data_rate: List[int] = [2959200, 1178400, 2845200, 115200, 2173200, 982800, 1273200, 87600, 2581200, 40800]
    g_numerology: List[Numerologies] = [
        (Numerology.N0, Numerology.N2), (Numerology.N0, Numerology.N1), (Numerology.N0, Numerology.N1, Numerology.N2),
        (Numerology.N0, Numerology.N2, Numerology.N3, Numerology.N4),
        (Numerology.N1, Numerology.N2, Numerology.N3, Numerology.N4),
        (Numerology.N0, Numerology.N1, Numerology.N2, Numerology.N3, Numerology.N4),
        (Numerology.N0, Numerology.N1, Numerology.N2, Numerology.N3, Numerology.N4),
        (Numerology.N3,), (Numerology.N1,), (Numerology.N0, Numerology.N2, Numerology.N3)
    ]

    d_data_rate: List[int] = [2535600, 308400, 462000, 1376400, 2979600, 642000, 1581600, 2162400, 2506800, 1676400]
    d_numerology: List[Numerologies] = [
        (Numerology.N0, Numerology.N1, Numerology.N2, Numerology.N3, Numerology.N4), (Numerology.N3,),
        (Numerology.N0, Numerology.N1, Numerology.N2, Numerology.N3, Numerology.N4),
        (Numerology.N0, Numerology.N2, Numerology.N3), (Numerology.N0, Numerology.N1, Numerology.N2, Numerology.N4),
        (Numerology.N0, Numerology.N2, Numerology.N3), (Numerology.N2, Numerology.N3, Numerology.N4),
        (Numerology.N1, Numerology.N2), (Numerology.N3,), (Numerology.N1, Numerology.N2, Numerology.N3)
    ]

    g_nb = GNodeB()
    e_nb = ENodeB()
