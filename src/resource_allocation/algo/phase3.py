import pickle
from typing import Dict, List, Optional, Tuple, Union

from hungarian_algorithm import algorithm

from src.channel_model.adjust_mcs import AdjustMCS
from src.channel_model.sinr import ChannelModel
from src.resource_allocation.ds.eutran import ENodeB
from src.resource_allocation.ds.ngran import GNodeB
from src.resource_allocation.ds.rb import ResourceBlock
from src.resource_allocation.ds.space import empty_space, Space
from src.resource_allocation.ds.ue import UserEquipment
from src.resource_allocation.ds.util_enum import E_MCS, G_MCS, NodeBType, UEType


class Phase3:
    def __init__(self, channel_model: ChannelModel, gnb: GNodeB, enb: ENodeB,
                 ue_list_allocated: Tuple[Tuple[UserEquipment, ...], ...],
                 ue_list_unallocated: Tuple[Tuple[UserEquipment, ...], ...]):
        self.file_path: str = "store.P"
        self.channel_model: ChannelModel = channel_model
        self.gnb: GNodeB = gnb
        self.enb: ENodeB = enb
        self.gue_allocated: List[UserEquipment] = list(ue_list_allocated[0])
        self.gue_unallocated: List[UserEquipment] = list(ue_list_unallocated[0])
        self.due_allocated: List[UserEquipment] = list(ue_list_allocated[1])
        self.due_unallocated: List[UserEquipment] = list(ue_list_unallocated[1])
        self.eue_allocated: List[UserEquipment] = list(ue_list_allocated[2])
        self.eue_unallocated: List[UserEquipment] = list(ue_list_unallocated[2])

        self.mcs_ordered: Tuple[Union[E_MCS, G_MCS], ...] = self.order_mcs()

        self.adjust_mcs = AdjustMCS(self.channel_model, self.gue_allocated, self.gue_unallocated, self.due_allocated,
                                    self.due_unallocated, self.eue_allocated, self.eue_unallocated)

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
            # graph: Dict[str, Dict[str, float]] = self.calc_weight(mcs, ue_list, gnb_empty_space, enb_empty_space)

            # Bipartite matching
            # match: List[Tuple[Tuple[str, str], float]] = self.matching(graph)

            # Implement the matching result from the highest weight.
            # If a movement lowers down the MCS of any allocated UE, dispose it and move on to the next match.

    def calc_weight(self, mcs: Union[E_MCS, G_MCS], ue_list: List[UserEquipment], gnb_spaces: Tuple[Space, ...],
                    enb_spaces: Tuple[Space, ...]) -> Dict[str, Dict[str, float]]:
        self.store()

        weight: Dict[str, Dict[str, float]] = {}
        num_of_bu_origin: int = self.calc_num_bu(self.gue_allocated + self.due_allocated + self.eue_allocated)
        for ue in ue_list:
            weight[str(ue.uuid)] = {}
            for space in gnb_spaces + enb_spaces:
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
                        num_of_bu_new: int = self.calc_num_bu(
                            self.gue_allocated + self.due_allocated + self.eue_allocated)
                        weight[str(ue.uuid)][str(space.uuid)] = num_of_bu_origin - num_of_bu_new
                        assert weight[str(ue.uuid)][str(space.uuid)] >= 0, "There are UE getting lower mcs than before."
                    self.restore(space)
        return weight

    def allocated_ue_to_space(self, ue: UserEquipment, space: Space, mcs: Union[E_MCS, G_MCS]) -> bool:
        # the space can place at least one RB of the size(numerology/LTE) the UE is using
        bu_i: int = space.starting_i
        bu_j: int = space.starting_j
        while True:
            rb: Optional[ResourceBlock] = space.layer.allocate_resource_block(bu_i, bu_j, ue)
            if not rb:
                # UE overlapped with itself
                # the coordination of next RB
                if bu := space.next_rb(bu_i, bu_j, ue.numerology_in_use):
                    bu_i: int = bu[0]
                    bu_j: int = bu[1]
                    continue
                else:
                    # running out of space
                    return False

            self.channel_model.sinr_rb(rb)
            if (ue.gnb_info if isinstance(rb.mcs, G_MCS) else ue.enb_info).mcs and (
                    rb.mcs.efficiency < (ue.gnb_info if isinstance(rb.mcs, G_MCS) else ue.enb_info).mcs.efficiency):
                # if ('ue' is allocated to the type of BS the 'rb' is allocated)
                #    and (the mcs of new RB is lower than the mcs the UE is currently using)
                rb.remove()
                # the coordination of next RB
                if bu := space.next_rb(bu_i, bu_j, ue.numerology_in_use):
                    bu_i: int = bu[0]
                    bu_j: int = bu[1]
                    continue
                else:
                    # running out of space
                    return False

            self.adjust_mcs.adjust(ue)
            if (isinstance(mcs, G_MCS) and ue.gnb_info.rb and ue.gnb_info.rb[-1].mcs.efficiency > mcs.efficiency) or (
                    isinstance(mcs, E_MCS) and ue.enb_info.rb and ue.enb_info.rb[-1].mcs.efficiency > mcs.efficiency) \
                    or (isinstance(mcs, G_MCS) and not ue.gnb_info.rb) \
                    or (isinstance(mcs, E_MCS) and not ue.enb_info.rb):
                # The bad RBs, using the mcs, are all replaced by the new RBs in the empty space
                return self.effected_ue()

            # the coordination of next RB
            if bu := space.next_rb(bu_i, bu_j, ue.numerology_in_use):
                bu_i: int = bu[0]
                bu_j: int = bu[1]
            else:
                # running out of space
                return False

    def effected_ue(self) -> bool:
        while True:
            is_all_adjusted: bool = True
            for ue in self.gue_allocated + self.due_allocated + self.eue_allocated:
                if ue.is_to_recalculate_mcs:
                    is_all_adjusted: bool = False
                    self.channel_model.sinr_ue(ue)
                    if not self.adjust_mcs.adjust(ue, allow_lower_mcs=False):
                        # the ue moving to the space lower down a original UEs' MCS
                        return False
            if is_all_adjusted:
                # the space is suitable for this ue
                return True

    def new_ue_to_space(self):
        pass

    @staticmethod
    def matching(graph: Dict[str, Dict[str, float]]) -> List[Tuple[Tuple[str, str], float]]:
        # TODO: graph用list傳入。把UE跟space依照weight由大到小排序
        # for ue in graph.keys():
        #     graph[ue]: Dict[str, float] = OrderedDict(sorted(graph[ue].items(), key=lambda x: x[1], reverse=True))
        # graph: Dict[str, Dict[str, float]] = OrderedDict(sorted(graph.items(), key=lambda x: x[1][0][1], reverse=True))

        if len(graph) <= 1:
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
        else:
            """
            Hungarian Algorithm: https://github.com/benchaplin/hungarian-algorithm
            Constraint in directed graph:
                1. The starting vertexes must be more than one.
                2. The starting vertexes and ending vertexes should not be the same.
            Tip:
                1. Do not input too many edges. Ignore the edge <= 0.
            """
            output: List[Tuple[Tuple[str, str], float]] = algorithm.find_matching(graph)
            if not output:  # return False
                raise ValueError
        return output

    @staticmethod
    def calc_num_bu(ue_list: List[UserEquipment]) -> int:
        # for weight
        num_of_bu: int = 0
        for ue in ue_list:
            if hasattr(ue, 'gnb_info'):
                num_of_bu += len(ue.gnb_info.rb) * 16
            if hasattr(ue, 'enb_info'):
                num_of_bu += len(ue.enb_info.rb) * 8
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

    def store(self):
        with open(self.file_path, "wb") as file:
            pickle.dump([self.gnb, self.enb,
                         self.gue_allocated, self.gue_unallocated,
                         self.due_allocated, self.due_unallocated,
                         self.eue_allocated, self.eue_unallocated],
                        file)

    def restore(self, space: Optional[Space] = None):
        """不能用deep copy，例如：nb.frame.layer.bu沒有複製到"""
        with open(self.file_path, "rb") as file_of_nb_and_ue:
            self.gnb, self.enb, self.gue_allocated, self.gue_unallocated, self.due_allocated, self.due_unallocated, self.eue_allocated, self.eue_unallocated = pickle.load(
                file_of_nb_and_ue)

        if space:
            space_layer_index: int = space.layer.layer_index
            space_nb_type: NodeBType = space.layer.nodeb.nb_type
            space.layer = (self.gnb if space_nb_type == NodeBType.G else self.enb).frame.layer[space_layer_index]
