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
    update_space_middle_jagged()
    update_space_middle_jags()
    update_space_middle_two_jags()
    update_space_middle_two_stack_jag()
    update_space_middle_two_stack_jag2()
    update_space_middle_two_stack_jags()
    update_space_end_jag()
    update_space_end_jag_empty()
    update_space_end_jag2()
    update_space_end_jag2_empty()
    update_space_end_jags()
    update_space_end_jags_empty()
    update_space_end_two_jags()
    update_space_to_second_layer()
    update_space_out_of_space()


def update_space_empty():
    # 0  --------
    # 1  --------
    #      ...
    # 49 --------
    intuitive: Intuitive = intuitive_gnb_2l()
    spaces: Optional[Tuple[Space, ...]] = intuitive.update_empty_space(intuitive.nb, gue())
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

    spaces: Optional[Tuple[Space, ...]] = intuitive.update_empty_space(intuitive.nb, ue)
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

    spaces: Optional[Tuple[Space, ...]] = intuitive.update_empty_space(intuitive.nb, ue)
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

    ue.set_numerology(Numerology.N1)
    spaces: Optional[Tuple[Space, ...]] = intuitive.update_empty_space(intuitive.nb, ue)
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


    ue.set_numerology(Numerology.N2)
    spaces: Optional[Tuple[Space, ...]] = intuitive.update_empty_space(intuitive.nb, ue)
    assert len(spaces) == 3
    assert spaces[0].starting_i == 0
    assert spaces[0].starting_j == 4
    assert spaces[0].ending_i == 3
    assert spaces[0].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[1].starting_i == 4
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

    ue.set_numerology(Numerology.N2)
    spaces: Optional[Tuple[Space, ...]] = intuitive.update_empty_space(intuitive.nb, ue)
    assert len(spaces) == 3
    assert spaces[0].starting_i == 0
    assert spaces[0].starting_j == 5
    assert spaces[0].ending_i == 3
    assert spaces[0].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[1].starting_i == 8
    assert spaces[1].starting_j == 0
    assert spaces[1].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[1].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[2].starting_i == 0
    assert spaces[2].starting_j == 0
    assert spaces[2].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[2].ending_j == intuitive.nb.frame.frame_time - 1

    ue.set_numerology(Numerology.N3)
    spaces: Optional[Tuple[Space, ...]] = intuitive.update_empty_space(intuitive.nb, ue)
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


def update_space_middle_jagged():
    # 0  ********
    # 1  ******--
    # 2  ******--
    # 3  ----**--
    # 4  ----**--
    # 5  --------
    #      ...
    # 49 --------
    intuitive: Intuitive = intuitive_gnb_2l()
    l0: Layer = intuitive.nb.frame.layer[0]
    ue: GUserEquipment = gue()

    ue.set_numerology(Numerology.N0)
    l0.allocate_resource_block(0, 0, ue)
    ue.set_numerology(Numerology.N1)
    l0.allocate_resource_block(1, 0, ue)
    ue.set_numerology(Numerology.N2)
    l0.allocate_resource_block(1, 4, ue)

    ue.set_numerology(Numerology.N2)
    spaces: Optional[Tuple[Space, ...]] = intuitive.update_empty_space(intuitive.nb, ue)
    assert len(spaces) == 3
    assert spaces[0].starting_i == 1
    assert spaces[0].starting_j == 6
    assert spaces[0].ending_i == 4
    assert spaces[0].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[1].starting_i == 5
    assert spaces[1].starting_j == 0
    assert spaces[1].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[1].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[2].starting_i == 0
    assert spaces[2].starting_j == 0
    assert spaces[2].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[2].ending_j == intuitive.nb.frame.frame_time - 1

    ue.set_numerology(Numerology.N3)
    spaces: Optional[Tuple[Space, ...]] = intuitive.update_empty_space(intuitive.nb, ue)
    assert len(spaces) == 3
    assert spaces[0].starting_i == 1
    assert spaces[0].starting_j == 6
    assert spaces[0].ending_i == 8
    assert spaces[0].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[1].starting_i == 9
    assert spaces[1].starting_j == 0
    assert spaces[1].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[1].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[2].starting_i == 0
    assert spaces[2].starting_j == 0
    assert spaces[2].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[2].ending_j == intuitive.nb.frame.frame_time - 1


