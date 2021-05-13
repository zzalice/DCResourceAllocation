from typing import Optional, Tuple

from src.resource_allocation.algo.algo_intuitive import Intuitive
from src.resource_allocation.ds.eutran import ENodeB
from src.resource_allocation.ds.frame import Layer
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.resource_allocation.ds.space import Space
from src.resource_allocation.ds.util_enum import Numerology
from src.resource_allocation.ds.util_type import CircularRegion, Coordinate


def intuitive_enb():
    enb = ENodeB(region=CircularRegion(0.0, 0.0, 0.5), frame_freq=50, frame_time=8)
    return Intuitive(enb, (), (), None)


def intuitive_gnb_2l():
    gnb = GNodeB(region=CircularRegion(0.5, 0.0, 0.5), frame_freq=50, frame_time=8, frame_max_layer=2)
    return Intuitive(gnb, (), (), None)


def intuitive_gnb_3l():
    gnb = GNodeB(region=CircularRegion(0.5, 0.0, 0.5), frame_freq=50, frame_time=8, frame_max_layer=3)
    return Intuitive(gnb, (), (), None)


def gue():
    return GUserEquipment(11, (Numerology.N0, Numerology.N1, Numerology.N2, Numerology.N3), Coordinate(0.5, 0.0))


def due():
    u = DUserEquipment(11, (Numerology.N1,), Coordinate(0.45, 0.0))
    u.set_numerology(Numerology.N1)
    return u


def test_update_space():
    update_space_empty()
    update_space_complete_row()
    update_space_enb()
    update_space_first_row()
    update_space_first_row_jagged()


def update_space_empty():
    # 0  --------
    # 1  --------
    #      ...
    # 49 --------
    intuitive: Intuitive = intuitive_gnb_2l()
    spaces: Optional[Tuple[Space, ...]] = intuitive.update_empty_space()
    assert len(spaces) == 2
    assert spaces[0].starting_i == 0
    assert spaces[0].starting_j == 0
    assert spaces[0].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[0].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[1].starting_i == 0
    assert spaces[1].starting_j == 0
    assert spaces[1].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[1].ending_j == intuitive.nb.frame.frame_time - 1


def update_space_complete_row():
    # 0  ********
    # 1  --------
    #      ...
    # 49 --------
    intuitive: Intuitive = intuitive_gnb_2l()
    l0: Layer = intuitive.nb.frame.layer[0]
    ue: GUserEquipment = gue()

    ue.set_numerology(Numerology.N0)
    l0.allocate_resource_block(0, 0, ue)

    spaces: Optional[Tuple[Space, ...]] = intuitive.update_empty_space()
    assert len(spaces) == 2
    assert spaces[0].starting_i == 1
    assert spaces[0].starting_j == 0
    assert spaces[0].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[0].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[1].starting_i == 0
    assert spaces[1].starting_j == 0
    assert spaces[1].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[1].ending_j == intuitive.nb.frame.frame_time - 1


def update_space_enb():
    # # (eNB)
    # 0  ********
    # 1  ****----
    # 2  --------
    #      ...
    # 49 --------
    intuitive: Intuitive = intuitive_enb()
    l0: Layer = intuitive.nb.frame.layer[0]
    ue: DUserEquipment = due()

    l0.allocate_resource_block(0, 0, ue)
    l0.allocate_resource_block(0, 4, ue)
    l0.allocate_resource_block(1, 0, ue)

    spaces: Optional[Tuple[Space, ...]] = intuitive.update_empty_space()
    assert len(spaces) == 2
    assert spaces[0].starting_i == 1
    assert spaces[0].starting_j == 4
    assert spaces[0].ending_i == 1
    assert spaces[0].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[1].starting_i == 2
    assert spaces[1].starting_j == 0
    assert spaces[1].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[1].ending_j == intuitive.nb.frame.frame_time - 1


def update_space_first_row():
    # 0  ****----
    # 1  ****----
    # 2  --------
    #      ...
    # 49 --------
    intuitive: Intuitive = intuitive_gnb_2l()
    l0: Layer = intuitive.nb.frame.layer[0]
    ue: GUserEquipment = gue()

    ue.set_numerology(Numerology.N1)
    l0.allocate_resource_block(0, 0, ue)

    spaces: Optional[Tuple[Space, ...]] = intuitive.update_empty_space()
    assert len(spaces) == 3
    assert spaces[0].starting_i == 0
    assert spaces[0].starting_j == 4
    assert spaces[0].ending_i == 1
    assert spaces[0].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[1].starting_i == 2
    assert spaces[1].starting_j == 0
    assert spaces[1].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[1].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[2].starting_i == 0
    assert spaces[2].starting_j == 0
    assert spaces[2].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[2].ending_j == intuitive.nb.frame.frame_time - 1


