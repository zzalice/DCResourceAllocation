from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING, Union

from .enum import E_MCS, G_MCS, NodeBType

if TYPE_CHECKING:
    from .rb import ResourceBlock


class NodeB:
    def __init__(self):
        self.nb_type: Optional[NodeBType] = None


class _NBInfoWithinUE:
    def __init__(self, request_data_rate: int):
        self.mcs: Optional[Union[E_MCS, G_MCS]] = None
        self.sinr: float = float('-inf')
        self.rb: List[ResourceBlock] = list()
        self._num_of_rb_determined_by_mcs: int = 0

        # for supporting (won't access by user)
        self.request_data_rate: int = request_data_rate
        self.nb_type: Optional[NodeBType] = None

    @property
    def num_of_rb(self) -> int:
        return self._num_of_rb_determined_by_mcs

    def update_mcs(self, mcs: Union[E_MCS, G_MCS]):
        self.mcs: Union[E_MCS, G_MCS] = mcs
        self._num_of_rb_determined_by_mcs: int = mcs.calc_required_rb_count(self.request_data_rate)


class ENBInfo(_NBInfoWithinUE):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.nb_type: NodeBType = NodeBType.E
        self.update_mcs(E_MCS(None))

    def update_mcs(self, mcs: E_MCS):
        super().update_mcs(mcs)


class GNBInfo(_NBInfoWithinUE):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.nb_type: NodeBType = NodeBType.G
        self.update_mcs(G_MCS(None))

    def update_mcs(self, mcs: G_MCS):
        super().update_mcs(mcs)
