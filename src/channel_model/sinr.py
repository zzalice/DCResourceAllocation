import math
from random import randint
from typing import List

from src.resource_allocation.ds.frame import _BaseUnit
from src.resource_allocation.ds.ue import UserEquipment
from src.resource_allocation.ds.util_enum import NodeBType


class ChannelModel:
    def __init__(self):
        pass

    def sinr_rb(self):
        raise NotImplemented

    # def sinr_bu(self, bu: _BaseUnit, nodeb: NodeBType):
    #     ue: UserEquipment = bu.within_rb.ue
    #     power_rx = self.power_rx((ue.gnb_info if nodeb.nb_type == NodeBType.G else ue.enb_info).distance, nb.power_tx)
    #     if nodeb.nb_type == NodeBType.G:
    #         interference_noma = self.power_rx()  # TODO: overlap BUs
    #     else:
    #         interference_noma = 0
    #     interference_ini = self.power_rx()  # TODO: overlap BUs
    #     interference_cross = self.power_rx()  # TODO: overlap BUs
    #     awgn_noise = pow(10, 17.4) * 180_000  # awgn noise: mW, awgn: mW/Hz, bu_bandwidth: 180_000 Hz
    #     return power_rx / (interference_noma + interference_ini + interference_cross + awgn_noise)

    def power_rx(self, distance: float, power_tx) -> float:
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
        return noise  # dB

    @staticmethod
    def bsd_rand(seed: int) -> float:
        """
        LCG(Linear congruential generator)
        """
        seed: float = (1103515245 * seed + 12345) & 0x7fffffff
        return seed
