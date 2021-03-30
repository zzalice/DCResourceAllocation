from typing import Dict, List, Optional, Tuple, Union

from src.channel_model.adjust_mcs import AdjustMCS
from src.channel_model.sinr import ChannelModel
from src.resource_allocation.ds.eutran import ENodeB
from src.resource_allocation.ds.frame import Layer
from src.resource_allocation.ds.ngran import GNodeB
from src.resource_allocation.ds.nodeb import ENBInfo, GNBInfo
from src.resource_allocation.ds.rb import ResourceBlock
from src.resource_allocation.ds.ue import UserEquipment
from src.resource_allocation.ds.undo import Undo
from src.resource_allocation.ds.util_enum import E_MCS, G_MCS, LTEResourceBlock, NodeBType, Numerology, UEType

BU = Dict[str, Union[int, Numerology, bool]]
#    bu  {'vacancy': the number of layers in the BS,
#         'numerology': the numerology this BU is using(in any layer),
#         'upper_left': if the BU is the upper left BU in a RB}
Status = Tuple[Tuple[BU, ...], ...]
#        freq  time
RB = Dict[str, int]  # {'bu_i': index, 'bu_j': index, 'layer': index}


class Msema(Undo):
    """
    UEs can only allocate to [BUs that has the same numerology as itself] or [BUs that are not used].
    At the same time, the RBs of a UE must be [continuous] but [can be in different layers].
    """

    def __init__(self, channel_model: ChannelModel, allocated_ue: Tuple[UserEquipment, ...]):
        super().__init__()
        self.channel_model: ChannelModel = channel_model
        self.nb: Optional[GNodeB, ENodeB] = None
        self.frame_status: Status = ()
        self.allocated_ue: List[UserEquipment] = list(allocated_ue)

    def allocate_ue_list(self, nb: Union[GNodeB, ENodeB], ue_list: List[UserEquipment]):
        self.nb: Union[GNodeB, ENodeB] = nb
        # from good channel quality
        if self.nb.nb_type == NodeBType.G:
            assert UEType.E not in [ue.ue_type for ue in ue_list]
            ue_list: List[UserEquipment] = sorted(ue_list, key=lambda x: x.coordinate.distance_gnb)
        elif self.nb.nb_type == NodeBType.E:
            assert UEType.G not in [ue.ue_type for ue in ue_list]
            ue_list: List[UserEquipment] = sorted(ue_list, key=lambda x: x.coordinate.distance_enb)

        self.frame_status: Status = tuple(
            tuple({'vacancy': self.nb.frame.max_layer, 'numerology': None, 'upper_left': False} for _ in
                  range(self.nb.frame.frame_time)) for _ in range(self.nb.frame.frame_freq))

        for ue in ue_list:
            # RB type
            tmp_numerology: Numerology = ue.numerology_in_use
            if self.nb.nb_type == NodeBType.E and ue.ue_type == UEType.D:
                ue.numerology_in_use = LTEResourceBlock.E  # TODO: refactor or redesign

            # main
            is_allocated: bool = self.allocate_ue(ue)
            if is_allocated:
                nb_info: Union[GNBInfo, ENBInfo] = ue.gnb_info if self.nb.nb_type == NodeBType.G else ue.enb_info
                self.update_frame_status(nb_info.rb)
                self.allocated_ue.append(ue)

            # restore RB type
            ue.numerology_in_use = tmp_numerology

    def allocate_ue(self, ue: UserEquipment) -> bool:
        assert not ue.is_allocated
        from utils.assertion import check_undo_copy  # TODO: commend to save time
        copy_ue = check_undo_copy([ue] + self.allocated_ue)

        bu_i: int = 0
        bu_j: int = 0
        while True:
            if start_rb := self.available_space(bu_i, bu_j, ue.numerology_in_use):
                # allocate new UE
                is_allocated, bu_i, bu_j = self.allocate_rb(ue, start_rb)

                # the effected UEs
                if is_allocated:
                    has_positive_effect: bool = self.adjust_effected_ue([ue] + self.allocated_ue)
                    if not has_positive_effect:
                        is_allocated: bool = False

                if is_allocated:
                    self.purge_undo(undo_all=True)
                    return True
                else:
                    self.undo(undo_all=True)
                    bu_i += 1
                    bu_j += 1

                    from utils.assertion import check_undo_compare  # TODO: commend to save time
                    check_undo_compare([ue] + self.allocated_ue, copy_ue)
                    continue
            else:
                # all the possible spaces are checked
                return False

    @Undo.undo_func_decorator
    def allocate_rb(self, ue: UserEquipment, first_rb: RB) -> Tuple[bool, int, int]:
        nb_info: Union[GNBInfo, ENBInfo] = ue.gnb_info if self.nb.nb_type == NodeBType.G else ue.enb_info
        bu_i: int = first_rb['bu_i']
        bu_j: int = first_rb['bu_j']
        layer: Layer = self.nb.frame.layer[first_rb['layer']]
        while True:
            # allocate a new RB
            rb: Optional[ResourceBlock] = layer.allocate_resource_block(bu_i, bu_j, ue)
            self.append_undo(lambda l=layer: l.undo(), lambda l=layer: l.purge_undo())
            if not rb:
                # overlapped with itself
                return False, bu_i, bu_j

            self.channel_model.sinr_rb(rb)
            self.append_undo(lambda: self.channel_model.undo(), lambda: self.channel_model.purge_undo())
            if rb.mcs is (G_MCS if nb_info.nb_type == NodeBType.G else E_MCS).CQI0:
                # SINR out of range
                return False, bu_i, bu_j

            # check if the allocated RBs fulfill request data rate
            if ue.calc_throughput() >= ue.request_data_rate:
                self.append_undo(lambda origin=nb_info.mcs: setattr(nb_info, 'mcs', origin))
                self.append_undo(lambda origin=ue.throughput: setattr(ue, 'throughput', origin))
                self.append_undo(lambda origin=ue.is_to_recalculate_mcs: setattr(ue, 'is_to_recalculate_mcs', origin))

                nb_info.update_mcs()
                ue.update_throughput()
                ue.is_to_recalculate_mcs = False
                return True, bu_i, bu_j

            # next RB
            if next_rb := self.continuous_available_rb(bu_i, bu_j, ue.numerology_in_use):
                bu_i: int = next_rb['bu_i']
                bu_j: int = next_rb['bu_j']
                layer: Layer = self.nb.frame.layer[next_rb['layer']]
            else:
                return False, bu_i, bu_j

    @Undo.undo_func_decorator
    def adjust_effected_ue(self, ue_list: List[UserEquipment]):
        while True:
            is_all_adjusted: bool = True
            for ue in ue_list:
                if ue.is_to_recalculate_mcs:
                    is_all_adjusted: bool = False
                    self.channel_model.sinr_ue(ue)
                    self.append_undo(lambda: self.channel_model.undo(), lambda: self.channel_model.purge_undo())
                    adjust_mcs: AdjustMCS = AdjustMCS()
                    has_positive_effect: bool = adjust_mcs.remove_worst_rb(ue, allow_lower_mcs=False)
                    self.append_undo(lambda a_m=adjust_mcs: a_m.undo(), lambda a_m=adjust_mcs: a_m.purge_undo())
                    if not has_positive_effect:
                        # the mcs of the ue is lowered down by another UE.
                        return False
            if is_all_adjusted:
                return True

    def available_space(self, bu_i: int, bu_j: int, ue_numerology: Numerology) -> Optional[RB]:
        for i in range(bu_i, self.nb.frame.frame_freq):
            for j in range(self.nb.frame.frame_time):
                if i == bu_i:
                    j += bu_j
                    if j >= self.nb.frame.frame_time:
                        break
                if self.is_available_rb(i, j, ue_numerology):
                    return {'bu_i': i, 'bu_j': j,
                            'layer': (self.nb.frame.max_layer - self.frame_status[i][j]['vacancy'])}
        return None

    def continuous_available_rb(self, bu_i: int, bu_j: int, ue_numerology: Numerology) -> Optional[RB]:
        # continuous RB
        bu_j += ue_numerology.time
        if bu_j + ue_numerology.time > self.nb.frame.frame_time:
            # next row
            bu_j = 0
            bu_i += ue_numerology.freq
            if bu_i + ue_numerology.freq > self.nb.frame.frame_freq:
                return None

        if self.is_available_rb(bu_i, bu_j, ue_numerology):
            return {'bu_i': bu_i, 'bu_j': bu_j,
                    'layer': (self.nb.frame.max_layer - self.frame_status[bu_i][bu_j]['vacancy'])}
        else:
            return None

    def is_available_rb(self, bu_i: int, bu_j: int, ue_numerology: Numerology) -> bool:
        if bu_i + ue_numerology.freq > self.nb.frame.frame_freq or bu_j + ue_numerology.time > self.nb.frame.frame_time:
            # out of bound
            return False

        for i in range(ue_numerology.freq):
            for j in range(ue_numerology.time):
                bu: BU = self.frame_status[bu_i + i][bu_j + j]
                self.assert_bu_status(bu)
                if i == j == 0:
                    if bu['numerology'] is None or (
                            bu['numerology'] == ue_numerology and bu['upper_left'] and bu['vacancy'] > 0):
                        # if the BU hasn't been used by any UE or is using the same numerology
                        continue
                    else:
                        return False
                else:
                    if bu['numerology'] is None or (
                            bu['numerology'] == ue_numerology and bu['upper_left'] is False and bu['vacancy'] > 0):
                        continue
                    else:
                        return False
        return True

    def update_frame_status(self, rb_list: List[ResourceBlock]):
        for rb in rb_list:
            for i in range(rb.numerology.freq):
                for j in range(rb.numerology.time):
                    bu: BU = self.frame_status[rb.i_start + i][rb.j_start + j]
                    self.assert_bu_status(bu)
                    if i == j == 0:
                        assert (bu['numerology'] is None and bu['upper_left'] is False) or (bu['upper_left']
                                                                                            ), 'The RBs must align.'
                        bu['upper_left'] = True
                    assert (bu['numerology'] is None) or (bu['numerology'] == rb.numerology
                                                          ), 'The BU is used and not with the same Numerology.'
                    bu['numerology'] = rb.numerology
                    bu['vacancy'] -= 1
                    assert bu['vacancy'] >= 0

    @staticmethod
    def assert_bu_status(bu: BU):
        if (bu['numerology'] is None and bu['upper_left']) or (
                bu['numerology'] is None and not bu['upper_left'] and bu['vacancy'] <= 0):
            raise AssertionError('Frame status update error.')
