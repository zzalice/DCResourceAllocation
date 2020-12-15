from src.resource_allocation.ds.eutran import ENodeB
from src.resource_allocation.ds.ngran import GNodeB


def cochannel(enb: ENodeB, gnb: GNodeB, cochannel_bandwidth: int = 25) -> int:
    #                                   5MHz * 1ms
    assert cochannel_bandwidth <= enb.frame.frame_freq and cochannel_bandwidth <= gnb.frame.frame_freq
    # the end of the eNB frame overlaps with the beginning of the gNB frame
    enb.frame.cochannel_offset = enb.frame.frame_freq - cochannel_bandwidth
    gnb.frame.cochannel_offset = cochannel_bandwidth

    for i in range(0, cochannel_bandwidth):
        for j in range(0, gnb.frame.frame_time):
            assert enb.frame.frame_time == gnb.frame.frame_time
            enb.frame.layer[0].bu[i + enb.frame.cochannel_offset][j].set_cochannel(gnb, i)  # only one layer in eNB
            for layer in gnb.frame.layer:
                layer.bu[i][j].set_cochannel(enb, i + enb.frame.cochannel_offset)

    total_bandwidth: int = enb.frame.frame_freq + gnb.frame.frame_freq - cochannel_bandwidth
    return total_bandwidth