def update_space_middle_jags():
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
    intuitive: Intuitive = intuitive_gnb_2l()
    l0: Layer = intuitive.nb.frame.layer[0]
    ue: GUserEquipment = gue()

    ue.set_numerology(Numerology.N0)
    l0.allocate_resource_block(0, 0, ue)
    ue.set_numerology(Numerology.N2)
    l0.allocate_resource_block(1, 0, ue)
    l0.allocate_resource_block(1, 3, ue)
    ue.set_numerology(Numerology.N3)
    l0.allocate_resource_block(1, 2, ue)

    ue.set_numerology(Numerology.N2)
    spaces: Optional[Tuple[Space, ...]] = intuitive.update_empty_space(intuitive.nb, ue)
    assert len(spaces) == 3
    assert spaces[0].starting_i == 1
    assert spaces[0].starting_j == 5
    assert spaces[0].ending_i == 4
    assert spaces[0].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[1].starting_i == 9
    assert spaces[1].starting_j == 0
    assert spaces[1].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[1].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[2].starting_i == 0
    assert spaces[2].starting_j == 0
    assert spaces[2].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[2].ending_j == intuitive.nb.frame.frame_time - 1


def update_space_middle_two_jags():
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
    intuitive: Intuitive = intuitive_gnb_2l()
    l0: Layer = intuitive.nb.frame.layer[0]
    ue: GUserEquipment = gue()

    ue.set_numerology(Numerology.N0)
    l0.allocate_resource_block(0, 0, ue)
    ue.set_numerology(Numerology.N2)
    l0.allocate_resource_block(1, 0, ue)
    l0.allocate_resource_block(1, 3, ue)
    ue.set_numerology(Numerology.N3)
    l0.allocate_resource_block(1, 2, ue)
    l0.allocate_resource_block(1, 5, ue)

    ue.set_numerology(Numerology.N2)
    spaces: Optional[Tuple[Space, ...]] = intuitive.update_empty_space(intuitive.nb, ue)
    assert len(spaces) == 3
    assert spaces[0].starting_i == 1
    assert spaces[0].starting_j == 6
    assert spaces[0].ending_i == 4
    assert spaces[0].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[1].starting_i == 9
    assert spaces[1].starting_j == 0
    assert spaces[1].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[1].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[2].starting_i == 0
    assert spaces[2].starting_j == 0
    assert spaces[2].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[2].ending_j == intuitive.nb.frame.frame_time - 1

    ue.set_numerology(Numerology.N3)
    spaces: Optional[Tuple[Space, ...]] = intuitive.update_empty_space(intuitive.nb, ue)
    assert len(spaces) == 3
    assert spaces[0].starting_i == 1
    assert spaces[0].starting_j == 6
    assert spaces[0].ending_i == 8
    assert spaces[0].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[1].starting_i == 9
    assert spaces[1].starting_j == 0
    assert spaces[1].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[1].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[2].starting_i == 0
    assert spaces[2].starting_j == 0
    assert spaces[2].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[2].ending_j == intuitive.nb.frame.frame_time - 1


def update_space_middle_two_stack_jag():
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
    intuitive: Intuitive = intuitive_gnb_2l()
    l0: Layer = intuitive.nb.frame.layer[0]
    ue: GUserEquipment = gue()

    ue.set_numerology(Numerology.N0)
    l0.allocate_resource_block(0, 0, ue)
    ue.set_numerology(Numerology.N1)
    l0.allocate_resource_block(9, 0, ue)
    ue.set_numerology(Numerology.N2)
    l0.allocate_resource_block(1, 0, ue)
    l0.allocate_resource_block(1, 4, ue)
    l0.allocate_resource_block(9, 4, ue)
    ue.set_numerology(Numerology.N3)
    l0.allocate_resource_block(1, 2, ue)
    l0.allocate_resource_block(1, 3, ue)

    ue.set_numerology(Numerology.N2)
    spaces: Optional[Tuple[Space, ...]] = intuitive.update_empty_space(intuitive.nb, ue)
    assert len(spaces) == 3
    assert spaces[0].starting_i == 9
    assert spaces[0].starting_j == 6
    assert spaces[0].ending_i == 12
    assert spaces[0].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[1].starting_i == 13
    assert spaces[1].starting_j == 0
    assert spaces[1].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[1].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[2].starting_i == 0
    assert spaces[2].starting_j == 0
    assert spaces[2].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[2].ending_j == intuitive.nb.frame.frame_time - 1


    ue.set_numerology(Numerology.N3)
    spaces: Optional[Tuple[Space, ...]] = intuitive.update_empty_space(intuitive.nb, ue)
    assert len(spaces) == 3
    assert spaces[0].starting_i == 9
    assert spaces[0].starting_j == 6
    assert spaces[0].ending_i == 16
    assert spaces[0].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[1].starting_i == 17
    assert spaces[1].starting_j == 0
    assert spaces[1].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[1].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[2].starting_i == 0
    assert spaces[2].starting_j == 0
    assert spaces[2].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[2].ending_j == intuitive.nb.frame.frame_time - 1


