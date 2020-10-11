from typing import Optional, Set, Tuple, Union
from uuid import UUID, uuid4

from nodeb import ENBInfoWithinUE, GNBInfoWithinUE
from util_enum import MCS_E, MCS_G, Numerology, UEType


class UserEquipment:
    def __init__(self, request_data_rate: int, candidate_set: Tuple[Numerology]):
        self.uuid: UUID = uuid4()
        self.request_data_rate: int = request_data_rate
        self.candidate_set: Set[Numerology] = set(candidate_set)

        # properties to be configured at runtime
        self.ue_type: Optional[UEType] = None
        self.numerology_in_use: Optional[Numerology] = None
        self.enb_info: ENBInfoWithinUE = ENBInfoWithinUE(request_data_rate)
        self.gnb_info: GNBInfoWithinUE = GNBInfoWithinUE(request_data_rate)

    def set_numerology(self, numerology: Numerology):
        assert numerology in self.candidate_set
        self.numerology_in_use = numerology

    def assign_mcs(self, mcs: Union[MCS_E, MCS_G]):
        raise NotImplementedError
