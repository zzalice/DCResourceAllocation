from dataclasses import dataclass


@dataclass
class RBIndex:
    layer: int
    i: int
    j: int
