from typing import List, Optional, Set, Tuple, Union

from src.channel_model.sinr import ChannelModel
from src.resource_allocation.algo.new_single_ue import AllocateUE, DCProportionAllocate
from src.resource_allocation.algo.new_ue_list import AllocateUEList
from src.resource_allocation.algo.utils import sort_by_channel_quality
from src.resource_allocation.ds.eutran import ENodeB, EUserEquipment
from src.resource_allocation.ds.frame import BaseUnit
from src.resource_allocation.ds.ngran import DUserEquipment, GNodeB, GUserEquipment
from src.resource_allocation.ds.rb import ResourceBlock
from src.resource_allocation.ds.space import empty_space, Space
from src.resource_allocation.ds.ue import UserEquipment
from src.resource_allocation.ds.util_enum import LTEResourceBlock, NodeBType, Numerology, UEType

UE = Union[UserEquipment, GUserEquipment, DUserEquipment, EUserEquipment]


class Intuitive(AllocateUEList):
    def __init__(self, nb: Union[GNodeB, ENodeB], another_nb: Union[GNodeB, ENodeB],
                 ue_to_allocate: Tuple[UE, ...], allocated_ue: Tuple[UE, ...],
                 channel_model: ChannelModel):
        super().__init__(nb, (), allocated_ue, channel_model)
        self.ue_to_allocate: List[UE] = sort_by_channel_quality(list(ue_to_allocate), nb.nb_type)
        assert nb.nb_type != another_nb.nb_type, 'Input two same-type-BS.'
        self.another_nb: Union[GNodeB, ENodeB] = another_nb

    def allocate(self, allow_lower_mcs: bool = True, allow_lower_than_cqi0: bool = True):
        while self.ue_to_allocate:
            ue: UE = self.ue_to_allocate.pop(0)
            # from tests.assertion import check_undo_copy   FIXME
            # copy_ue = check_undo_copy([ue] + self.gue_allocated + self.due_allocated + self.eue_allocated)
            is_allocated: bool = self._allocate(ue, (), allow_lower_mcs, allow_lower_than_cqi0)
            if is_allocated:
                self.allocated_ue.append(ue)
                self.purge_undo()
            else:
                self.undo()
                # from tests.assertion import check_undo_compare
                # check_undo_compare([ue] + self.gue_allocated + self.due_allocated + self.eue_allocated, copy_ue)
            # from tests.assertion import assert_is_empty
            # assert_is_empty(spaces, ue, is_allocated)

    def allocate_one_ue(self, ue: UE, spaces: Tuple = ()) -> bool:
        """
        :param ue: The UE to allocate.
        :param spaces: A redundant input.
        :return: If the ue allocation succeed.
        """
        assert not ue.is_allocated, 'Not a new UE.'
        if ue.ue_type == UEType.D:
            space_in_nbs: List[Tuple[Space, ...]] = []
            for nb in [self.nb, self.another_nb]:
                space_in_nbs.append(self.update_empty_space(nb, ue))
                if not space_in_nbs[-1]:  # run out of space
                    return False

            allocate_ue: DCProportionAllocate = DCProportionAllocate(ue, self.channel_model)
            is_allocated: bool = allocate_ue.allocate(tuple(space_in_nbs))
        else:
            spaces: Tuple[Space, ...] = self.update_empty_space(self.nb, ue)
            if not spaces:  # run out of space
                return False

            allocate_ue: AllocateUE = AllocateUE(ue, spaces, self.channel_model)
            is_allocated: bool = allocate_ue.allocate()
        self.append_undo(lambda a_u=allocate_ue: a_u.undo(), lambda a_u=allocate_ue: a_u.purge_undo())
        return is_allocated

    @staticmethod
    def update_empty_space(nb: Union[GNodeB, ENodeB], ue: UE) -> Tuple[Space, ...]:
        # find the last occupied BU
        last_layer, last_freq_up_bound, last_time = Intuitive.find_row_last_bu(nb)

        if last_layer == last_freq_up_bound == last_time == -1:  # empty NB
            spaces: List[Space] = [Space(layer, 0, 0, nb.frame.frame_freq - 1, nb.frame.frame_time - 1) for
                                   layer in nb.frame.layer]
            for space in spaces:
                space.assert_is_empty()
            return tuple(spaces)

        last_freq_low_bound: int = Intuitive.find_row_lower_bound(last_layer, last_freq_up_bound, last_time, nb)

        # find a small space to continue to allocate
        if space_para := Intuitive.find_next_space_start_bu(
                last_layer, last_freq_up_bound, last_time, last_freq_low_bound, nb):
            bu_layer: int = space_para[0]
            bu_freq: int = space_para[1]
            bu_time: int = space_para[2]
            if bu_time != 0:  # is a smaller space
                in_use_numerology_freq: int = ue.numerology_in_use.freq if nb.nb_type == NodeBType.G else LTEResourceBlock.E.freq  # TODO: refactor or redesign
                space_end_i: int = bu_freq + in_use_numerology_freq - 1
                if space_end_i >= nb.frame.frame_freq:
                    bu_layer += 1
                    spaces: List[Space] = []
                else:
                    first_space: Space = Space(nb.frame.layer[bu_layer],
                                               bu_freq, bu_time, space_end_i, nb.frame.frame_time - 1)
                    first_space.assert_is_empty()
                    spaces: List[Space] = [first_space]
            else:
                spaces: List[Space] = []
        else:  # run out of space
            return tuple()
        assert (len(spaces) == 1 and spaces[0].width < nb.frame.frame_time) or (
                len(spaces) == 0), 'Should be a space smaller than frame time.'

        # find other large spaces
        for l in range(bu_layer, nb.frame.max_layer):
            new_spaces: Tuple[Space, ...] = empty_space(nb.frame.layer[l])

            # find a space at the end of the frame
            space_at_bottom: Optional[Space] = next(
                (s for s in new_spaces if (
                        s.width == nb.frame.frame_time) and (s.ending_i == nb.frame.frame_freq - 1)),
                None)
            if space_at_bottom:
                if l == bu_layer and len(spaces) == 1:  # found a small space earlier
                    assert spaces[0].width < nb.frame.frame_time, 'Not a smaller space.'
                    if spaces[0].ending_i >= space_at_bottom.starting_i:
                        starting_i: int = spaces[0].ending_i + 1
                    else:
                        starting_i: int = space_at_bottom.starting_i
                    if starting_i >= nb.frame.frame_freq:
                        continue
                    space_at_bottom: Space = Space(
                        space_at_bottom.layer, starting_i, space_at_bottom.starting_j,
                        space_at_bottom.ending_i, space_at_bottom.ending_j)
                spaces.append(space_at_bottom)
        return tuple(spaces)

    @staticmethod
    def find_next_space_start_bu(last_layer: int, last_freq: int, last_time: int, last_freq_low_bound: int,
                                 nb: Union[GNodeB, ENodeB]) -> Optional[Tuple[int, int, int]]:
        assert 0 <= last_layer < nb.frame.max_layer
        assert 0 <= last_freq <= last_freq_low_bound < nb.frame.frame_freq
        assert 0 <= last_time < nb.frame.frame_time
        first_bu_layer: int = last_layer
        first_bu_freq: int = last_freq
        first_bu_time: int = last_time + 1
        if first_bu_time >= nb.frame.frame_time:
            # next row
            first_bu_time: int = 0
            first_bu_freq: int = last_freq_low_bound + 1
            if first_bu_freq >= nb.frame.frame_freq:
                first_bu_layer += 1
                first_bu_freq: int = 0
                first_bu_time: int = 0
                if first_bu_layer >= nb.frame.max_layer:
                    return None  # run out of space
        return first_bu_layer, first_bu_freq, first_bu_time

    @staticmethod
    def find_row_last_bu(nb: Union[GNodeB, ENodeB]) -> Tuple[int, int, int]:
        layer, freq, time = Intuitive.find_latest_bu(nb)
        if layer == freq == time == -1:
            # empty NB
            return -1, -1, -1

        last_rb: ResourceBlock = nb.frame.layer[layer].bu[freq][time].within_rb
        assert last_rb, 'A unused BU.'

        last_numerology: Union[Numerology, LTEResourceBlock] = last_rb.numerology
        row_start: int = freq - last_numerology.freq + 1
        assert nb.frame.layer[layer].bu_status[row_start][time], 'Algorithm error.'
        col_end: int = time
        for t in range(time + 1, nb.frame.frame_time):
            if nb.frame.layer[layer].bu_status[row_start][t] is True:
                col_end: int = t
        assert nb.frame.layer[layer].bu_status[row_start][col_end], 'Algorithm error.'
        return layer, row_start, col_end

    @staticmethod
    def find_latest_bu(nb: Union[GNodeB, ENodeB]) -> Tuple[int, int, int]:
        for l in range(nb.frame.max_layer - 1, -1, -1):
            for f in range(nb.frame.frame_freq - 1, -1, -1):
                for t in range(nb.frame.frame_time - 1, -1, -1):
                    if nb.frame.layer[l].bu_status[f][t] is True:
                        return l, f, t
        return -1, -1, -1  # empty NB

    @staticmethod
    def find_row_lower_bound(layer: int, freq: int, time: int, nb: Union[GNodeB, ENodeB]):
        assert nb.frame.layer[layer].bu_status[freq][time], 'Input a unused BU.'
        assert time == nb.frame.frame_time - 1 or nb.frame.layer[layer].bu_status[freq][
            time + 1] is False, 'No the last BU.'

        if nb.nb_type == NodeBType.E:
            return freq + LTEResourceBlock.E.freq - 1

        # collect the numerology of RBs in the same row.
        numerology_set: Set[Numerology] = set()
        is_upper_left: int = 0
        for t in range(time, -1, -1):
            bu: BaseUnit = nb.frame.layer[layer].bu[freq][t]
            assert bu.is_used, 'Algorithm error.'
            numerology_set.add(bu.within_rb.numerology)
            if bu.is_upper_left:
                is_upper_left += 1
        assert numerology_set, 'Algorithm error.'
        assert len(numerology_set) <= is_upper_left, 'Input BU is not the start of a row of RB.'

        # find the longest RB
        longest_freq: int = -1
        for numerology in numerology_set:
            if numerology.freq > longest_freq:
                longest_freq: int = numerology.freq
        assert longest_freq > 0, 'Algorithm error.'
        return freq + longest_freq - 1
