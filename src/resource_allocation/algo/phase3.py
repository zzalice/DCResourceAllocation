from typing import Dict, List, Optional, Tuple, Union

from src.channel_model.adjust_mcs import AdjustMCS
from src.channel_model.sinr import ChannelModel
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.resource_allocation.ds.nodeb import ENBInfo, GNBInfo
from src.resource_allocation.ds.rb import ResourceBlock
from src.resource_allocation.ds.space import empty_space, Space
from src.resource_allocation.ds.ue import UserEquipment
from src.resource_allocation.ds.undo import Undo
from src.resource_allocation.ds.util_enum import E_MCS, G_MCS, NodeBType, UEType


class Phase3(Undo):
    def __init__(self, channel_model: ChannelModel, gnb: GNodeB, enb: ENodeB,
                 ue_list_allocated: Tuple[
                     Tuple[GUserEquipment, ...], Tuple[DUserEquipment, ...], Tuple[EUserEquipment, ...]],
                 ue_list_unallocated: Tuple[
                     Tuple[GUserEquipment, ...], Tuple[DUserEquipment, ...], Tuple[EUserEquipment, ...]]):
        super().__init__()
        self.channel_model: ChannelModel = channel_model
        self.gnb: GNodeB = gnb
        self.enb: ENodeB = enb
        self.gue_allocated: List[GUserEquipment] = list(ue_list_allocated[0])
        self.gue_unallocated: List[GUserEquipment] = list(ue_list_unallocated[0])
        self.due_allocated: List[DUserEquipment] = list(ue_list_allocated[1])
        self.due_unallocated: List[DUserEquipment] = list(ue_list_unallocated[1])
        self.eue_allocated: List[EUserEquipment] = list(ue_list_allocated[2])
        self.eue_unallocated: List[EUserEquipment] = list(ue_list_unallocated[2])
        self.adjust_mcs = AdjustMCS(self.channel_model, self.gue_allocated, self.gue_unallocated, self.due_allocated,
                                    self.due_unallocated, self.eue_allocated, self.eue_unallocated)

        self.mcs_ordered: Tuple[Union[E_MCS, G_MCS], ...] = self.order_mcs()

    def increase_resource_efficiency(self):
        self.adjust_mcs.adjust_mcs_allocated_ues()

        for mcs in self.mcs_ordered:
            # Find the UEs using this mcs
            ue_list: List[UserEquipment] = []
            if isinstance(mcs, E_MCS):
                for ue in self.due_allocated + self.eue_allocated:
                    if ue.enb_info.mcs is mcs:
                        ue_list.append(ue)
            elif isinstance(mcs, G_MCS):
                for ue in self.due_allocated + self.gue_allocated:
                    if ue.gnb_info.mcs is mcs:
                        ue_list.append(ue)
            if not ue_list:
                continue

            # Find empty spaces
            gnb_empty_space: List[Space] = []
            for layer in self.gnb.frame.layer:
                gnb_empty_space.extend(empty_space(layer))
            gnb_empty_space: Tuple[Space, ...] = tuple(gnb_empty_space)
            enb_empty_space: Tuple[Space, ...] = empty_space(self.enb.frame.layer[0])

            # Calculate the weight of ue to space
            graph: Dict[str, Dict[str, float]] = self.calc_weight(mcs, ue_list, gnb_empty_space, enb_empty_space)

            # Bipartite matching
            # match: List[Tuple[Tuple[str, str], float]] = self.matching(graph)

            # Implement the matching result from the highest weight.
            # If a movement lowers down the MCS of any allocated UE, dispose it and move on to the next match.

    def calc_weight(self, mcs: Union[E_MCS, G_MCS], ue_list: List[UserEquipment], gnb_spaces: Tuple[Space, ...],
                    enb_spaces: Tuple[Space, ...]) -> Dict[str, Dict[str, float]]:
        weight: Dict[str, Dict[str, float]] = {}
        num_of_bu_origin: int = self.num_of_bu_in_all_nb
        for ue in ue_list:
            weight[str(ue.uuid)] = {}
            for space in gnb_spaces + enb_spaces:
                assert len(self._undo_stack) == 0, "Undo stack was not cleared."
                assert len(self._purge_stack) == 0, "Purge stack was not cleared."
                is_to_try: bool = False
                if space.layer.nodeb.nb_type == NodeBType.G and (ue.ue_type == UEType.G or ue.ue_type == UEType.D):
                    for numerology in space.rb_type:
                        if ue.numerology_in_use is numerology:
                            # the size of the space is large enough for at least one RB of the numerology in use
                            is_to_try: bool = True
                            break
                        else:
                            continue
                elif space.layer.nodeb.nb_type == NodeBType.E and (ue.ue_type == UEType.E or ue.ue_type == UEType.D):
                    is_to_try: bool = True

                if is_to_try:
                    is_usable: bool = self.allocated_ue_to_space(ue, space, mcs)
                    if is_usable:
                        weight[str(ue.uuid)][str(space.uuid)] = num_of_bu_origin - self.num_of_bu_in_all_nb
                        assert weight[str(ue.uuid)][str(space.uuid)] >= 0, "There are UE getting lower mcs than before."
                    self.undo()
                space.assert_is_empty()
        return weight

    def allocated_ue_to_space(self, ue: UserEquipment, space: Space, mcs: Union[E_MCS, G_MCS]) -> bool:
        # the space can place at least one RB of the size(numerology/LTE) the UE is using
        bu_i: int = -1
        bu_j: int = -1
        while True:
            if bu_i == -1 or bu_j == -1:
                bu_i: int = space.starting_i
                bu_j: int = space.starting_j
            elif bu := space.next_rb(bu_i, bu_j, ue.numerology_in_use):
                # the coordination of next RB
                bu_i: int = bu[0]
                bu_j: int = bu[1]
            else:
                # running out of space
                return False

            rb: Optional[ResourceBlock] = space.layer.allocate_resource_block(bu_i, bu_j, ue)
            if not rb:
                # UE overlapped with itself
                continue
            self.append_undo([lambda l=space.layer: l.undo(), lambda l=space.layer: l.purge_undo()])

            self.channel_model.sinr_rb(rb)
            if rb.mcs.efficiency < mcs.efficiency:
                # TODO: undo的last move. rb.undo(-1)
                return False

            self.adjust_mcs.adjust(ue)
            self.append_undo([lambda a_m=self.adjust_mcs: a_m.undo(), lambda a_m=self.adjust_mcs: a_m.purge_undo()])
            nb_info: Union[GNBInfo, ENBInfo] = ue.gnb_info if isinstance(mcs, G_MCS) else ue.enb_info
            if not nb_info.rb or nb_info.rb[-1].mcs.efficiency > mcs.efficiency:
                # The bad RBs, using the mcs, are all replaced by the new RBs in the empty space
                # the ue must had RB of mcs or else it would not be calling calc_weight().
                has_positive_effect: bool = self.adjust_mcs.adjust_mcs_allocated_ues(allow_lower_mcs=False)
                self.append_undo([lambda a_m=self.adjust_mcs: a_m.undo(), lambda a_m=self.adjust_mcs: a_m.purge_undo()])
                return has_positive_effect

    def new_ue_to_space(self):
        pass

    @staticmethod
    def matching(graph: Dict[str, Dict[str, float]]) -> List[Tuple[Tuple[str, str], float]]:
        # TODO: graph用list傳入。把UE跟space依照weight由大到小排序
        # for ue in graph.keys():
        #     graph[ue]: Dict[str, float] = OrderedDict(sorted(graph[ue].items(), key=lambda x: x[1], reverse=True))
        # graph: Dict[str, Dict[str, float]] = OrderedDict(sorted(graph.items(), key=lambda x: x[1][0][1], reverse=True))

        # greedy
        max_weight: float = -1
        max_weight_space: str = ''
        output: List[Tuple[Tuple[str, str], float]] = []
        for ue in graph:
            for space in graph[ue]:
                if graph[ue][space] > max_weight:
                    max_weight: float = graph[ue][space]
                    max_weight_space: str = space
            output: List[Tuple[Tuple[str, str], float]] = [((ue, max_weight_space), max_weight)]
        return output

    @property
    def num_of_bu_in_all_nb(self) -> int:
        """ Calculate the total number of BU occupied in both NodeBs. """
        num_of_bu: int = 0
        for nb in [self.gnb, self.enb]:
            for layer in nb.frame.layer:
                for bu_i in range(nb.frame.frame_freq):
                    for bu_j in range(nb.frame.frame_time):
                        num_of_bu += 1 if layer.bu_status[bu_i][bu_j] else 0
        return num_of_bu

    @staticmethod
    def order_mcs() -> Tuple[Union[E_MCS, G_MCS], ...]:
        mcs_list: List[List[Union[E_MCS, G_MCS], float]] = []
        for mcs in E_MCS:
            mcs_list.append([mcs, mcs.efficiency])
        for mcs in G_MCS:
            mcs_list.append([mcs, mcs.efficiency])
        mcs_list.sort(key=lambda x: x[1])

        ordered_mcs: List[Union[E_MCS, G_MCS]] = []
        for mcs in mcs_list:
            ordered_mcs.append(mcs[0])
        return tuple(ordered_mcs)
