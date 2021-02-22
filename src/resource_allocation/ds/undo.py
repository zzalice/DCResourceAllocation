# reference: https://github.com/LouisSung/UndoFunc/commit/a0235bddd236475ea4ea96df106a6599ffc35b00
from typing import Any, Callable, Dict, List, Tuple


class Undo:
    def __init__(self):
        self._func_stack: List[List[Tuple[Callable, Callable]]] = []
        self._end_of_func: bool = True

    def append_undo(self, local_func_stack: Callable, purge_callback: Callable = lambda: None):
        def _execute(undo_or_purge: int):
            if hasattr(_execute, 'has_called'):  # should never call an undo twice
                raise ValueError('NEVER invoke the returned `undo()` twice')
            else:
                _execute.__setattr__('has_called', True)
                if undo_or_purge == 0:  # undo
                    local_func_stack()
                elif undo_or_purge == 1:  # purge
                    purge_callback()
                else:
                    raise ValueError
                _execute.__delattr__('undo_lambdas')

        assert self._func_stack or self._end_of_func is False, "Didn't start a function undo."
        _execute.undo_lambdas = (lambda: _execute(0), lambda: _execute(1))
        self._func_stack[-1].append(_execute.undo_lambdas)

    def start_of_func_undo(self):
        assert self._end_of_func, "The last function undo isn't closed."
        self._end_of_func: bool = False
        self._func_stack.append([])

    def end_of_func_undo(self):
        assert not self._end_of_func, "The start undo function isn't called."
        self._end_of_func: bool = True

    @staticmethod
    def undo_func_decorator(func: callable) -> callable:
        def wrap(*args, **kwargs) -> Any:
            args[0].start_of_func_undo()
            val = func(*args, **kwargs)
            args[0].end_of_func_undo()
            return val
        return wrap

    def assert_undo_function(self):
        """If assertion raised means the function calling this isn't in the duration of undo_func_decorator."""
        assert self._end_of_func is False, "A new undo function isn't created."

    def undo(self, undo_all: bool = False, undo_times: int = 1) -> bool:
        return self._undo_functions(0, undo_all, undo_times)

    def purge_undo(self, undo_all: bool = False, undo_times: int = 1) -> bool:
        return self._undo_functions(1, undo_all, undo_times)

    def _undo_functions(self, undo_or_purge: int, undo_all, undo_times) -> bool:
        num_of_func: int = len(self._func_stack) if undo_all else min(undo_times, len(self._func_stack))
        if num_of_func == 0:
            return False  # nothing to undo
        else:
            # undo funcs in reverse order
            # don't do `pop()` here, it's done in the end of the inner `undo_a_func()`
            for _ in range(num_of_func):
                self._undo_function(self._func_stack.pop(), undo_or_purge)
            return True

    @staticmethod
    def _undo_function(func_stack: List[Tuple[Callable, Callable]], undo_or_purge: int):
        while func_stack:
            (func_stack.pop()[undo_or_purge])()

    def __getstate__(self):
        return self.empty_undo_stake(self.__dict__)

    @staticmethod
    def empty_undo_stake(d):
        d_copy: Dict = d.copy()
        if d_copy['_func_stack']:
            d_copy['_func_stack'] = []
        return d_copy