def update_space_middle_two_stack_jag2():
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
    intuitive: Intuitive = intuitive_gnb_2l()
    l0: Layer = intuitive.nb.frame.layer[0]
    ue: GUserEquipment = gue()

    ue.set_numerology(Numerology.N0)
    l0.allocate_resource_block(0, 0, ue)
    ue.set_numerology(Numerology.N1)
    l0.allocate_resource_block(9, 0, ue)
    ue.set_numerology(Numerology.N2)
    l0.allocate_resource_block(1, 0, ue)
    l0.allocate_resource_block(1, 3, ue)
    l0.allocate_resource_block(9, 4, ue)
    ue.set_numerology(Numerology.N3)
    l0.allocate_resource_block(1, 2, ue)
    l0.allocate_resource_block(1, 5, ue)

    ue.set_numerology(Numerology.N2)
    spaces: Optional[Tuple[Space, ...]] = intuitive.update_empty_space(intuitive.nb, ue)
    assert len(spaces) == 3
    assert spaces[0].starting_i == 9
    assert spaces[0].starting_j == 6
    assert spaces[0].ending_i == 12
    assert spaces[0].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[1].starting_i == 13
    assert spaces[1].starting_j == 0
    assert spaces[1].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[1].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[2].starting_i == 0
    assert spaces[2].starting_j == 0
    assert spaces[2].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[2].ending_j == intuitive.nb.frame.frame_time - 1

    ue.set_numerology(Numerology.N3)
    spaces: Optional[Tuple[Space, ...]] = intuitive.update_empty_space(intuitive.nb, ue)
    assert len(spaces) == 3
    assert spaces[0].starting_i == 9
    assert spaces[0].starting_j == 6
    assert spaces[0].ending_i == 16
    assert spaces[0].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[1].starting_i == 17
    assert spaces[1].starting_j == 0
    assert spaces[1].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[1].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[2].starting_i == 0
    assert spaces[2].starting_j == 0
    assert spaces[2].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[2].ending_j == intuitive.nb.frame.frame_time - 1


def update_space_middle_two_stack_jags():
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
    intuitive: Intuitive = intuitive_gnb_2l()
    l0: Layer = intuitive.nb.frame.layer[0]
    ue: GUserEquipment = gue()

    ue.set_numerology(Numerology.N0)
    l0.allocate_resource_block(0, 0, ue)
    ue.set_numerology(Numerology.N2)
    l0.allocate_resource_block(1, 0, ue)
    l0.allocate_resource_block(1, 3, ue)
    l0.allocate_resource_block(1, 6, ue)
    l0.allocate_resource_block(9, 1, ue)
    l0.allocate_resource_block(9, 4, ue)
    ue.set_numerology(Numerology.N3)
    l0.allocate_resource_block(1, 2, ue)
    l0.allocate_resource_block(1, 5, ue)
    l0.allocate_resource_block(9, 0, ue)
    l0.allocate_resource_block(9, 3, ue)

    ue.set_numerology(Numerology.N2)
    spaces: Optional[Tuple[Space, ...]] = intuitive.update_empty_space(intuitive.nb, ue)
    assert len(spaces) == 3
    assert spaces[0].starting_i == 9
    assert spaces[0].starting_j == 6
    assert spaces[0].ending_i == 12
    assert spaces[0].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[1].starting_i == 17
    assert spaces[1].starting_j == 0
    assert spaces[1].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[1].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[2].layer.layer_index == 1
    assert spaces[2].starting_i == 0
    assert spaces[2].starting_j == 0
    assert spaces[2].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[2].ending_j == intuitive.nb.frame.frame_time - 1

    ue.set_numerology(Numerology.N3)
    spaces: Optional[Tuple[Space, ...]] = intuitive.update_empty_space(intuitive.nb, ue)
    assert len(spaces) == 3
    assert spaces[0].starting_i == 9
    assert spaces[0].starting_j == 6
    assert spaces[0].ending_i == 16
    assert spaces[0].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[1].starting_i == 17
    assert spaces[1].starting_j == 0
    assert spaces[1].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[1].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[2].layer.layer_index == 1
    assert spaces[2].starting_i == 0
    assert spaces[2].starting_j == 0
    assert spaces[2].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[2].ending_j == intuitive.nb.frame.frame_time - 1


