from typing import Optional
from uuid import uuid4, UUID

from util_enum import MCS_E, MCS_G, Numerology, UEType


class UserEquipment:
    def __init__(self, sinr: float = float('-inf'), request_data_rate: int = 0, candidate_set: set = None):
        self.uuid: UUID = uuid4()
        self.sinr: float = sinr
        self.request_data_rate: int = request_data_rate
        # candidate_set is {Numerology.N0~N4 (all)} by default
        self.candidate_set: set = candidate_set if candidate_set is not None else {n for n in Numerology}

        # properties to be configured at runtime
        self.ue_type: Optional[UEType] = None
        self.numerology_in_use: Optional[Numerology] = None
        self.mcs: dict = {'e': MCS_E(None), 'g': MCS_G(None)}

    def set_numerology(self, numerology: Numerology):
        assert numerology in self.candidate_set
        self.numerology_in_use = numerology

    def assign_mcs(self, mcs: dict):
        self.mcs = mcs
