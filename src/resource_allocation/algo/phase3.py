from src.channel_model.sinr import ChannelModel
from src.resource_allocation.ds.eutran import ENodeB
from src.resource_allocation.ds.ngran import GNodeB
from src.resource_allocation.ds.undo import Undo


class Phase3(Undo):
    def __init__(self, channel_model: ChannelModel, gnb: GNodeB, enb: ENodeB):
        super().__init__()
        self.channel_model: ChannelModel = channel_model
        self.gnb: GNodeB = gnb
        self.enb: ENodeB = enb
        # self.adjust_mcs = AdjustMCS(self.channel_model)

    # def zone_group_adjust_mcs(self):
    #     for zone_group in self.zone_groups_gnb:
    #         for b in zone_group.bin:
    #             for zone in b.zone:
    #                 for ue in zone.ue_list:

