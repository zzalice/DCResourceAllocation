import math
import random
from random import randint
from typing import Dict, List, Tuple

from src.resource_allocation.ds.cochannel import cochannel
from src.resource_allocation.ds.eutran import ENodeB
from src.resource_allocation.ds.frame import BaseUnit, Layer
from src.resource_allocation.ds.ngran import GNodeB, GUserEquipment
from src.resource_allocation.ds.nodeb import NodeB
from src.resource_allocation.ds.rb import ResourceBlock
from src.resource_allocation.ds.ue import UserEquipment
from src.resource_allocation.ds.util_enum import NodeBType, Numerology
from src.resource_allocation.ds.util_type import Coordinate


class ChannelModel:
    def __init__(self, cochannel_index: Dict):
        self.cochannel_index: Dict = cochannel_index
        self.channel_bs: Tuple[List[Coordinate], ...] = self.gen_channel_interference()

    def sinr_ue(self, ue: UserEquipment):
        """
        Update the SINR for every RBs in the UE,
        but this isn't the final SINR of the UE.
        """
        if hasattr(ue, 'gnb_info'):
            for rb in ue.gnb_info.rb:
                self.sinr_rb(rb)
            ue.gnb_info.rb.sort(key=lambda x: x.sinr, reverse=True)
        if hasattr(ue, 'enb_info'):
            for rb in ue.enb_info.rb:
                self.sinr_rb(rb)
            ue.enb_info.rb.sort(key=lambda x: x.sinr, reverse=True)

    def sinr_rb(self, rb: ResourceBlock):
        tmp_sinr_rb: float = float('inf')
        for bu_i in range(rb.position[0], rb.position[1] + 1):
            for bu_j in range(rb.position[2], rb.position[3] + 1):
                self.sinr_bu(rb.layer.bu[bu_i][bu_j])
                if tmp_sinr_rb > rb.layer.bu[bu_i][bu_j].sinr:
                    tmp_sinr_rb: float = rb.layer.bu[bu_i][bu_j].sinr
        rb.sinr = tmp_sinr_rb
        print(f'RB SINR: {rb.sinr}')

    def sinr_bu(self, bu: BaseUnit):
        """
        SINR(ratio) = rx power(mW) / (noma(mW) + ini(mW) + cross-tier(mW) + interference from other BSs(mW) + awgn(mW))
        :param bu: The BU to calculate its' SINR.
        :return: SINR in dB
        """
        print(f'rb({bu.relative_i},{bu.relative_j})')
        rb: ResourceBlock = bu.within_rb
        ue: UserEquipment = rb.ue
        nodeb: NodeB = bu.layer.nodeb
        power_rx: float = self.power_rx(
            nodeb,
            ue.coordinate.distance_gnb if nodeb.nb_type == NodeBType.G else ue.coordinate.distance_enb)
        print(f'power rx: {10 * math.log10(power_rx)}')

        interference_noma: float = 0.0
        interference_ini: float = 0.0
        interference_cross: float = 0.0
        for overlapped_rb in bu.overlapped_rb:
            overlapped_bu_power_rx: float = self.power_rx(
                overlapped_rb.layer.nodeb,
                ue.coordinate.distance_gnb if overlapped_rb.layer.nodeb.nb_type == NodeBType.G else ue.coordinate.distance_enb)
            if overlapped_rb.layer.nodeb.nb_type == NodeBType.G and nodeb.nb_type == NodeBType.G:
                # NOMA interference
                """
                The formal way is compared by |h|^2 / N.
                As the reference bellow, this part is done by comparing power and power is related to distance.
                https://ecewireless.blogspot.com/2020/04/how-to-simulate-ber-capacity-and-outage.html
                """
                if overlapped_rb.ue.coordinate.distance_gnb < ue.coordinate.distance_gnb:
                    interference_noma += overlapped_bu_power_rx
                    print(f'interference_noma: {10 * math.log10(interference_noma)}')
            if overlapped_rb.layer.nodeb.nb_type != nodeb.nb_type:
                # cross-tier interference
                interference_cross += overlapped_bu_power_rx
                print(f'interference_cross: {10 * math.log10(interference_cross)}')
            # inter-numerology interference
            if overlapped_rb.numerology.freq != rb.numerology.freq:
                interference_ini += overlapped_bu_power_rx
                print(f'interference_ini: {10 * math.log10(interference_ini)}')
        interference_channel: float = self.channel_interference(bu)

        sinr = power_rx / (
                interference_noma + interference_ini + interference_cross + interference_channel + self.awgn_noise)  # ratio
        bu.sinr = 10 * math.log10(sinr)  # ratio to dB
        print(f'BU SINR: {bu.sinr}')

    def power_rx(self, tx_nb: NodeB, distance: float) -> float:
        """
        Calculate the degraded signal transmitted by the BS to the UE.
        rx power(dBm) = tx power(dBm) - path loss(dB) - shadowing(dB)
        :param tx_nb: The signal is transmitted by tx_nb.
        :param distance: in km. The distance from the BS to the UE.
        :return power_rx: in mW. The receive power from BS of UE.
        """
        path_loss: float = self._path_loss_marco(distance) if tx_nb.nb_type == NodeBType.E else self._path_loss_mirco(
            distance)
        power_rx: float = tx_nb.power_tx - path_loss - self.noise(8)  # dBm
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
             Dual-Connectivity Enabled Resource Allocation Approach With eICIC
             for Throughput Maximization in HetNets With Backhaul Constraint.
        :param distance: in kilometer
        :return path loss: in dB
        """
        return 140.7 + 36.7 * math.log10(distance)  # dB

    @property
    def awgn_noise(self) -> float:
        """
        AWGN times bandwidth, reference by Techplayon, Signal to Interference and Noise Ratio (SINR),
        http://www.techplayon.com/signal-to-interference-and-noise-ratio-snir/?fbclid=IwAR3cvJQAzcDfA4o1u5zEtbO_Q-ADdPm6wxUS6-dBA7VYjMBNVJLcegTOrnE
        Confirmed by https://www.everythingrf.com/rf-calculators/noise-power-calculator,
            Temperature = 20 C, Bandwidth = 180_000 Hz
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
        stemp: float = 2 * log_value / slevel  # used "-2" in Wang's C code
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

    def channel_interference(self, bu: BaseUnit) -> float:
        """
        The interference from far away BSs using the same channel.
        Assume the BSs are all eNB.
        """
        e_nb: ENodeB = ENodeB(Coordinate(4, 8))  # just for generating rx power

        if bu.layer.nodeb.nb_type == NodeBType.E:
            channel: int = bu.absolute_i
        else:
            channel: int = bu.absolute_i + self.cochannel_index['e_freq'] - self.cochannel_index['co_bandwidth']

        interference: float = 0.0
        for bs in self.channel_bs[channel]:
            dist: float = bs.calc_distance(bs, bu.within_rb.ue.coordinate)
            interference += self.power_rx(e_nb, dist)
        if interference:
            print(f'interference_BSs: {10 * math.log10(interference)}')

        return interference

    def gen_channel_interference(self) -> Tuple[List[Coordinate], ...]:
        """
        interference_info =
            (BU1[BS[coordinate], BS[], BS[]],
             BU2[BS[]],
             BU3[BS[], BS[]],
             BU4[BS[], BS[], BS[]],
             ...,
             BUi[BS[]])
        """
        bs1: Coordinate = Coordinate(x=2, y=0)
        bs2: Coordinate = Coordinate(x=0, y=2)
        bs3: Coordinate = Coordinate(x=-2, y=0)
        bs4: Coordinate = Coordinate(x=0, y=-2)
        total_bw: int = self.cochannel_index['e_freq'] + self.cochannel_index['g_freq'] - self.cochannel_index[
            'co_bandwidth']  # the total bandwidth of gNB and eNB, in the number of BUs
        interference_info: Tuple[List[Coordinate], ...] = tuple([] for _ in range(total_bw))

        # deploy the channels to BSs
        j = 0
        bs: List[Coordinate] = []
        for i in range(total_bw):
            if not j % 25:  # all the BSs' channel bandwidth are 5MHz, 25 RBs
                bs: List[Coordinate] = random.sample([bs1, bs2, bs3, bs4], k=random.choice([0, 1, 2, 3]))
                j = 0
            interference_info[i].extend(bs)
            j += 1

        return interference_info


