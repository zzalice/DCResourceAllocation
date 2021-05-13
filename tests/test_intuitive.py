from typing import Optional, Tuple

from src.resource_allocation.algo.algo_intuitive import Intuitive
from src.resource_allocation.ds.eutran import ENodeB
from src.resource_allocation.ds.ngran import GNodeB
from src.resource_allocation.ds.space import Space
from src.resource_allocation.ds.util_type import CircularRegion


def enb():
    return ENodeB(region=CircularRegion(0.0, 0.0, 0.5))


def gnb_2l():
    return GNodeB(region=CircularRegion(0.5, 0.0, 0.5), frame_max_layer=2)


def gnb_3l():
    return GNodeB(region=CircularRegion(0.5, 0.0, 0.5), frame_max_layer=3)


def test_update_space():
    update_space_empty()
    update_space_complete_row()


def update_space_empty():
    # 0  --------
    # 1  --------
    #      ...
    # 49 --------
    gnb = gnb_2l()
    intuitive: Intuitive = Intuitive(gnb, (), (), None)
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
    pass
    # 0  ********
    # 1  --------
    #      ...
    # 49 --------


def update_space_():
    pass
    # # (eNB)
    # 0  ********
    # 1  ****----
    # 2  --------
    #      ...
    # 49 --------


def update_space_():
    pass
    # 0  ****----
    # 1  ****----
    # 2  --------
    #      ...
    # 49 --------


def update_space_():
    pass
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