def update_space_first_row_jagged():
    # 0  *****---
    # 1  *****---
    # 2  *****---
    # 3  *****---
    # 4  --*-----
    # 5  --*-----
    # 6  --*-----
    # 7  --*-----
    # 8  --------
    #      ...
    # 49 --------
    intuitive: Intuitive = intuitive_gnb_2l()
    l0: Layer = intuitive.nb.frame.layer[0]
    ue: GUserEquipment = gue()

    ue.set_numerology(Numerology.N2)
    l0.allocate_resource_block(0, 0, ue)
    l0.allocate_resource_block(0, 3, ue)
    ue.set_numerology(Numerology.N3)
    l0.allocate_resource_block(0, 2, ue)

    spaces: Optional[Tuple[Space, ...]] = intuitive.update_empty_space()
    assert len(spaces) == 3
    assert spaces[0].starting_i == 0
    assert spaces[0].starting_j == 5
    assert spaces[0].ending_i == 7
    assert spaces[0].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[1].starting_i == 8
    assert spaces[1].starting_j == 0
    assert spaces[1].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[1].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[2].starting_i == 0
    assert spaces[2].starting_j == 0
    assert spaces[2].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[2].ending_j == intuitive.nb.frame.frame_time - 1


def update_space_():
    pass
    # 0  ********
    # 1  ******--
    # 2  ******--
    # 3  ----**--
    # 4  ----**--
    # 5  --------
    #      ...
    # 49 --------

    # 0  ********
    # 1  *****---
    # 2  *****---
    # 3  *****---
    # 4  *****---
    # 5  --*-----
    # 6  --*-----
    # 7  --*-----
    # 8  --*-----
    # 9  --------
    #      ...
    # 49 --------

    # 0  ********
    # 1  ******--
    # 2  ******--
    # 3  ******--
    # 4  ******--
    # 5  --*--*--
    # 6  --*--*--
    # 7  --*--*--
    # 8  --*--*--
    # 9  --------
    #      ...
    # 49 --------

    # 0  ********
    # 1  ******--
    # 2  ******--
    # 3  ******--
    # 4  ******--
    # 5  --**----
    # 6  --**----
    # 7  --**----
    # 8  --**----
    # 9  ******--
    # 10 ******--
    # 11 ----**--
    # 12 ----**--
    # 13 --------
    #      ...
    # 49 --------

    # 0  ********
    # 1  ******--
    # 2  ******--
    # 3  ******--
    # 4  ******--
    # 5  --*--*--
    # 6  --*--*--
    # 7  --*--*--
    # 8  --*--*--
    # 9  ******--
    # 10 ******--
    # 11 ----**--
    # 12 ----**--
    # 13 --------
    #      ...
    # 49 --------

    # 0  ********
    # 1  ********
    # 2  ********
    # 3  ********
    # 4  ********
    # 5  --*--*--
    # 6  --*--*--
    # 7  --*--*--
    # 8  --*--*--
    # 9  ******--
    # 10 ******--
    # 11 ******--
    # 12 ******--
    # 13 *--*----
    # 14 *--*----
    # 15 *--*----
    # 16 *--*----
    # 17 --------
    #      ...
    # 49 --------

    # 0  ********
    #      ...
    # 45 ********
    # 46 ******--
    # 47 ******--
    # 48 ----**--
    # 49 ----**--

    # 0  ********
    #      ...
    # 44 ********
    # 45 ******--
    # 46 ******--
    # 47 ----**--
    # 48 ----**--
    # 49 --------

    # 0  ********
    #      ...
    # 45 ********
    # 46 ******--
    # 47 ******--
    # 48 **------
    # 49 **------

    # 0  ********
    #      ...
    # 44 ********
    # 45 ******--
    # 46 ******--
    # 47 **------
    # 48 **------
    # 49 --------

    # 0  ********     layer 1 empty     | no next layer
    #      ...          --------        |
    # 41 ********                       |
    # 42 *****---                       |
    # 43 *****---                       |
    # 44 *****---         ...           |
    # 45 *****---                       |
    # 46 --*-----                       |
    # 47 --*-----                       |
    # 48 --*-----                       |
    # 49 --*-----       --------        |

    # layer 0         layer 1 empty     | no next layer
    # 0  ********       --------        |
    #      ...                          |
    # 40 ********                       |
    # 41 *****---                       |
    # 42 *****---                       |
    # 43 *****---                       |
    # 44 *****---         ...           |
    # 45 --*-----                       |
    # 46 --*-----                       |
    # 47 --*-----                       |
    # 48 --*-----                       |
    # 49 --------       --------        |

    # layer 0         layer 1 empty     |     no next layer
    # 0  ********       --------        |
    #      ...                          |
    # 41 ********                       |
    # 42 ********                       |
    # 43 ********                       |
    # 44 ********                       |
    # 45 ********         ...           |
    # 46 --*--*--                       |
    # 47 --*--*--                       |
    # 48 --*--*--                       |
    # 49 --*--*--       --------        |
