from __future__ import annotations

from typing import List, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from src.resource_allocation.ds.nodeb import ENBInfo, GNBInfo
    from src.resource_allocation.ds.rb import ResourceBlock
    from src.resource_allocation.ds.ue import UserEquipment


class CopyRB:
    def __init__(self, rb: ResourceBlock):
        self.id = id(rb)
        self.i_start = rb.i_start
        self.j_start = rb.j_start
        self.sinr = rb.sinr


class CopyNBInfo:
    def __init__(self, nb_info: Union[GNBInfo, ENBInfo]):
        self.nb_type = nb_info.nb_type
        self.mcs = nb_info.mcs
        self.rb: List[CopyRB] = [CopyRB(rb) for rb in nb_info.rb]


class CopyUE:
    def __init__(self, ue: UserEquipment):
        self.uuid = ue.uuid
        self.throughput: float = ue.throughput
        self.is_allocated: bool = ue.is_allocated
        self.is_to_recalculate_mcs: bool = ue.is_to_recalculate_mcs
        if hasattr(ue, 'gnb_info'):
            self.gnb_info: CopyNBInfo = CopyNBInfo(ue.gnb_info)
        if hasattr(ue, 'enb_info'):
            self.enb_info: CopyNBInfo = CopyNBInfo(ue.enb_info)


def check_undo_copy(allocated_ue: List[UserEquipment]) -> List[CopyUE]:
    return [CopyUE(ue) for ue in allocated_ue]


def check_undo_compare(allocated_ue: List[UserEquipment], copy_ue: List[CopyUE]):
    for ue in allocated_ue:
        copy_ue.sort(key=lambda x: x.uuid != ue.uuid)
        if copy_ue[0].uuid != ue.uuid:
            raise AssertionError("ue not found")

        assert copy_ue[0].throughput == ue.throughput
        assert copy_ue[0].is_allocated == ue.is_allocated
        assert copy_ue[0].is_to_recalculate_mcs == ue.is_to_recalculate_mcs
        for i in ['gnb_info', 'enb_info']:
            if hasattr(ue, i):
                ue_nb_info: Union[GNBInfo, ENBInfo] = getattr(ue, i)
                aue0_nb_info: CopyNBInfo = getattr(copy_ue[0], i)
                assert aue0_nb_info.mcs == ue_nb_info.mcs
                assert len(aue0_nb_info.rb) == len(ue_nb_info.rb)
                for rb in ue_nb_info.rb:
                    aue0_nb_info.rb.sort(key=lambda x: x.i_start != rb.i_start)
                    aue0_nb_info.rb.sort(key=lambda x: x.j_start != rb.j_start)
                    assert aue0_nb_info.rb[0].sinr == rb.sinr
    # except AssertionError:
    #     print('undo fail!', locals())


def assert_is_empty(spaces, this_ue, is_allocated):
    for space in spaces:
        for i in range(space.starting_i, space.ending_i + 1):
            for j in range(space.starting_j, space.ending_j + 1):
                if space.layer.bu_status[i][j]:
                    space.layer.bu_status_cache_is_valid = False
                    assert space.layer.bu_status[i][j], "bu_status_cache_is_valid is True when it should be False."
                    assert space.layer.bu[i][j].within_rb.ue is this_ue, "Which UE is this???"
                    assert is_allocated is True, "undo() fail. Space not cleared"
                    raise AssertionError


def assert_throughput(ue: UserEquipment):
    if hasattr(ue, 'gnb_info'):
        if ue.gnb_info.mcs:
            assert ue.gnb_info.rb, "There is MCS but no RB(s)"
            assert (ue.gnb_info.mcs.value <= rb.mcs.value for rb in ue.gnb_info.rb)
        else:
            assert ue.gnb_info.mcs is None and not ue.gnb_info.rb, "The MCS is not up-to-date."
    if hasattr(ue, 'enb_info'):
        if ue.enb_info.mcs:
            assert ue.enb_info.rb, "There is MCS but no RB(s)"
            assert (ue.enb_info.mcs.value <= rb.mcs.value for rb in ue.enb_info.rb)
        else:
            assert ue.enb_info.mcs is None and not ue.enb_info.rb, "The MCS is not up-to-date."

    assert ue.throughput == ue.calc_throughput()
    assert ue.throughput >= ue.request_data_rate


class ThroughputError(Exception):
    def __init__(self, message='Throughput is lower than request.'):
        super().__init__(message)
