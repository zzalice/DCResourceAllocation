import math
from random import randint
from typing import List

from src.resource_allocation.ds.frame import BaseUnit, Layer
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB
from src.resource_allocation.ds.nodeb import NodeB
from src.resource_allocation.ds.rb import ResourceBlock
from src.resource_allocation.ds.ue import UserEquipment
from src.resource_allocation.ds.util_enum import NodeBType, Numerology


class ChannelModel:
    def __init__(self):
        pass

    def sinr_rb(self, rb: ResourceBlock):
        tmp_sinr_rb: float = float('inf')
        for bu_i in range(rb.position[0], rb.position[1] + 1):
            for bu_j in range(rb.position[2], rb.position[3] + 1):
                self.sinr_bu(rb.layer.bu[bu_i][bu_j])
                if tmp_sinr_rb > rb.layer.bu[bu_i][bu_j].sinr:
                    tmp_sinr_rb: float = rb.layer.bu[bu_i][bu_j].sinr
        rb.sinr = tmp_sinr_rb

    def sinr_bu(self, bu: BaseUnit):
        ue: UserEquipment = bu.within_rb.ue
        nodeb: NodeB = bu.layer.nodeb
        power_rx: float = self.power_rx(
            (ue.gnb_info if nodeb.nb_type == NodeBType.G else ue.enb_info).distance, nodeb.power_tx)

        interference_noma: float = 0.0
        interference_ini: float = 0.0
        interference_cross: float = 0.0
        if nodeb.nb_type == NodeBType.G:
            for layer in nodeb.frame.layer:
                if layer != bu.layer:
                    overlapped_bu: BaseUnit = layer.bu[bu.absolute_i][bu.absolute_j]
                    try:
                        overlapped_ue: UserEquipment = overlapped_bu.within_rb.ue
                    except AttributeError:
                        continue
                    overlapped_bu_power_rx = self.power_rx(overlapped_ue.gnb_info.distance, nodeb.power_tx)
                    if power_rx > overlapped_bu_power_rx:
                        interference_noma += overlapped_bu_power_rx
                    if bu.within_rb.numerology != overlapped_bu.within_rb.numerology:
                        interference_ini += overlapped_bu_power_rx
            # interference_ini += self.power_rx()     # TODO: co-channel
            # interference_cross += 0.0               # TODO: co-channel. The other BS, eNB.
        elif nodeb.nb_type == NodeBType.E:
            pass
            # interference_ini += self.power_rx()     # TODO: co-channel
            # interference_cross += 0.0               # TODO: co-channel
        awgn_noise = pow(10, 17.4) * 180_000  # awgn noise: mW, awgn: mW/Hz, bu_bandwidth: 180_000 Hz

        bu.sinr = power_rx / (interference_noma + interference_ini + interference_cross + awgn_noise)

    def power_rx(self, distance: float, power_tx: float) -> float:
        """
        Calculate the degraded signal transmitted by the BS to the UE.
        :param distance: in km. The distance from the BS to the UE.
        :param power_tx: in mW. The transmit power from BS to UE.
        :return power_rx: in mW. The receive power from BS of UE.
        """
        return self.channel_gain(distance) * power_tx

    def channel_gain(self, distance: float) -> float:
        """
        Calculate the channel gain of a UE.
        Channel gain = path loss * shadowing
        :return channel gain: in ratio
        """
        return self._path_loss(distance) * self.noise(8)

    @staticmethod
    def _path_loss(distance: float) -> float:
        """
        A UMa (urban macro-cell) outdoor path loss model.
        ref: TR 36.931 v13.0.0
        :param distance: in kilometer
        :return path loss: in ratio
        """
        path_loss = 128.1 + 37.6 * math.log10(distance)  # dB
        return pow(10, path_loss / 10)  # dB to ratio

    def noise(self, noise_variance: int) -> float:
        seed: int = 0 - randint(1, 100)
        slevel: float = 0.0
        runiform: List[float] = [0.0, 0.0]
        while slevel < 1.0:
            runiform[0]: float = self.bsd_rand(seed)
            runiform[1]: float = self.bsd_rand(seed)
            runiform[0]: float = 2.0 * runiform[0] - 1.0
            runiform[1]: float = 2.0 * runiform[1] - 1.0
            slevel: float = runiform[0] * runiform[0] + runiform[1] * runiform[1]

        log_value: float = math.log10(slevel)
        stemp: float = 2 * log_value / slevel  # original -2
        noise: float = math.sqrt(noise_variance) * runiform[0] * math.sqrt(stemp)
        return noise

    @staticmethod
    def bsd_rand(seed: int) -> float:
        """
        LCG(Linear congruential generator)
        https://rosettacode.org/wiki/Linear_congruential_generator#Python
        """
        seed: float = (1103515245 * seed + 12345) & 0x7fffffff
        return seed


if __name__ == '__main__':
    gNB: NodeB = GNodeB()
    layer_: Layer = gNB.frame.layer[1]
    ue_: UserEquipment = DUserEquipment(12345, [Numerology.N1])
    ue_.set_numerology(Numerology.N1)
    ue_.gnb_info.distance = 0.9
    rb_: ResourceBlock = ResourceBlock(layer_, 2, 2, ue_)
    layer_.allocate_resource_block(2, 2, ue_)

    layer__: Layer = gNB.frame.layer[0]
    ue__: UserEquipment = DUserEquipment(12345, [Numerology.N1])
    ue__.set_numerology(Numerology.N1)
    ue__.gnb_info.distance = 0.1
    rb__: ResourceBlock = ResourceBlock(layer__, 2, 2, ue__)
    layer__.allocate_resource_block(2, 2, ue__)

    ChannelModel().sinr_rb(rb_)
