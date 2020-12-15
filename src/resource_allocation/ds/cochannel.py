from src.resource_allocation.ds.eutran import ENodeB
from src.resource_allocation.ds.ngran import GNodeB


def cochannel(enb: ENodeB, gnb: GNodeB, cochannel_bandwidth_bu: int = 25) -> int:
    #                                   5MHz * 1ms
    assert cochannel_bandwidth_bu <= enb.frame.frame_freq and cochannel_bandwidth_bu <= gnb.frame.frame_freq
    # the end of the eNB frame overlaps with the beginning of the gNB frame
    enb.frame.cochannel_offset = enb.frame.frame_freq - cochannel_bandwidth_bu
    gnb.frame.cochannel_offset = cochannel_bandwidth_bu

    for bu_i in range(0, cochannel_bandwidth_bu):
        for bu_j in range(0, gnb.frame.frame_time):
            assert enb.frame.frame_time == gnb.frame.frame_time
            enb_freq_offset = enb.frame.frame_freq - cochannel_bandwidth_bu
            enb.frame.layer[0].bu[bu_i + enb_freq_offset][bu_j].set_cochannel(gnb, bu_i)  # only one layer in eNB
            for layer in gnb.frame.layer:
                layer.bu[bu_i][bu_j].set_cochannel(enb, bu_i + enb_freq_offset)

    total_bandwidth: int = enb.frame.frame_freq + gnb.frame.frame_freq - cochannel_bandwidth_bu
    return total_bandwidth