def update_space_end_jag():
    # 0  ********
    #      ...
    # 45 ********
    # 46 ******--
    # 47 ******--
    # 48 ----**--
    # 49 ----**--
    intuitive: Intuitive = intuitive_gnb_3l()
    l0: Layer = intuitive.nb.frame.layer[0]
    ue: GUserEquipment = gue()

    ue.set_numerology(Numerology.N0)
    for i in range(0, 46):
        l0.allocate_resource_block(i, 0, ue)
    ue.set_numerology(Numerology.N1)
    l0.allocate_resource_block(46, 0, ue)
    ue.set_numerology(Numerology.N2)
    l0.allocate_resource_block(46, 4, ue)

    ue.set_numerology(Numerology.N2)
    spaces: Optional[Tuple[Space, ...]] = intuitive.update_empty_space(intuitive.nb, ue)
    assert len(spaces) == 3
    assert spaces[0].starting_i == 46
    assert spaces[0].starting_j == 6
    assert spaces[0].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[0].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[1].layer.layer_index == 1
    assert spaces[1].starting_i == 0
    assert spaces[1].starting_j == 0
    assert spaces[1].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[1].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[2].layer.layer_index == 2
    assert spaces[2].starting_i == 0
    assert spaces[2].starting_j == 0
    assert spaces[2].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[2].ending_j == intuitive.nb.frame.frame_time - 1

    ue.set_numerology(Numerology.N3)
    spaces: Optional[Tuple[Space, ...]] = intuitive.update_empty_space(intuitive.nb, ue)
    assert len(spaces) == 2
    assert spaces[0].layer.layer_index == 1
    assert spaces[0].starting_i == 0
    assert spaces[0].starting_j == 0
    assert spaces[0].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[0].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[1].layer.layer_index == 2
    assert spaces[1].starting_i == 0
    assert spaces[1].starting_j == 0
    assert spaces[1].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[1].ending_j == intuitive.nb.frame.frame_time - 1


def update_space_end_jag_empty():
    # 0  ********
    #      ...
    # 44 ********
    # 45 ******--
    # 46 ******--
    # 47 ----**--
    # 48 ----**--
    # 49 --------
    intuitive: Intuitive = intuitive_gnb_3l()
    l0: Layer = intuitive.nb.frame.layer[0]
    ue: GUserEquipment = gue()

    ue.set_numerology(Numerology.N0)
    for i in range(0, 45):
        l0.allocate_resource_block(i, 0, ue)
    ue.set_numerology(Numerology.N1)
    l0.allocate_resource_block(45, 0, ue)
    ue.set_numerology(Numerology.N2)
    l0.allocate_resource_block(45, 4, ue)

    ue.set_numerology(Numerology.N2)
    spaces: Optional[Tuple[Space, ...]] = intuitive.update_empty_space(intuitive.nb, ue)
    assert len(spaces) == 4
    assert spaces[0].starting_i == 45
    assert spaces[0].starting_j == 6
    assert spaces[0].ending_i == 48
    assert spaces[0].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[1].starting_i == 49
    assert spaces[1].starting_j == 0
    assert spaces[1].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[1].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[2].layer.layer_index == 1
    assert spaces[2].starting_i == 0
    assert spaces[2].starting_j == 0
    assert spaces[2].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[2].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[3].layer.layer_index == 2
    assert spaces[3].starting_i == 0
    assert spaces[3].starting_j == 0
    assert spaces[3].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[3].ending_j == intuitive.nb.frame.frame_time - 1

    ue.set_numerology(Numerology.N3)
    spaces: Optional[Tuple[Space, ...]] = intuitive.update_empty_space(intuitive.nb, ue)
    assert len(spaces) == 2
    assert spaces[0].layer.layer_index == 1
    assert spaces[0].starting_i == 0
    assert spaces[0].starting_j == 0
    assert spaces[0].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[0].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[1].layer.layer_index == 2
    assert spaces[1].starting_i == 0
    assert spaces[1].starting_j == 0
    assert spaces[1].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[1].ending_j == intuitive.nb.frame.frame_time - 1


