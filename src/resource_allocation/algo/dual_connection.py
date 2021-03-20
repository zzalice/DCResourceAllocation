from typing import List, Optional, Union

from src.channel_model.adjust_mcs import AdjustMCS
from src.channel_model.sinr import ChannelModel
from src.resource_allocation.algo.max_subarray import MaxSubarray
from src.resource_allocation.algo.new_resource_allocation import AllocateUE
from src.resource_allocation.ds.ngran import DUserEquipment
from src.resource_allocation.ds.nodeb import ENBInfo, GNBInfo
from src.resource_allocation.ds.space import empty_space, Space
from src.resource_allocation.ds.undo import Undo
from src.resource_allocation.ds.util_enum import E_MCS, G_MCS, NodeBType, UEType


class DualConnection(Undo):
    def __init__(self, ue: DUserEquipment, channel_model: ChannelModel):
        """
        :param ue: Must be dUE, and can be a single or dual connection dUE.
        :param channel_model:
        """
        super().__init__()
        assert ue.ue_type == UEType.D and ue.is_allocated
        self.ue: DUserEquipment = ue
        self.channel_model: ChannelModel = channel_model

    def cutting(self, nb_info: Union[GNBInfo, ENBInfo]):
        """
        Cut part of the RBs in a BS to another BS.
        To improve resource efficiency by using fewer RBs.
        :param nb_info: The BS to be modified.
        :return: Always True because there's no cutting failure.
        """
        another_nb_info: Union[
            GNBInfo, ENBInfo] = self.ue.gnb_info if nb_info.nb_type == NodeBType.E else self.ue.enb_info

        is_cut: bool = self._cutting(nb_info, another_nb_info)
        if not is_cut:
            self.undo()
        return is_cut

    @Undo.undo_func_decorator
    def _cutting(self, nb_info: Union[GNBInfo, ENBInfo], another_nb_info: Union[GNBInfo, ENBInfo]) -> bool:
        while True:
            if not self.remove_list_of_rb(nb_info, another_nb_info):
                return False

            if self.ue.calc_throughput() >= self.ue.request_data_rate:
                # SPECIAL CASE: After the MCS is improved, the QoS is fulfill and might even need less RBs.
                # For example, the origin RB list is [CQI 2, CQI 1, CQI 11, CQI 11, CQI 11, CQI 11, CQI 11, CQI 2],
                #   throughput = CQI 1 * 8 = 176.085
                # After removing the first two RBs, the RB list became [CQI 11, CQI 11, CQI 11, CQI 11, CQI 11, CQI 2],
                #   throughput = CQI 2 * 6 = 203.175
                # but the ue.request_data_rate is 160.
                # Eventually, the UE only need ONE RB of CQI 11.
                self.adjust_mcs()
                continue

            # find spaces in another BS to fulfill QoS
            spaces: List[Space] = [space for layer in another_nb_info.nb.frame.layer for space in empty_space(layer)]

            # add new RBs
            if spaces:
                allocate_ue = AllocateUE(self.ue, tuple(spaces), self.channel_model)
                is_succeed: bool = allocate_ue.allocate()
                self.append_undo(lambda a_u=allocate_ue: a_u.undo(), lambda a_u=allocate_ue: a_u.purge_undo())
                if is_succeed:
                    self.adjust_mcs()   # The new RB(s) from the other BS has high MCS which will fulfill QoS on it's own.
                # TODO: if another BSs' MCS is lower after cut(in other word, the total num of RBs increase), undo.
            else:
                is_succeed: bool = False

            return is_succeed

    def remove_list_of_rb(self, ue_nb_info: Union[GNBInfo, ENBInfo], another_nb_info: Union[ENBInfo, GNBInfo]) -> bool:
        if not ue_nb_info.rb:
            return False

        # where to crop the RBs with lower MCS
        max_subarray: MaxSubarray = MaxSubarray(ue_nb_info)
        if not max_subarray.max_subarray():
            # if the MCS can not be improved
            # no cutting
            return False

        # if the MCS of the other BS is lower than the old(current) MCS of this BS, don't cut RBs.
        mcs_of_another_bs: Optional[G_MCS, E_MCS] = another_nb_info.mcs
        assert another_nb_info.rb if mcs_of_another_bs is not None else not another_nb_info.rb, "The MCS in NBInfo isn't up-to-date."
        if mcs_of_another_bs is not None and max_subarray.lower_mcs.efficiency >= mcs_of_another_bs.efficiency:
            # if (the dUE was allocated to another BS) and (the other BS has bad MCS)
            # don't cut
            return False

        max_subarray.remove_rbs()
        self.append_undo(lambda: max_subarray.undo(), lambda: max_subarray.purge_undo())
        return True

    def adjust_mcs(self):
        adjust_mcs: AdjustMCS = AdjustMCS()
        adjust_mcs.remove_worst_rb(self.ue)
        self.append_undo(lambda a_m=adjust_mcs: a_m.undo(), lambda a_m=adjust_mcs: a_m.purge_undo())
        if not self.ue.is_allocated:
            raise AssertionError
