from typing import Optional
from util_enum import MCS_E, MCS_G, Numerology, UEType


class UserEquipment:
    def __init__(self, sinr: float = float('-inf'), request_data_rate: int = 0, candidate_set: set = None):
        self.sinr: float = sinr
        self.request_data_rate: int = request_data_rate
        self.candidate_set = candidate_set if candidate_set is not None else set()

        # properties to be decided at runtime
        self.ue_type: Optional[UEType] = None
        self.numerology_in_use: Optional[Numerology] = None
        self.mcs: dict = {'e': MCS_E(None), 'g': MCS_G(None)}

    def assign_mcs(self, mcs):
        self.mcs = mcs
