import math
from random import randint
from typing import List

from src.resource_allocation.ds.cochannel import cochannel
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.frame import BaseUnit, Layer
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.resource_allocation.ds.nodeb import NodeB
from src.resource_allocation.ds.rb import ResourceBlock
from src.resource_allocation.ds.ue import UserEquipment
from src.resource_allocation.ds.util_enum import LTEPhysicalResourceBlock, NodeBType, Numerology
from src.resource_allocation.ds.util_type import Coordinate


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
        """
        SINR(ratio) = rx power(mW) / (interference_noma(mW) + interference_ini(mW) + interference_cross(mW) + awgn(mW))
        :param bu: The BU to calculate its' SINR.
        :return: SINR in dB
        """
        rb: ResourceBlock = bu.within_rb
        ue: UserEquipment = rb.ue
        nodeb: NodeB = bu.layer.nodeb
        power_rx: float = self.power_rx(
            nodeb.nb_type,
            ue.coordinate.distance_gnb if nodeb.nb_type == NodeBType.G else ue.coordinate.distance_enb,
            nodeb.power_tx)

        interference_noma: float = 0.0
        interference_ini: float = 0.0
        interference_cross: float = 0.0
        for layer in nodeb.frame.layer:
            if layer != bu.layer:  # only for gNB, which has multiple layers
                print(f'{bu.relative_j}layer: {layer.nodeb.nb_type} {layer.layer_index}')
                overlapped_bu: BaseUnit = layer.bu[bu.absolute_i][bu.absolute_j]
                if not (overlapped_rb := overlapped_bu.within_rb):  # if the radio resource is not allocated
                    continue
                overlapped_bu_power_rx: float = self.power_rx(nodeb.nb_type,
                                                              overlapped_rb.ue.coordinate.distance_gnb,
                                                              nodeb.power_tx)  # nodeb.power_tx = layer.nodeb.power_tx = overlapped_rb.ue.gnb_info.nb.power_tx
                print(f'{bu.relative_j}power rx: {power_rx}')

                # NOMA interference
                if overlapped_bu_power_rx > power_rx:  # should be comparing channel gain. However, the rx power of the two UE are the same.
                    interference_noma += overlapped_bu_power_rx
                    print(f'{bu.relative_j}interference_noma: {interference_noma}')
                # inter-numerology interference
                if rb.numerology != overlapped_rb.numerology:
                    interference_ini += overlapped_bu_power_rx
                    print(f'{bu.relative_j}interference_ini: {interference_ini}')
        if bu.is_cochannel:
            for layer in bu.cochannel_nb.frame.layer:
                print(f'layer: {layer.nodeb.nb_type} {layer.layer_index}')
                overlapped_bu: BaseUnit = layer.bu[bu.cochannel_bu_i][bu.absolute_j]
                if not (overlapped_rb := overlapped_bu.within_rb):  # if the radio resource is allocated
                    continue
                overlapped_bu_power_rx: float = self.power_rx(
                    nodeb.nb_type,
                    overlapped_rb.ue.coordinate.distance_gnb if nodeb.nb_type == NodeBType.G else overlapped_rb.ue.coordinate.distance_enb,
                    bu.cochannel_nb.power_tx)

                # cross-tier interference
                interference_cross += overlapped_bu_power_rx
                print(f'interference_cross: {interference_cross}')
                # inter-numerology interference
                if rb.numerology.freq != overlapped_rb.numerology.freq:
                    interference_ini += overlapped_bu_power_rx
                    print(f'interference_ini(cross): {interference_ini}')

        sinr = power_rx / (interference_noma + interference_ini + interference_cross + self.awgn_noise)  # ratio
        bu.sinr = 10 * math.log10(sinr)  # ratio to dB

    def power_rx(self, nb_type: NodeBType, distance: float, power_tx: float) -> float:
        """
        Calculate the degraded signal transmitted by the BS to the UE.
        rx power(dBm) = tx power(dBm) - path loss(dB) - shadowing(dB)
        :param nb_type: Either eNB or gNB.
        :param distance: in km. The distance from the BS to the UE.
        :param power_tx: in dBm. The transmit power from BS to UE.
        :return power_rx: in mW. The receive power from BS of UE.
        """
        path_loss: float = self._path_loss_marco(distance) if nb_type == NodeBType.E else self._path_loss_mirco(
            distance)
        power_rx: float = power_tx - path_loss - self.noise(8)  # dBm
        return pow(10, power_rx / 10)  # dBm to mW

    @staticmethod
    def _path_loss_marco(distance: float) -> float:
        """
        A UMa (urban macro-cell) outdoor path loss model.
        ref: TR 36.931 v13.0.0
        :param distance: in kilometer
        :return path loss: in dB
        """
        return 128.1 + 37.6 * math.log10(distance)  # dB

    @staticmethod
    def _path_loss_mirco(distance: float) -> float:
        """
        A UMi (urban micro-cell) outdoor path loss model.
        ref: Proportional Fairness through Dual Connectivity in Heterogeneous Networks
             Dual-Connectivity Enabled Resource Allocation Approach With eICIC for Throughput Maximization in HetNets With Backhaul Constraint
        :param distance: in kilometer
        :return path loss: in dB
        """
        return 140.7 + 36.7 * math.log10(distance)  # dB

    @property
    def awgn_noise(self) -> float:
        """
        AWGN times bandwidth, reference by Techplayon, Signal to Interference and Noise Ratio (SINR),
        http://www.techplayon.com/signal-to-interference-and-noise-ratio-snir/?fbclid=IwAR3cvJQAzcDfA4o1u5zEtbO_Q-ADdPm6wxUS6-dBA7VYjMBNVJLcegTOrnE
        """
        power_spectral_density: int = -174  # dBm/Hz
        bandwidth: int = 180_000  # Hz, for a BU
        noise_power: float = power_spectral_density + 10 * math.log10(bandwidth)  # dBm
        return pow(10, noise_power / 10)  # dBm to mW

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
        https://rosettacode.org/wiki/Linear_congruential_generator#Python
        """
        seed: float = (1103515245 * seed + 12345) & 0x7fffffff
        return seed


if __name__ == '__main__':
    eNB: ENodeB = ENodeB(radius=0.5, coordinate=Coordinate(0.0, 0.0))
    gNB: GNodeB = GNodeB(radius=0.1, coordinate=Coordinate(0.4, 0.0))
    cochannel(eNB, gNB)
    layer_e: Layer = eNB.frame.layer[0]
    layer_1: Layer = gNB.frame.layer[1]
    layer_2: Layer = gNB.frame.layer[0]

    # DUE in eNB, in co-channel area
    # due: UserEquipment = DUserEquipment(12345, [Numerology.N0, Numerology.N1], Coordinate(0.5, 0.0))
    # due.register_nb(eNB, gNB)
    # due.set_numerology(Numerology.N0)
    # layer_e.allocate_resource_block(75, 0, due)
    # rb_: ResourceBlock = due.enb_info.rb[0]

    # DUE in gNB, N0
    due_2: UserEquipment = DUserEquipment(12345, [Numerology.N0, Numerology.N1], Coordinate(0.41, 0.0))
    due_2.register_nb(eNB, gNB)
    due_2.set_numerology(Numerology.N0)
    layer_1.allocate_resource_block(0, 0, due_2)
    rb__: ResourceBlock = due_2.gnb_info.rb[0]

    # GUE, N2
    gue_3: UserEquipment = GUserEquipment(12345, [Numerology.N1, Numerology.N2], Coordinate(0.45, 0.0))
    gue_3.register_nb(eNB, gNB)
    gue_3.set_numerology(Numerology.N2)
    layer_2.allocate_resource_block(0, 0, gue_3)
    rb_3: ResourceBlock = gue_3.gnb_info.rb[0]

    ChannelModel().sinr_rb(rb_3)
