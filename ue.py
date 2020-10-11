from typing import Optional, Union
from uuid import UUID, uuid4

from nodeb import ENBInfoWithinUE, GNBInfoWithinUE
from util_enum import MCS_E, MCS_G, Numerology, UEType


class UserEquipment:
    def __init__(self, request_data_rate: int = 0, candidate_set: set = None):
        self.uuid: UUID = uuid4()
        self.request_data_rate: int = request_data_rate
        # candidate_set is init as ALL AVAILABLE {Numerology.N0~N4} by default
        self.candidate_set: set = candidate_set if candidate_set is not None else {n for n in Numerology}

        # properties to be configured at runtime
        self.ue_type: Optional[UEType] = None
        self.numerology_in_use: Optional[Numerology] = None
        self.enb_info: ENBInfoWithinUE = ENBInfoWithinUE()
        self.gnb_info: GNBInfoWithinUE = GNBInfoWithinUE()

    def set_numerology(self, numerology: Numerology):
        assert numerology in self.candidate_set
        self.numerology_in_use = numerology

    def assign_mcs(self, mcs: Union[MCS_E, MCS_G]):
        raise NotImplementedError
