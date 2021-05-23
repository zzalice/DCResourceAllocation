from typing import Callable, Optional, Tuple, Union

from src.channel_model.sinr import ChannelModel
from src.resource_allocation.algo.util_type import RBIndex
from src.resource_allocation.ds.rb import ResourceBlock
from src.resource_allocation.ds.space import next_rb_in_space
from src.resource_allocation.ds.ue import UserEquipment
from src.resource_allocation.ds.undo import Undo


class NewResource(Undo):
    def __init__(self):
        super().__init__()

    def add_one_continuous_rb(self, ue: UserEquipment, channel_model: ChannelModel,
                              same_numerology: bool = False, func_is_available_rb: Callable = None
                              ) -> Union[ResourceBlock, bool]:
        """
        Design for single and dual connection UE.
        :param ue: The UE to add a new RB.
        :param channel_model: For the new RB.
        :param same_numerology: If is True, add a RB has the same numerology with other layers or any layer is empty.
        :param func_is_available_rb: If same_numerology is True, is_available_rb should also be given.
        :return: If a RB is allocated.
        """
        assert (not same_numerology) or (same_numerology and func_is_available_rb is not None), 'Function not given.'
        # the RB in highest frequency and latest time in a frame
        last_rb_gnb: Optional[ResourceBlock] = None
        last_rb_enb: Optional[ResourceBlock] = None
        last_rb: Optional[ResourceBlock] = None
        if hasattr(ue, 'gnb_info'):
            last_rb_gnb: Optional[ResourceBlock] = ue.gnb_info.highest_frequency_rb()
        if hasattr(ue, 'enb_info'):
            last_rb_enb: Optional[ResourceBlock] = ue.enb_info.highest_frequency_rb()
        if last_rb_gnb and last_rb_enb:
            # pick the one with higher efficiency
            if last_rb_gnb.mcs.efficiency > last_rb_enb.mcs.efficiency:
                last_rb: ResourceBlock = last_rb_gnb
            else:
                last_rb: ResourceBlock = last_rb_enb
        elif last_rb_gnb:
            last_rb: ResourceBlock = last_rb_gnb
        elif last_rb_enb:
            last_rb: ResourceBlock = last_rb_enb
        else:
            assert last_rb_gnb is not None or last_rb_enb is not None, "The UE isn't allocated."

        # check if there is empty space for one RB after the last_rb
        next_rb: Optional[Tuple[int, int]] = next_rb_in_space(last_rb.i_start, last_rb.j_start,
                                                              ue.numerology_in_use,
                                                              last_rb.layer, 0, 0,
                                                              last_rb.layer.FREQ - 1, last_rb.layer.TIME - 1)
        if next_rb is None:  # no continuous space for another RB. run out of space.
            return False
        if same_numerology and not func_is_available_rb(
                RBIndex(layer=last_rb.layer.layer_index, i=next_rb[0], j=next_rb[1]),
                last_rb.numerology, last_rb.layer.nodeb):
            return False

        self.start_func_undo()

        # allocate a RB in the space
        new_rb: Optional[ResourceBlock] = last_rb.layer.allocate_resource_block(next_rb[0], next_rb[1], ue)
        self.append_undo(lambda l=last_rb.layer: l.undo(), lambda l=last_rb.layer: l.purge_undo())
        if new_rb is None:  # allocation failed
            self.end_func_undo()
            self.purge_undo()
            return False

        # the SINR of the new RB
        assert channel_model is not None, "Channel model isn't passed in."
        channel_model.sinr_rb(new_rb)
        self.append_undo(lambda: channel_model.undo(), lambda: channel_model.purge_undo())

        self.end_func_undo()

        if new_rb.mcs.efficiency == 0.0:
            self.undo()
            return False

        return new_rb
