"""reference: shorturl.at/rDLS0"""
from typing import Callable, List, Set


class Undo:
    def __init__(self):
        self._undo_stack: List[Callable] = []
        self.purge_stack: Set[Undo] = set()

    def undo_a_func(self, func_local_undo_stack: List[Callable]) -> Callable:
        def undo_func():
            undo_func.__dict__['has_called'] = True
            while func_local_undo_stack:
                (func_local_undo_stack.pop())()
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

    def purge(self):
        self._undo_stack.clear()
        while self.purge_stack:
            obj: Undo = self.purge_stack.pop()
            obj.purge()