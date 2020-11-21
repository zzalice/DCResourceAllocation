from __future__ import annotations

from typing import Tuple, TYPE_CHECKING

from .util_enum import Numerology

if TYPE_CHECKING:
    from .frame import Layer
    from .ue import UserEquipment


class ResourceBlock:
    def __init__(self, layer: Layer, starting_i: int, starting_j: int, ue: UserEquipment):
        self.layer: Layer = layer
        self.ue: UserEquipment = ue
        self.position: Tuple[int, int, int, int] = self.update_position(starting_i, starting_j)

    def update_position(self, starting_i: int, starting_j: int) -> Tuple[int, int, int, int]:
        self.position: Tuple[int, int, int, int] = (starting_i, starting_i + self.numerology.freq - 1,
                                                    starting_j, starting_j + self.numerology.time - 1)
        return self.position

    @property
    def numerology(self) -> Numerology:
        return self.ue.numerology_in_use    # TODO: not correct if it's dUE

    @property
    def i_start(self) -> int:
        return self.position[0]

    @property
    def i_end(self) -> int:
        return self.position[1]

    @property
    def j_start(self) -> int:
        return self.position[2]

    @property
    def j_end(self) -> int:
        return self.position[3]
