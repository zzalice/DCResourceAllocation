from typing import Optional
from util_enum import NodeBType


class NodeB:
    def __init__(self):
        self.nb_type: Optional[NodeBType] = None