if __name__ == '__main__':
    eNB: ENodeB = ENodeB(radius=0.5, coordinate=Coordinate(0.0, 0.0))
    gNB: GNodeB = GNodeB(radius=0.1, coordinate=Coordinate(0.4, 0.0))
    co_index: Dict = cochannel(eNB, gNB)
    layer_e: Layer = eNB.frame.layer[0]
    layer_0: Layer = gNB.frame.layer[0]
    layer_1: Layer = gNB.frame.layer[1]
    layer_2: Layer = gNB.frame.layer[2]

    # EUE, in co-channel area
    # eue_1: UserEquipment = EUserEquipment(12345, [LTEPhysicalResourceBlock], Coordinate(0.3, 0.0))
    # eue_1.register_nb(eNB, gNB)
    # layer_e.allocate_resource_block(75, 0, eue_1)
    # rb_0: ResourceBlock = eue_1.enb_info.rb[0]

    # DUE in eNB, in co-channel area
    # due_1: UserEquipment = DUserEquipment(12345, [Numerology.N0, Numerology.N1], Coordinate(0.5, 0.0))
    # due_1.register_nb(eNB, gNB)
    # due_1.set_numerology(Numerology.N0)
    # layer_e.allocate_resource_block(75, 0, due_1)
    # rb_1: ResourceBlock = due_1.enb_info.rb[0]

    # DUE in gNB, N0
    # due_2: UserEquipment = DUserEquipment(12345, [Numerology.N0, Numerology.N1], Coordinate(0.399, 0.0))
    # due_2.register_nb(eNB, gNB)
    # due_2.set_numerology(Numerology.N0)
    # layer_0.allocate_resource_block(0, 0, due_2)
    # rb_2: ResourceBlock = due_2.gnb_info.rb[0]

    # GUE, N0
    # gue_1: UserEquipment = GUserEquipment(12345, [Numerology.N0, Numerology.N1], Coordinate(0.30000001, 0.0))
    # gue_1.register_nb(eNB, gNB)
    # gue_1.set_numerology(Numerology.N0)
    # layer_1.allocate_resource_block(0, 0, gue_1)
    # rb_3: ResourceBlock = gue_1.gnb_info.rb[0]

    # GUE, N1
    gue_2: UserEquipment = GUserEquipment(12345, [Numerology.N1, Numerology.N2], Coordinate(0.43, 0.0))
    gue_2.register_nb(eNB, gNB)
    gue_2.set_numerology(Numerology.N1)
    layer_0.allocate_resource_block(0, 0, gue_2)
    rb_4: ResourceBlock = gue_2.gnb_info.rb[0]

    # GUE, N2
    gue_3: UserEquipment = GUserEquipment(12345, [Numerology.N1, Numerology.N2], Coordinate(0.5, 0.0))
    gue_3.register_nb(eNB, gNB)
    gue_3.set_numerology(Numerology.N2)
    layer_1.allocate_resource_block(0, 0, gue_3)
    rb_5: ResourceBlock = gue_3.gnb_info.rb[0]

    # GUE, N3
    gue_4: UserEquipment = GUserEquipment(12345, [Numerology.N1, Numerology.N2, Numerology.N3], Coordinate(0.5, 0.0))
    gue_4.register_nb(eNB, gNB)
    gue_4.set_numerology(Numerology.N3)
    layer_2.allocate_resource_block(0, 0, gue_4)
    rb_6: ResourceBlock = gue_4.gnb_info.rb[0]

    channel_model: ChannelModel = ChannelModel(co_index)
    channel_model.sinr_rb(rb_6)
