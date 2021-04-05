from typing import Dict, List, Optional, Tuple, Union

from src.channel_model.sinr import ChannelModel
from src.resource_allocation.algo.new_ue import AllocateUEList
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.frame import BaseUnit
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.resource_allocation.ds.space import Space
from src.resource_allocation.ds.ue import UserEquipment
from src.resource_allocation.ds.undo import Undo
from src.resource_allocation.ds.util_enum import LTEResourceBlock, NodeBType, Numerology, UEType

UE = Union[UserEquipment, GUserEquipment, EUserEquipment, DUserEquipment]
RB = Dict[str, int]  # {'layer': index, 'i': index, 'j': index}


class Msema(Undo):
    """
    UEs can only allocate to [BUs that has the same numerology as itself] or [BUs that are not used].
    At the same time, the RBs of a UE must be [continuous] but [can be in different layers].
    """

    def __init__(self, nb: Union[GNodeB, ENodeB], channel_model: ChannelModel, allocated_ue: Tuple[UE, ...]):
        super().__init__()
        self.nb: Union[GNodeB, ENodeB] = nb
        self.channel_model: ChannelModel = channel_model
        self.allocated_ue: List[UE] = list(allocated_ue)
        self.unallocated_ue: List[UE] = []

    def allocate_ue_list(self, ue_list: Tuple[UE]):
        self.unallocated_ue: List[UE] = list(ue_list)

        # lap with same numerology or unused BU in any layer
        self.sort_by_channel_quality()  # from good channel quality
        same_numerology: AllocateUEListSameNumerology = AllocateUEListSameNumerology(self.nb,
                                                                                     tuple(self.unallocated_ue),
                                                                                     tuple(self.allocated_ue),
                                                                                     self.channel_model)
        same_numerology.allocate_ue_list(allow_lower_than_cqi0=False)
        self.allocated_ue = same_numerology.allocated_ue
        self.unallocated_ue = same_numerology.unallocated_ue

        # allocate to any empty space
        self.sort_by_channel_quality()  # from good channel quality
        AllocateUEList(self.nb, tuple(self.unallocated_ue), tuple(self.allocated_ue), self.channel_model).allocate(
            allow_lower_than_cqi0=False)

    def sort_by_channel_quality(self):
        self.unallocated_ue.sort(key=lambda x: x.request_data_rate, reverse=True)
        if self.nb.nb_type == NodeBType.G:
            assert UEType.E not in [ue.ue_type for ue in self.unallocated_ue]
            self.unallocated_ue.sort(key=lambda x: x.coordinate.distance_gnb)
        elif self.nb.nb_type == NodeBType.E:
            assert UEType.G not in [ue.ue_type for ue in self.unallocated_ue]
            self.unallocated_ue.sort(key=lambda x: x.coordinate.distance_enb)
        else:
            raise AssertionError


