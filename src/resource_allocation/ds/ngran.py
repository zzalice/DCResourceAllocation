from typing import Union

from .nodeb import NodeB
from .ue import UserEquipment
from .util_enum import E_MCS, G_MCS, NodeBType, UEType


class GNodeB(NodeB):
    def __init__(self, *args, **kwargs):
        # default: 1.0km, 20MHz * 10ms * 3layers, TODO: check if 20MHz == 100BUs ??
        default_kwargs = dict(radius=1.0, frame_freq=100, frame_max_layer=3)  # TODO: this workaround should be fixed
        default_kwargs.update(kwargs)
        super().__init__(*args, **default_kwargs)
        self.nb_type: NodeBType = NodeBType.G


class GUserEquipment(UserEquipment):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ue_type: UEType = UEType.G
        del self.enb_info

    def assign_mcs(self, mcs: G_MCS):
        self.gnb_info.mcs = mcs


class DUserEquipment(UserEquipment):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ue_type: UEType = UEType.D

    def assign_mcs(self, mcs: Union[E_MCS, G_MCS]):
        if isinstance(mcs, E_MCS):
            self.enb_info.mcs = mcs
        elif isinstance(mcs, G_MCS):
            self.gnb_info.mcs = mcs