def update_space_end_jag2():
    # 0  ********
    #      ...
    # 45 ********
    # 46 ******--
    # 47 ******--
    # 48 **------
    # 49 **------
    intuitive: Intuitive = intuitive_gnb_3l()
    l0: Layer = intuitive.nb.frame.layer[0]
    ue: GUserEquipment = gue()

    ue.set_numerology(Numerology.N0)
    for i in range(0, 46):
        l0.allocate_resource_block(i, 0, ue)
    ue.set_numerology(Numerology.N1)
    l0.allocate_resource_block(46, 2, ue)
    ue.set_numerology(Numerology.N2)
    l0.allocate_resource_block(46, 0, ue)

    ue.set_numerology(Numerology.N2)
    spaces: Optional[Tuple[Space, ...]] = intuitive.update_empty_space(intuitive.nb, ue)
    assert len(spaces) == 3
    assert spaces[0].starting_i == 46
    assert spaces[0].starting_j == 6
    assert spaces[0].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[0].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[1].layer.layer_index == 1
    assert spaces[1].starting_i == 0
    assert spaces[1].starting_j == 0
    assert spaces[1].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[1].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[2].layer.layer_index == 2
    assert spaces[2].starting_i == 0
    assert spaces[2].starting_j == 0
    assert spaces[2].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[2].ending_j == intuitive.nb.frame.frame_time - 1

    ue.set_numerology(Numerology.N3)
    spaces: Optional[Tuple[Space, ...]] = intuitive.update_empty_space(intuitive.nb, ue)
    assert len(spaces) == 2
    assert spaces[0].layer.layer_index == 1
    assert spaces[0].starting_i == 0
    assert spaces[0].starting_j == 0
    assert spaces[0].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[0].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[1].layer.layer_index == 2
    assert spaces[1].starting_i == 0
    assert spaces[1].starting_j == 0
    assert spaces[1].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[1].ending_j == intuitive.nb.frame.frame_time - 1


def update_space_end_jag2_empty():
    # 0  ********
    #      ...
    # 44 ********
    # 45 ******--
    # 46 ******--
    # 47 **------
    # 48 **------
    # 49 --------
    intuitive: Intuitive = intuitive_gnb_3l()
    l0: Layer = intuitive.nb.frame.layer[0]
    ue: GUserEquipment = gue()

    ue.set_numerology(Numerology.N0)
    for i in range(0, 45):
        l0.allocate_resource_block(i, 0, ue)
    ue.set_numerology(Numerology.N1)
    l0.allocate_resource_block(45, 2, ue)
    ue.set_numerology(Numerology.N2)
    l0.allocate_resource_block(45, 0, ue)

    ue.set_numerology(Numerology.N2)
    spaces: Optional[Tuple[Space, ...]] = intuitive.update_empty_space(intuitive.nb, ue)
    assert len(spaces) == 4
    assert spaces[0].starting_i == 45
    assert spaces[0].starting_j == 6
    assert spaces[0].ending_i == 48
    assert spaces[0].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[1].starting_i == 49
    assert spaces[1].starting_j == 0
    assert spaces[1].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[1].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[2].layer.layer_index == 1
    assert spaces[2].starting_i == 0
    assert spaces[2].starting_j == 0
    assert spaces[2].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[2].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[3].layer.layer_index == 2
    assert spaces[3].starting_i == 0
    assert spaces[3].starting_j == 0
    assert spaces[3].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[3].ending_j == intuitive.nb.frame.frame_time - 1

    ue.set_numerology(Numerology.N3)
    spaces: Optional[Tuple[Space, ...]] = intuitive.update_empty_space(intuitive.nb, ue)
    assert len(spaces) == 2
    assert spaces[0].layer.layer_index == 1
    assert spaces[0].starting_i == 0
    assert spaces[0].starting_j == 0
    assert spaces[0].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[0].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[1].layer.layer_index == 2
    assert spaces[1].starting_i == 0
    assert spaces[1].starting_j == 0
    assert spaces[1].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[1].ending_j == intuitive.nb.frame.frame_time - 1


