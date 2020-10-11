from typing import List, Optional, Union

# TODO$ from frame import ResourceBlock
from util_enum import NodeBType, MCS_E, MCS_G


class NodeB:
    def __init__(self):
        self.nb_type: Optional[NodeBType] = None


class _NBInfoWithinUE:
    def __init__(self):
        self.mcs: Optional[Union[MCS_E, MCS_G]] = None
        self.sinr: float = float('-inf')
        # TODO$ self.rb: List[ResourceBlock] = list()
        self.rb: list = list()


class ENBInfoWithinUE(_NBInfoWithinUE):
    def __init__(self):
        super().__init__()
        self.mcs: MCS_E = MCS_E(None)


class GNBInfoWithinUE(_NBInfoWithinUE):
    def __init__(self):
        super().__init__()
        self.mcs: MCS_G = MCS_G(None)
