from typing import Dict, List, Optional, Tuple, Union

from src.channel_model.sinr import ChannelModel
from src.resource_allocation.algo.new_ue import AllocateUEList
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.frame import BaseUnit, Layer
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.resource_allocation.ds.nodeb import ENBInfo, GNBInfo
from src.resource_allocation.ds.rb import ResourceBlock
from src.resource_allocation.ds.space import Space
from src.resource_allocation.ds.ue import UserEquipment
from src.resource_allocation.ds.undo import Undo
from src.resource_allocation.ds.util_enum import E_MCS, G_MCS, LTEResourceBlock, NodeBType, Numerology, UEType

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


class AllocateUEListSameNumerology(AllocateUEList):
    def __init__(self, nb: Union[GNodeB, ENodeB], ue_to_allocate: Tuple[UE], allocated_ue: Tuple[UE],
                 channel_model: ChannelModel):
        super().__init__(nb, ue_to_allocate, allocated_ue, channel_model)
        self.nb: Union[GNodeB, ENodeB] = nb
        self.ue_to_allocate: List[UE] = list(ue_to_allocate)
        self.allocated_ue: List[UE] = list(allocated_ue)  # including UEs in another BS(for co-channel area adjustment)
        self.unallocated_ue: List[UE] = []
        self.channel_model: ChannelModel = channel_model

        self.empty_spaces: List[Space] = []

    def allocate_ue_list(self, allow_lower_mcs: bool = True, allow_lower_than_cqi0: bool = True):
        while self.ue_to_allocate:
            ue: UE = self.ue_to_allocate.pop()
            tmp_numerology: Numerology = ue.numerology_in_use
            if self.nb.nb_type == NodeBType.E and ue.ue_type == UEType.D:
                ue.numerology_in_use = LTEResourceBlock.E  # TODO: refactor or redesign

            # main
            is_allocated: bool = False
            bu: RB = {'layer': 0, 'i': 0, 'j': -1}
            self.empty_spaces: List[Space] = list(self.update_empty_space())
            while bu_start := self.next_available_space(bu, ue.numerology_in_use):
                # from utils.assertion import check_undo_copy
                # copy_ue = check_undo_copy([ue] + self.allocated_ue)
                self.start_func_undo()
                is_allocated, bu = self.allocate_ue(ue, bu_start)

                if is_allocated:
                    is_allocated: bool = self.adjust_mcs_allocated_ues([ue] + self.allocated_ue,
                                                                       allow_lower_mcs, allow_lower_than_cqi0)
                self.end_func_undo()

                if is_allocated:
                    self.purge_undo()
                    break
                else:
                    self.undo()
                    # from utils.assertion import check_undo_compare
                    # check_undo_compare([ue] + self.allocated_ue, copy_ue)
            self.allocated_ue.append(ue) if is_allocated else self.unallocated_ue.append(ue)
            ue.numerology_in_use = tmp_numerology  # restore

    def allocate_ue(self, ue: UE, first_rb: RB) -> Tuple[bool, RB]:
        """
        Allocate UE to continuous RB that are either overlapped with same numerology
        or at a space that isn't used in any layer.
        :param ue: A unallocated UE.
        :param first_rb: The first RB for ue.
        :return: 1. if UE is allocated 2. The last RB the UE was allocated
        """
        assert not ue.is_allocated
        self.assert_undo_function()

        nb_info: Union[GNBInfo, ENBInfo] = ue.gnb_info if self.nb.nb_type == NodeBType.G else ue.enb_info
        bu: RB = first_rb
        layer: Layer = self.nb.frame.layer[bu['layer']]
        while True:
            # allocate a new RB
            rb: Optional[ResourceBlock] = layer.allocate_resource_block(bu['i'], bu['j'], ue)
            self.append_undo(lambda l=layer: l.undo(), lambda l=layer: l.purge_undo())
            if not rb:
                # overlapped with itself
                return False, bu

            self.channel_model.sinr_rb(rb)
            self.append_undo(lambda: self.channel_model.undo(), lambda: self.channel_model.purge_undo())
            if rb.mcs is (G_MCS if nb_info.nb_type == NodeBType.G else E_MCS).CQI0:
                # SINR out of range
                return False, bu

            # check if the allocated RBs fulfill request data rate
            if ue.calc_throughput() >= ue.request_data_rate:
                self.append_undo(lambda origin=nb_info.mcs: setattr(nb_info, 'mcs', origin))
                self.append_undo(lambda origin=ue.throughput: setattr(ue, 'throughput', origin))
                self.append_undo(lambda origin=ue.is_to_recalculate_mcs: setattr(ue, 'is_to_recalculate_mcs', origin))

                nb_info.update_mcs()
                ue.update_throughput()
                ue.is_to_recalculate_mcs = False
                return True, bu

            # next RB
            if next_rb := self.continuous_rb(bu, ue.numerology_in_use):
                bu: RB = next_rb
            else:
                return False, bu

    def continuous_rb(self, bu: RB, numerology: Union[Numerology, LTEResourceBlock]) -> Optional[RB]:
        """Check the next RB in the same layer."""
        self.assert_undo_function()
        # continuous RB
        bu['j'] += numerology.time
        if bu['j'] + numerology.time > self.nb.frame.frame_time:
            # next row
            bu['j'] = 0
            bu['i'] += numerology.freq
            if bu['i'] + numerology.freq > self.nb.frame.frame_freq:
                return None
        assert (0 <= bu['i'] + numerology.freq <= self.nb.frame.frame_freq) and (
                0 <= bu['j'] + numerology.time <= self.nb.frame.frame_time), 'RB index out of bound'

        if self.is_available_rb(bu, numerology):
            return bu
        else:
            return None

    def next_available_space(self, bu: RB, numerology: Union[Numerology, LTEResourceBlock]) -> Optional[RB]:
        next_bu: RB = bu.copy()
        if self.nb.nb_type == NodeBType.G:
            next_bu['j'] += 1
            if next_bu['j'] >= self.nb.frame.frame_time:
                next_bu['j'] = 0
                next_bu['i'] += 1
                if next_bu['i'] >= self.nb.frame.frame_freq:
                    next_bu['i'] = 0
                    next_bu['layer'] += 1
                    if next_bu['layer'] >= self.nb.frame.max_layer:
                        return None
        elif self.nb.nb_type == NodeBType.E:
            if not (next_bu := self.enb_next_rb(bu)):
                # no more spaces in the frame
                return None
        else:
            raise AssertionError
        assert (0 <= next_bu['i'] < self.nb.frame.frame_freq) and (
                0 <= next_bu['j'] < self.nb.frame.frame_time), 'BU index out of bound'

        self.empty_spaces.sort(key=lambda x: x.ending_j)
        self.empty_spaces.sort(key=lambda x: x.ending_i)
        self.empty_spaces.sort(key=lambda x: x.layer.layer_index)

        for space in self.empty_spaces:
            if (space.layer.layer_index < next_bu['layer']) or (space.layer.layer_index == next_bu['layer'] and (
                    (space.ending_i < next_bu['i']) or (
                    space.ending_i == next_bu['i'] and space.ending_j < next_bu['j']))):
                continue
            elif space.layer.layer_index == next_bu['layer']:
                for i in range(max(next_bu['i'], space.starting_i), space.ending_i + 1):
                    for j in range(space.starting_j, space.ending_j + 1):
                        if i == next_bu['i'] and j < next_bu['j']:
                            continue
                        new_bu: RB = {'layer': space.layer.layer_index, 'i': i, 'j': j}
                        if self.is_available_rb(new_bu, numerology):
                            assert new_bu != bu
                            return new_bu
            elif space.layer.layer_index > next_bu['layer']:
                # look in a whole space
                if new_bu := self.is_available_space(space, numerology):
                    assert new_bu != bu
                    return new_bu
            else:
                raise AssertionError
        return None

    def is_available_space(self, space: Space, numerology: Union[Numerology, LTEResourceBlock]) -> Optional[RB]:
        for i in range(space.starting_i, space.ending_i + 1):
            for j in range(space.starting_j, space.ending_j + 1):
                if self.is_available_rb({'layer': space.layer.layer_index, 'i': i, 'j': j}, numerology):
                    return {'layer': space.layer.layer_index, 'i': i, 'j': j}
        return None

    def is_available_rb(self, starting_bu: RB, numerology: Union[Numerology, LTEResourceBlock]) -> bool:
        assert 0 <= starting_bu['i'] < self.nb.frame.frame_freq and 0 <= starting_bu['j'] < self.nb.frame.frame_time
        if (starting_bu['i'] + numerology.freq > self.nb.frame.frame_freq) or (
                starting_bu['j'] + numerology.time > self.nb.frame.frame_time):
            # RB out of bound
            return False

        for i in range(starting_bu['i'], starting_bu['i'] + numerology.freq):
            for j in range(starting_bu['j'], starting_bu['j'] + numerology.time):
                bu: BaseUnit = self.nb.frame.layer[starting_bu['layer']].bu[i][j]
                if bu.is_used:
                    return False
                assert len(bu.lapped_numerology) <= 1, 'Only lap with same numerology.'
                if i == starting_bu['i'] and j == starting_bu['j']:
                    if not(not bu.overlapped_rb or (
                            bu.lapped_numerology[0] == numerology and bu.lapped_is_upper_left)):
                        # not (if the BU hasn't been used by any UE or is using the same numerology)
                        return False
                else:
                    if not(not bu.overlapped_rb or (
                            bu.lapped_numerology[0] == numerology and not bu.lapped_is_upper_left)):
                        return False
                assert len(set(bu.lapped_numerology + (numerology,))) <= 1, 'Only lap with same numerology.'
                assert (not bu.overlapped_ue) or (
                        len(bu.lapped_numerology) == 1), 'Should be either empty in any layer or used.'
        return True

    def enb_next_rb(self, bu: RB) -> Optional[RB]:
        assert isinstance(self.nb, ENodeB)
        assert bu['j'] % LTEResourceBlock.E.count_bu == 0

        # continuous RB
        bu['j'] += LTEResourceBlock.E.count_bu
        if bu['j'] + LTEResourceBlock.E.time > self.nb.frame.frame_time:
            # next row
            bu['j'] = 0
            bu['i'] += LTEResourceBlock.E.freq
            if bu['i'] + LTEResourceBlock.E.freq > self.nb.frame.frame_freq:
                return None
        return bu