def update_space_end_jags():
    #  layer 0      layer 1
    #  ********     0  ********
    #                    ...
    #               41 ********
    #               42 *****---
    #               43 *****---
    #    ...        44 *****---
    #               45 *****---
    #               46 --*-----
    #               47 --*-----
    #               48 --*-----
    #  ********     49 --*-----
    intuitive: Intuitive = intuitive_gnb_2l()
    l0: Layer = intuitive.nb.frame.layer[0]
    l1: Layer = intuitive.nb.frame.layer[1]
    ue: GUserEquipment = gue()

    ue.set_numerology(Numerology.N0)
    for i in range(0, intuitive.nb.frame.frame_freq):
        l0.allocate_resource_block(i, 0, ue)
    for i in range(0, 42):
        l1.allocate_resource_block(i, 0, ue)
    ue.set_numerology(Numerology.N2)
    l1.allocate_resource_block(42, 0, ue)
    l1.allocate_resource_block(42, 3, ue)
    ue.set_numerology(Numerology.N3)
    l1.allocate_resource_block(42, 2, ue)

    ue.set_numerology(Numerology.N2)
    spaces: Optional[Tuple[Space, ...]] = intuitive.update_empty_space(intuitive.nb, ue)
    assert len(spaces) == 1
    assert spaces[0].starting_i == 42
    assert spaces[0].starting_j == 5
    assert spaces[0].ending_i == 45
    assert spaces[0].ending_j == intuitive.nb.frame.frame_time - 1

    ue.set_numerology(Numerology.N3)
    spaces: Optional[Tuple[Space, ...]] = intuitive.update_empty_space(intuitive.nb, ue)
    assert len(spaces) == 1
    assert spaces[0].starting_i == 42
    assert spaces[0].starting_j == 5
    assert spaces[0].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[0].ending_j == intuitive.nb.frame.frame_time - 1


def update_space_end_jags_empty():
    #  layer 0      layer 1
    #  ********     0  ********
    #                    ...
    #               40 ********
    #               41 *****---
    #               42 *****---
    #    ...        43 *****---
    #               44 *****---
    #               45 --*-----
    #               46 --*-----
    #               47 --*-----
    #               48 --*-----
    #  ********     49 --------
    intuitive: Intuitive = intuitive_gnb_2l()
    l0: Layer = intuitive.nb.frame.layer[0]
    l1: Layer = intuitive.nb.frame.layer[1]
    ue: GUserEquipment = gue()

    ue.set_numerology(Numerology.N0)
    for i in range(0, intuitive.nb.frame.frame_freq):
        l0.allocate_resource_block(i, 0, ue)
    for i in range(0, 41):
        l1.allocate_resource_block(i, 0, ue)
    ue.set_numerology(Numerology.N2)
    l1.allocate_resource_block(41, 0, ue)
    l1.allocate_resource_block(41, 3, ue)
    ue.set_numerology(Numerology.N3)
    l1.allocate_resource_block(41, 2, ue)

    ue.set_numerology(Numerology.N2)
    spaces: Optional[Tuple[Space, ...]] = intuitive.update_empty_space(intuitive.nb, ue)
    assert len(spaces) == 2
    assert spaces[0].starting_i == 41
    assert spaces[0].starting_j == 5
    assert spaces[0].ending_i == 44
    assert spaces[0].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[1].layer.layer_index == 1
    assert spaces[1].starting_i == 49
    assert spaces[1].starting_j == 0
    assert spaces[1].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[1].ending_j == intuitive.nb.frame.frame_time - 1

    ue.set_numerology(Numerology.N3)
    spaces: Optional[Tuple[Space, ...]] = intuitive.update_empty_space(intuitive.nb, ue)
    assert len(spaces) == 2
    assert spaces[0].starting_i == 41
    assert spaces[0].starting_j == 5
    assert spaces[0].ending_i == 48
    assert spaces[0].ending_j == intuitive.nb.frame.frame_time - 1
    assert spaces[1].layer.layer_index == 1
    assert spaces[1].starting_i == 49
    assert spaces[1].starting_j == 0
    assert spaces[1].ending_i == intuitive.nb.frame.frame_freq - 1
    assert spaces[1].ending_j == intuitive.nb.frame.frame_time - 1


