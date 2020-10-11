from typing import List, Optional, Union

# TODO$ from frame import ResourceBlock
from util_enum import NodeBType, MCS_E, MCS_G


class NodeB:
    def __init__(self):
        self.nb_type: Optional[NodeBType] = None


class _NBInfoWithinUE:
    def __init__(self, request_data_rate: int):
        self.mcs: Optional[Union[MCS_E, MCS_G]] = None
        self.sinr: float = float('-inf')
        # TODO$ self.rb: List[ResourceBlock] = list()  # circular import error
        self.rb: list = list()
        self._number_of_rb_determined_by_mcs: int = 0

        # for supporting (won't access by user)
        self.request_data_rate = request_data_rate
        self.nb_type: Optional[NodeBType] = None

    @property
    def num_of_rb(self) -> int:
        return self._number_of_rb_determined_by_mcs

    def update_mcs(self, mcs: Union[MCS_E, MCS_G]):
        self.mcs = mcs
        self._number_of_rb_determined_by_mcs = mcs.calc_required_rb_count(self.request_data_rate)


class ENBInfoWithinUE(_NBInfoWithinUE):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.nb_type = NodeBType.E
        self.update_mcs(MCS_E(None))

    def update_mcs(self, mcs: MCS_E):
        super().update_mcs(mcs)


class GNBInfoWithinUE(_NBInfoWithinUE):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.nb_type = NodeBType.G
        self.update_mcs(MCS_G(None))

    def update_mcs(self, mcs: MCS_G):
        super().update_mcs(mcs)
