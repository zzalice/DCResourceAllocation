from typing import List, Optional, Tuple, Union

from src.channel_model.adjust_mcs import AdjustMCS
from src.channel_model.sinr import ChannelModel
from src.resource_allocation.algo.new_resource_allocation import AllocateUE
from src.resource_allocation.algo.util_type import RBIndex
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.frame import BaseUnit, Layer
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.resource_allocation.ds.nodeb import ENBInfo, GNBInfo
from src.resource_allocation.ds.rb import ResourceBlock
from src.resource_allocation.ds.space import empty_space, next_rb_in_space, Space
from src.resource_allocation.ds.ue import UserEquipment
from src.resource_allocation.ds.undo import Undo
from src.resource_allocation.ds.util_enum import E_MCS, G_MCS, LTEResourceBlock, NodeBType, Numerology, UEType

UE = Union[UserEquipment, GUserEquipment, EUserEquipment, DUserEquipment]


class AllocateUEList(Undo):
    def __init__(self, nb: Union[GNodeB, ENodeB], ue_to_allocate: Tuple[UE], allocated_ue: Tuple[UE],
                 channel_model: ChannelModel):
        super().__init__()
        self.nb: Union[GNodeB, ENodeB] = nb
        self.ue_to_allocate: List[UE] = list(ue_to_allocate)
        self.allocated_ue: List[UE] = list(allocated_ue)  # including UEs in another BS(for co-channel area adjustment)
        self.channel_model: ChannelModel = channel_model

    def allocate(self, allow_lower_mcs: bool = True, allow_lower_than_cqi0: bool = True):
        spaces: Tuple[Space] = self.update_empty_space(nb=self.nb)
        while self.ue_to_allocate:
            ue: UE = self.ue_to_allocate.pop()
            # assert not ue.is_allocated    # TODO: refactor, for MCUP combine RA algorithms
            for space in spaces:
                # from tests.assertion import check_undo_copy
                # copy_ue = check_undo_copy([ue] + self.gue_allocated + self.due_allocated + self.eue_allocated)
                is_allocated: bool = self._allocate(ue, (space,), allow_lower_mcs, allow_lower_than_cqi0)
                if is_allocated:
                    self.allocated_ue.append(ue)
                    spaces: Tuple[Space] = self.update_empty_space(nb=self.nb)
                    self.purge_undo()
                    break
                else:
                    self.undo()
                    # from tests.assertion import check_undo_compare
                    # check_undo_compare([ue] + self.gue_allocated + self.due_allocated + self.eue_allocated, copy_ue)
                # from tests.assertion import assert_is_empty
                # assert_is_empty(spaces, ue, is_allocated)

    @Undo.undo_func_decorator
    def _allocate(self, ue, spaces: Tuple[Space, ...], allow_lower_mcs, allow_lower_than_cqi0) -> bool:
        # allocate new ue
        allocate_ue: AllocateUE = AllocateUE(ue, spaces, self.channel_model)
        is_allocated: bool = allocate_ue.allocate()
        self.append_undo(lambda a_u=allocate_ue: a_u.undo(), lambda a_u=allocate_ue: a_u.purge_undo())

        # the effected UEs
        if is_allocated:
            has_positive_effect: bool = self.adjust_mcs_allocated_ues([ue] + self.allocated_ue,
                                                                      allow_lower_mcs, allow_lower_than_cqi0)
            if not has_positive_effect:
                is_allocated: bool = False
        return is_allocated

    @staticmethod
    def update_empty_space(nb: Union[GNodeB, ENodeB]) -> Tuple[Space]:
        tmp_spaces: List[Space] = []
        for layer in nb.frame.layer:
            new_spaces: Tuple[Space] = empty_space(layer)
            tmp_spaces.extend(new_spaces)

            # break if there is a complete layer in tmp_space
            if len(new_spaces) == 1 and (
                    new_spaces[0].width == nb.frame.frame_time and new_spaces[0].height == nb.frame.frame_freq):
                break

        return tuple(tmp_spaces)

    def adjust_mcs_allocated_ues(self, allocated_ue: List[UE], allow_lower_mcs, allow_lower_than_cqi0) -> bool:
        self.assert_undo_function()
        self.assert_allow_lower(allow_lower_mcs, allow_lower_than_cqi0)
        while True:
            is_all_adjusted: bool = True
            for ue in allocated_ue:
                if ue.is_to_recalculate_mcs:
                    is_all_adjusted: bool = False
                    self.channel_model.sinr_ue(ue)
                    self.append_undo(lambda: self.channel_model.undo(), lambda: self.channel_model.purge_undo())

                    has_positive_effect: bool = self.adjust_mcs(ue, allow_lower_mcs, allow_lower_than_cqi0)

                    if not has_positive_effect:
                        # the mcs of the ue is lowered down by another UE.
                        return False
            if is_all_adjusted:
                return True

    def adjust_mcs(self, ue: UE, allow_lower_mcs: bool, allow_lower_than_cqi0: bool) -> bool:
        self.assert_undo_function()
        adjust_mcs: AdjustMCS = AdjustMCS()
        if not allow_lower_mcs:
            has_positive_effect: bool = adjust_mcs.remove_worst_rb(ue, allow_lower_mcs=False)
        elif not allow_lower_than_cqi0:
            has_positive_effect: bool = adjust_mcs.remove_worst_rb(ue, allow_lower_than_cqi0=False,
                                                                   channel_model=self.channel_model)
        else:
            has_positive_effect: bool = adjust_mcs.remove_worst_rb(ue)  # ue can be removed
        self.append_undo(lambda a_m=adjust_mcs: a_m.undo(), lambda a_m=adjust_mcs: a_m.purge_undo())
        return has_positive_effect

    @staticmethod
    def assert_allow_lower(allow_lower_mcs, allow_lower_than_cqi0):
        if allow_lower_than_cqi0 is False:
            assert allow_lower_mcs is True
        else:
            pass


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

    def allocate_ue_list(self, allow_lower_mcs: bool = True, allow_lower_than_cqi0: bool = False):
        while self.ue_to_allocate:
            ue: UE = self.ue_to_allocate.pop()
            tmp_numerology: Numerology = ue.numerology_in_use
            if self.nb.nb_type == NodeBType.E and ue.ue_type == UEType.D:
                ue.numerology_in_use = LTEResourceBlock.E  # TODO: refactor or redesign

            # main
            is_allocated: bool = False
            bu: RBIndex = RBIndex(layer=0, i=0, j=-1)
            self.empty_spaces: List[Space] = list(self.update_empty_space(self.nb))
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

    def allocate_ue(self, ue: UE, first_rb: RBIndex) -> Tuple[bool, RBIndex]:
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
        bu: RBIndex = first_rb
        layer: Layer = self.nb.frame.layer[bu.layer]
        while True:
            # allocate a new RB
            rb: Optional[ResourceBlock] = layer.allocate_resource_block(bu.i, bu.j, ue)
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
                bu: RBIndex = next_rb
            else:
                return False, bu

    def continuous_rb(self, bu: RBIndex, numerology: Union[Numerology, LTEResourceBlock]) -> Optional[RBIndex]:
        """Check the next RB in the same layer."""
        self.assert_undo_function()
        # continuous RB
        bu.j += numerology.time
        if bu.j + numerology.time > self.nb.frame.frame_time:
            # next row
            bu.j = 0
            bu.i += numerology.freq
            if bu.i + numerology.freq > self.nb.frame.frame_freq:
                return None
        assert (0 <= bu.i + numerology.freq <= self.nb.frame.frame_freq) and (
                0 <= bu.j + numerology.time <= self.nb.frame.frame_time), 'RB index out of bound'

        if self.is_available_rb(bu, numerology, self.nb):
            return bu
        else:
            return None

    def adjust_mcs(self, ue: UE, allow_lower_mcs: bool, allow_lower_than_cqi0: bool) -> bool:
        adjust_mcs: AdjustMCS = AdjustMCS()
        if self.nb.nb_type == NodeBType.G:
            has_positive_effect: bool = adjust_mcs.remove_from_tail(ue, allow_lower_mcs=allow_lower_mcs,
                                                                    allow_lower_than_cqi0=allow_lower_than_cqi0,
                                                                    channel_model=self.channel_model,
                                                                    new_same_numerology_rb=True,
                                                                    func_is_available_rb=self.is_available_rb)
        elif self.nb.nb_type == NodeBType.E:
            has_positive_effect: bool = adjust_mcs.remove_from_tail(ue, allow_lower_mcs=allow_lower_mcs,
                                                                    allow_lower_than_cqi0=allow_lower_than_cqi0,
                                                                    channel_model=self.channel_model)
        else:
            raise AssertionError

        self.append_undo(lambda a_m=adjust_mcs: a_m.undo(), lambda a_m=adjust_mcs: a_m.purge_undo())
        return has_positive_effect

    def next_available_space(self, bu: RBIndex, numerology: Union[Numerology, LTEResourceBlock]) -> Optional[RBIndex]:
        if self.nb.nb_type == NodeBType.G:
            return self.next_space_gnb(bu, numerology)
        elif self.nb.nb_type == NodeBType.E:
            return self.next_space_enb(bu)
        else:
            raise AssertionError

    def next_space_gnb(self, bu: RBIndex, numerology: Numerology) -> Optional[RBIndex]:
        next_bu: RBIndex = RBIndex(layer=bu.layer, i=bu.i, j=bu.j)
        next_bu.j += 1
        if next_bu.j >= self.nb.frame.frame_time:
            next_bu.j = 0
            next_bu.i += 1
            if next_bu.i >= self.nb.frame.frame_freq:
                next_bu.i = 0
                next_bu.layer += 1
                if next_bu.layer >= self.nb.frame.max_layer:
                    return None
        assert (0 <= next_bu.i < self.nb.frame.frame_freq) and (
                0 <= next_bu.j < self.nb.frame.frame_time), 'BU index out of bound'

        self.empty_spaces.sort(key=lambda x: x.ending_j)
        self.empty_spaces.sort(key=lambda x: x.ending_i)
        self.empty_spaces.sort(key=lambda x: x.layer.layer_index)

        for space in self.empty_spaces:
            if (space.layer.layer_index < next_bu.layer) or (space.layer.layer_index == next_bu.layer and (
                    (space.ending_i < next_bu.i) or (
                    space.ending_i == next_bu.i and space.ending_j < next_bu.j))):
                continue
            elif space.layer.layer_index == next_bu.layer:
                if space.ending_i >= next_bu.i:
                    for i in range(max(next_bu.i, space.starting_i), space.ending_i + 1):
                        for j in range(space.starting_j, space.ending_j + 1):
                            if i == next_bu.i and j < next_bu.j:
                                continue
                            new_bu: RBIndex = RBIndex(layer=space.layer.layer_index, i=i, j=j)
                            if self.is_available_rb(new_bu, numerology, self.nb):
                                assert new_bu != bu
                                return new_bu
            elif space.layer.layer_index > next_bu.layer:
                # look in a whole space
                if new_bu := self.is_available_space(space, numerology):
                    assert new_bu != bu
                    return new_bu
            else:
                raise AssertionError
        return None

    def is_available_space(self, space: Space, numerology: Union[Numerology, LTEResourceBlock]) -> Optional[RBIndex]:
        for i in range(space.starting_i, space.ending_i + 1):
            for j in range(space.starting_j, space.ending_j + 1):
                if self.is_available_rb(RBIndex(layer=space.layer.layer_index, i=i, j=j), numerology, self.nb):
                    return RBIndex(layer=space.layer.layer_index, i=i, j=j)
        return None

    def next_space_enb(self, bu: RBIndex) -> Optional[RBIndex]:
        # doesn't need to check if it's overlapped with same RB type.
        assert self.nb.nb_type == NodeBType.E and bu.layer == 0
        if not (next_bu := self.next_rb_enb(bu)):
            # no more spaces in the frame
            return None
        else:
            new_bu: Optional[RBIndex] = None
            for space in self.empty_spaces:
                # find the space includes next_bu or after next_bu
                if space.starting_i <= next_bu.i <= space.ending_i and space.starting_j <= next_bu.j <= space.ending_j:
                    # includes next_bu
                    new_bu: RBIndex = next_bu
                    break
                elif space.starting_i <= next_bu.i <= space.ending_i and space.starting_j > next_bu.j:
                    # same row after next_bu
                    new_bu: RBIndex = RBIndex(layer=next_bu.layer, i=next_bu.i, j=space.starting_j)
                    break
                elif space.starting_i > next_bu.i:
                    # after next_bu
                    new_bu: RBIndex = RBIndex(layer=space.layer.layer_index, i=space.starting_i, j=space.starting_j)
                    break
            if new_bu is not None:
                assert new_bu.i != bu.i or new_bu.j != bu.j, "The next RB shouldn't be the same."
                assert (0 <= new_bu.i < self.nb.frame.frame_freq) and (
                        0 <= new_bu.j < self.nb.frame.frame_time), 'RB index out of bound.'
                assert new_bu.j % LTEResourceBlock.E.count_bu == 0, 'LTE RB not aligned.'
            return new_bu

    def next_rb_enb(self, bu: RBIndex) -> Optional[RBIndex]:
        assert self.nb.nb_type == NodeBType.E
        if bu.j == -1 and bu.i == 0 and bu.layer == 0:
            return RBIndex(layer=0, i=0, j=0)
        else:
            # continuous RB
            if bu_idx := next_rb_in_space(bu.i, bu.j, LTEResourceBlock.E, self.nb.frame.layer[bu.layer],
                                          0, 0, self.nb.frame.frame_freq - 1, self.nb.frame.frame_time - 1):
                assert bu_idx != bu, "RB index shouldn't be the same."
                assert (0 <= bu_idx[0] < self.nb.frame.frame_freq) and (
                        0 <= bu_idx[1] < self.nb.frame.frame_time), 'RB index out of bound.'
                assert bu_idx[1] % LTEResourceBlock.E.count_bu == 0, 'LTE RB not aligned.'
                return RBIndex(layer=bu.layer, i=bu_idx[0], j=bu_idx[1])
            else:
                return None

    @staticmethod
    def is_available_rb(starting_bu: RBIndex, numerology: Union[Numerology, LTEResourceBlock],
                        nb: Union[GNodeB, ENodeB]) -> bool:
        assert 0 <= starting_bu.i < nb.frame.frame_freq and 0 <= starting_bu.j < nb.frame.frame_time
        if (starting_bu.i + numerology.freq > nb.frame.frame_freq) or (
                starting_bu.j + numerology.time > nb.frame.frame_time):
            # RB out of bound
            return False

        for i in range(starting_bu.i, starting_bu.i + numerology.freq):
            for j in range(starting_bu.j, starting_bu.j + numerology.time):
                bu: BaseUnit = nb.frame.layer[starting_bu.layer].bu[i][j]
                if bu.is_used:
                    return False
                assert len(bu.lapped_numerology) <= 1, 'Only lap with same numerology.'
                if i == starting_bu.i and j == starting_bu.j:
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
