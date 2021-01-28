from __future__ import annotations

from typing import Optional, Tuple, TYPE_CHECKING, Union

from .undo import Undo
from .util_enum import E_MCS, G_MCS, NodeBType, Numerology, SINRtoMCS

if TYPE_CHECKING:
    from .frame import BaseUnit, Layer
    from .ue import UserEquipment


class ResourceBlock(Undo):
    def __init__(self, layer: Layer, starting_i: int, starting_j: int, ue: UserEquipment):
        super().__init__()
        self.layer: Layer = layer
        self.ue: UserEquipment = ue
        self._numerology = ue.numerology_in_use
        self.position: Tuple[int, int, int, int] = self.update_position(starting_i, starting_j)
        self._sinr: float = float('-inf')
        self._mcs: Optional[E_MCS, G_MCS] = None

    def update_position(self, starting_i: int, starting_j: int) -> Tuple[int, int, int, int]:
        self.position: Tuple[int, int, int, int] = (starting_i, starting_i + self.numerology.freq - 1,
                                                    starting_j, starting_j + self.numerology.time - 1)
        return self.position

    def remove(self):
        """
        Removing the allocated RB in ue and frame will effect
        UE throughput, system throughput, and the UEs that has overlapped RB with this RB and
        might also change the UE MCS.
        Here we do only 1. remove the RB in ue and 2. on the frame and 3. mark the RBs that was effected.
        The UE throughput and MCS are updated in Phase3.py.
        """
        # Remove this RB in the UE RB list
        if self.layer.nodeb.nb_type == NodeBType.G:
            self.ue.gnb_info.rb.remove(self)
            self.append_undo([lambda: self.ue.gnb_info.rb.append(self)])
        else:
            self.ue.enb_info.rb.remove(self)
            self.append_undo([lambda: self.ue.enb_info.rb.append(self)])

        # Remove the RB in the layer
        for bu_i in range(self.i_start, self.i_end + 1):
            for bu_j in range(self.j_start, self.j_end + 1):
                bu: BaseUnit = self.layer.bu[bu_i][bu_j]

                # Mark the affected UEs
                for rb in bu.overlapped_rb:
                    origin_value: bool = rb.ue.is_to_recalculate_mcs
                    rb.ue.is_to_recalculate_mcs = True
                    self.append_undo([lambda r=rb: setattr(r.ue, 'is_to_recalculate_mcs', origin_value)])

                bu.clear_up()
                self.append_undo([lambda b=bu: b.set_up(self)])

    @property
    def sinr(self) -> float:
        return self._sinr

    @sinr.setter
    def sinr(self, sinr: float):
        self._sinr: float = sinr
        self._mcs: Union[E_MCS, G_MCS] = SINRtoMCS.sinr_to_mcs(self.sinr, self.layer.nodeb.nb_type)

    @property
    def mcs(self) -> Union[E_MCS, G_MCS]:
        return self._mcs

    @property
    def numerology(self) -> Numerology:
        return self._numerology

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
