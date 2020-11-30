from src.resource_allocation.ds.eutran import ENodeB
from src.resource_allocation.ds.ngran import GNodeB


def cochannel(enb: ENodeB, gnb: GNodeB, bandwidth: int = 25):
                                        # 5MHz * 1ms
    assert bandwidth <= enb.frame.frame_freq and bandwidth <= gnb.frame.frame_freq
    # the end of the eNB frame overlaps with the beginning of the gNB frame
    for bu_i in range(enb.frame.frame_freq - bandwidth, enb.frame.frame_freq):
        for bu_j in range(0, enb.frame.frame_time):
            enb.frame.layer[0].bu[bu_i][bu_j].set_cochannel(gnb)
    for bu_i in range(0, bandwidth):
        for bu_j in range(0, gnb.frame.frame_time):
            for layer in gnb.frame.layer:
                layer.bu[bu_i][bu_j].set_cochannel(enb)