class AllocateUEListSameNumerology(Undo):
    def __init__(self, nb: Union[GNodeB, ENodeB], ue_to_allocate: Tuple[UE], allocated_ue: Tuple[UE],
                 channel_model: ChannelModel):
        super().__init__()
        self.nb: Union[GNodeB, ENodeB] = nb
        self.ue_to_allocate: List[UE] = list(ue_to_allocate)
        self.allocated_ue: List[UE] = list(allocated_ue)  # including UEs in another BS(for co-channel area adjustment)
        self.unallocated_ue: List[UE] = []
        self.channel_model: ChannelModel = channel_model

        self.empty_spaces: List[Space] = []

    def allocate_ue_list(self, allow_lower_mcs: bool = True, allow_lower_than_cqi0: bool = True):
        while self.ue_to_allocate:
            ue: UE = self.ue_to_allocate.pop()
            # FIXME RB type暫換
            is_allocated: bool = False
            bu: RB = {'layer': 0, 'i': -1, 'j': -1}
            self.empty_spaces: List[Space] = list(AllocateUEList.update_empty_space(self.nb))
            while bu_start := self.next_available_space(bu, ue.numerology_in_use):
                # from tests.assertion import check_undo_copy
                # copy_ue = check_undo_copy([ue] + self.gue_allocated + self.due_allocated + self.eue_allocated)
                is_allocated, bu = self.allocate_ue(ue, bu_start, allow_lower_mcs, allow_lower_than_cqi0)
                if is_allocated:
                    self.purge_undo()  # FIXME
                    break
                else:
                    self.undo()
                    # from tests.assertion import check_undo_compare
                    # check_undo_compare([ue] + self.gue_allocated + self.due_allocated + self.eue_allocated, copy_ue)
                # from tests.assertion import assert_is_empty
                # assert_is_empty(spaces, ue, is_allocated)
            if is_allocated:
                self.allocated_ue.append(ue)
            else:
                self.unallocated_ue.append(ue)

    def allocate_ue(self, ue: UE, bu: RB, allow_lower_mcs: bool, allow_lower_than_cqi0: bool) -> Tuple[bool, RB]:
        # FIXME
        """
        :param ue:
        :param bu: The first RB for ue.
        :param allow_lower_mcs:
        :param allow_lower_than_cqi0:
        :return: 1. if UE is allocated 2. The last RB the UE was allocated
        """
        assert not ue.is_allocated
        return is_allocated, {layer, bu_i, bu_j}

    def allocate_resource(self):  # FIXME
        pass

    def continuous_available_rb(self, bu: RB, numerology: Union[Numerology, LTEResourceBlock]) -> Optional[RB]:  # FIXME
        # continuous RB
        bu_j += numerology.time
        if bu_j + numerology.time > self.nb.frame.frame_time:
            # next row
            bu_j = 0
            bu_i += numerology.freq
            if bu_i + numerology.freq > self.nb.frame.frame_freq:
                return None

        if self.is_available_rb(bu_i, bu_j, numerology):
            return {'i': bu_i, 'j': bu_j,
                    'layer': (self.nb.frame.max_layer - self.frame_status[bu_i][bu_j]['vacancy'])}
        else:
            return None

    def next_available_space(self, bu: RB, numerology: Union[Numerology, LTEResourceBlock]) -> Optional[RB]:
        next_bu: RB = bu
        next_bu['j'] += 1  # FIXME LTE RB
        if next_bu['j'] >= self.nb.frame.frame_time:
            next_bu['j'] = 0
            next_bu['i'] += 1
            if next_bu['i'] >= self.nb.frame.frame_freq:
                next_bu['i'] = 0
                next_bu['layer'] += 1
                if next_bu['layer'] >= self.nb.frame.max_layer:
                    return None

        self.empty_spaces.sort(key=lambda x: x.ending_j)
        self.empty_spaces.sort(key=lambda x: x.ending_i)
        self.empty_spaces.sort(key=lambda x: x.layer.layer_index)

        for space in self.empty_spaces:
            if (space.layer.layer_index < next_bu['layer']) or (space.layer.layer_index == next_bu['layer'] and (
                    (space.ending_i < next_bu['i']) or (
                    space.ending_i == next_bu['i'] and space.ending_j < next_bu['j']))):
                continue
            elif space.layer.layer_index == next_bu['layer'] and (
                    space.starting_i <= next_bu['i'] <= space.ending_i) and (
                    space.starting_j <= next_bu['j'] <= space.ending_j):
                # next_bu in the space
                for i in range(next_bu['i'], space.ending_i + 1):
                    for j in range(space.starting_j, space.ending_j + 1):
                        if i == next_bu['i'] and j < next_bu['j']:
                            continue
                        if self.is_available_rb({'layer': space.layer.layer_index, 'i': i, 'j': j}, numerology):
                            return {'layer': space.layer.layer_index, 'i': i, 'j': j}
            else:
                # look in a whole space
                if bu := self.is_available_space(space, numerology):
                    return bu
        return None

    def is_available_space(self, space: Space, numerology: Union[Numerology, LTEResourceBlock]) -> Optional[RB]:
        for i in range(space.starting_i, space.ending_i + 1):
            for j in range(space.starting_j, space.ending_j + 1):
                if self.is_available_rb({'layer': space.layer.layer_index, 'i': i, 'j': j}, numerology):
                    return {'layer': space.layer.layer_index, 'i': i, 'j': j}
        return None

    def is_available_rb(self, starting_bu: RB, numerology: Union[Numerology, LTEResourceBlock]) -> bool:
        assert (starting_bu['i'] + numerology.freq <= self.nb.frame.frame_freq) and (
                starting_bu['j'] + numerology.time <= self.nb.frame.frame_time), 'RB out of bound.'

        for i in range(starting_bu['i'], starting_bu['i'] + numerology.freq):
            for j in range(starting_bu['j'], starting_bu['j'] + numerology.time):
                bu: BaseUnit = self.nb.frame.layer[starting_bu['layer']].bu[i][j]
                assert bu.within_rb is None
                if i == starting_bu['i'] and j == starting_bu['j']:
                    if not bu.overlapped_ue or (bu.numerology == numerology and bu.is_upper_left):
                        # if the BU hasn't been used by any UE or is using the same numerology
                        assert not bu.overlapped_rb or (
                                bu.overlapped_ue and bu.numerology), 'Should be either empty in any layer or used.'
                        continue
                    else:
                        return False
                else:
                    if not bu.overlapped_ue or (bu.numerology == numerology and not bu.is_upper_left):
                        assert not bu.overlapped_rb or (
                                bu.overlapped_ue and bu.numerology), 'Should be either empty in any layer or used.'
                        continue
                    else:
                        return False
        return True
