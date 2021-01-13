"""reference: shorturl.at/rDLS0"""
from typing import Callable, List, Set, Union


class Undo:
    def __init__(self):
        self._undo_stack: List[Callable] = []
        self._purge_stack: Set[Undo] = set()

    def append_undo(self, local_undo_stack: List[Union[Callable, object]]) -> Callable:
        if len(local_undo_stack) == 2:
            assert isinstance(local_undo_stack[1], Undo)
            # Though adding purge to set won't save the actual state,
            # the newer _undo_stack will over write the old one.
            # The aim of purge does change.
            self._purge_stack.add(local_undo_stack[1])

        def undo_func():
            undo_func.__dict__['has_called'] = True
            (local_undo_stack[0])()
            # remove self (i.e., lambda: undo_func()) from the global undo stack
            self._undo_stack.remove(undo_func.__dict__['undo_lambda'])

        undo_func.undo_lambda = lambda: undo_func()
        self._undo_stack.append(undo_func.undo_lambda)
        return undo_func.undo_lambda

    def undo(self) -> bool:
        if len(self._undo_stack) == 0:
            return False  # nothing to undo
        else:
            # undo funcs in reverse order
            # don't do `pop()` here, it's done in the end of the inner `undo_a_func()`
            while self._undo_stack:
                (self._undo_stack[-1])()
            return True

    def purge_undo(self):
        # To free the memory when the UE allocation is to be implemented.
        self._undo_stack.clear()
        while self._purge_stack:
            obj: Undo = self._purge_stack.pop()
            obj.purge_undo()
