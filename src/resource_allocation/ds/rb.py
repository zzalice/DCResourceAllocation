from __future__ import annotations

from typing import Any, Dict, Optional, Tuple, TYPE_CHECKING, Union

from .undo import Undo
from .util_enum import E_MCS, G_MCS, NodeBType, Numerology

if TYPE_CHECKING:
    from .frame import BaseUnit, Layer
    from .ue import UserEquipment


class ResourceBlock(Undo):
    def __repr__(self):
        return f'U{self.ue.uuid.hex[:4]} R{str(id(self))[:4]} M{self.mcs.name[3:5]}'

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

    @Undo.undo_func_decorator
    def remove_rb(self):
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
            self.append_undo(lambda: self.ue.gnb_info.rb.append(self))
        else:
            self.ue.enb_info.rb.remove(self)
            self.append_undo(lambda: self.ue.enb_info.rb.append(self))

        # Remove the RB in the layer
        for bu_i in range(self.i_start, self.i_end + 1):
            for bu_j in range(self.j_start, self.j_end + 1):
                bu: BaseUnit = self.layer.bu[bu_i][bu_j]
                bu.clear_up()
                self.append_undo(lambda b=bu: b.undo(), lambda b=bu: b.purge_undo())

    @property
    def sinr(self) -> float:
        return self._sinr

    @sinr.setter
    def sinr(self, sinr: float):
        self._sinr: float = sinr
        self._mcs: Union[E_MCS, G_MCS] = (G_MCS if self.layer.nodeb.nb_type == NodeBType.G else E_MCS).sinr_to_mcs(
            self.sinr)

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

    def to_json(self) -> Dict[str, Any]:
        rb: Dict[str, Any] = {
            'layer': self.layer.layer_index,
            'i_start': self.i_start,
            'j_start': self.j_start,
            'numerology': self.numerology.name if self.numerology else None,
            'mcs': self.mcs.index if self.mcs else None
        }
        return rb