def update_space_end_two_jags():
    #  layer 0       layer 1
    #  ********      0  ********
    #                     ...
    #                41 ********
    #                42 ********
    #                43 ********
    #    ...         44 ********
    #                45 ********
    #                46 --*--*--
    #                47 --*--*--
    #                48 --*--*--
    #  ********      49 --*--*--
    intuitive: Intuitive = intuitive_gnb_2l()
    l0: Layer = intuitive.nb.frame.layer[0]
    l1: Layer = intuitive.nb.frame.layer[1]
    ue: GUserEquipment = gue()

    ue.set_numerology(Numerology.N0)
    for i in range(0, intuitive.nb.frame.frame_freq):
        l0.allocate_resource_block(i, 0, ue)
    for i in range(0, 42):
        l1.allocate_resource_block(i, 0, ue)
    ue.set_numerology(Numerology.N2)
    l1.allocate_resource_block(42, 0, ue)
    l1.allocate_resource_block(42, 3, ue)
    l1.allocate_resource_block(42, 6, ue)
    ue.set_numerology(Numerology.N3)
    l1.allocate_resource_block(42, 2, ue)
    l1.allocate_resource_block(42, 5, ue)

    for numerology in Numerology:
        ue.set_numerology(numerology)
        spaces: Optional[Tuple[Space, ...]] = intuitive.update_empty_space(intuitive.nb, ue)
        assert len(spaces) == 0


def update_space_to_second_layer():
    # layer 0       layer 1        layer 2
    # 0  ********   0  ********    --------
    #      ...      1  ********
    # 39 ********   2  **----**
    # 40 ********   3  **----**
    # 41 ********   4  ------**
    # 42 ********   5  ------**      ...
    # 43 ********   6  ------**
    # 44 --****--   7  ------**
    # 45 --****--   8  --------
    # 46 --****--
    # 47 --****--        ...
    # 48 --------
    # 49 --------   49 --------    --------
    intuitive: Intuitive = intuitive_gnb_3l()
    l0: Layer = intuitive.nb.frame.layer[0]
    l1: Layer = intuitive.nb.frame.layer[1]
    ue: GUserEquipment = gue()

    ue.set_numerology(Numerology.N0)
    for i in range(0, 40):
        l0.allocate_resource_block(i, 0, ue)
    ue.set_numerology(Numerology.N1)
    l1.allocate_resource_block(0, 2, ue)
    ue.set_numerology(Numerology.N2)
    l0.allocate_resource_block(40, 0, ue)
    l0.allocate_resource_block(40, 6, ue)
    l1.allocate_resource_block(0, 0, ue)
    ue.set_numerology(Numerology.N3)
    l0.allocate_resource_block(40, 2, ue)
    l0.allocate_resource_block(40, 3, ue)
    l0.allocate_resource_block(40, 4, ue)
    l0.allocate_resource_block(40, 5, ue)
    l1.allocate_resource_block(0, 6, ue)
    l1.allocate_resource_block(0, 7, ue)

    for numerology in Numerology:
        ue.set_numerology(numerology)
        spaces: Optional[Tuple[Space, ...]] = intuitive.update_empty_space(intuitive.nb, ue)
        assert len(spaces) == 2
        assert spaces[0].layer.layer_index == 1
        assert spaces[0].starting_i == 8
        assert spaces[0].starting_j == 0
        assert spaces[0].ending_i == intuitive.nb.frame.frame_freq - 1
        assert spaces[0].ending_j == intuitive.nb.frame.frame_time - 1
        assert spaces[1].layer.layer_index == 2
        assert spaces[1].starting_i == 0
        assert spaces[1].starting_j == 0
        assert spaces[1].ending_i == intuitive.nb.frame.frame_freq - 1
        assert spaces[1].ending_j == intuitive.nb.frame.frame_time - 1


def update_space_out_of_space():
    # 0  ********
    #      ...
    # 49 ********
    intuitive: Intuitive = intuitive_enb()
    l0: Layer = intuitive.nb.frame.layer[0]
    ue: DUserEquipment = due()

    for i in range(0, intuitive.nb.frame.frame_freq):
        l0.allocate_resource_block(i, 0, ue)
        l0.allocate_resource_block(i, 4, ue)

    spaces: Optional[Tuple[Space, ...]] = intuitive.update_empty_space(intuitive.nb, ue)
    assert len(spaces) == 0
