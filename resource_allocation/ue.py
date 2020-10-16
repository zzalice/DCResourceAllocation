from typing import Optional, Set, Tuple, Union
from uuid import UUID, uuid4

from resource_allocation.enum import E_MCS, G_MCS, Numerology, UEType
from resource_allocation.nodeb import ENBInfo, GNBInfo


class UserEquipment:
    def __init__(self, request_data_rate: int, candidate_set: Tuple[Numerology, ...]):
        self.uuid: UUID = uuid4()
        self.request_data_rate: int = request_data_rate
        self.candidate_set: Set[Numerology] = set(candidate_set)

        # properties to be configured at runtime
        self.ue_type: Optional[UEType] = None
        self.numerology_in_use: Optional[Numerology] = None
        self.enb_info: ENBInfo = ENBInfo(request_data_rate)
        self.gnb_info: GNBInfo = GNBInfo(request_data_rate)

    def set_numerology(self, numerology: Numerology):
        assert numerology in self.candidate_set
        self.numerology_in_use: Numerology = numerology

    def assign_mcs(self, mcs: Union[E_MCS, G_MCS]):
        raise NotImplementedError
