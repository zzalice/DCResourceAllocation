from src.resource_allocation.ds.undo import Undo


class Test(Undo):
    def __init__(self):
        super().__init__()
        self.i = 0
        self.l = []

    @Undo.undo_func_decorator
    def add(self, value=1):
        self.append_undo(lambda origin=self.i: setattr(self, 'i', origin))
        self.i += value

    @Undo.undo_func_decorator
    def nested_decorator(self):
        self.add()

    def no_decorator(self):
        self.append_undo(lambda: print("Shouldn't print this!"))

    @Undo.undo_func_decorator
    def undo_in_undo(self):
        t2 = Test2()
        for _ in range(5):
            self.append_undo(lambda origin=self.i: setattr(self, 'i', origin))
            self.i += 1
            t2.increase()
            self.append_undo(lambda: t2.undo(), lambda: t2.purge_undo())
        return t2

    @Undo.undo_func_decorator
    def append_remove(self):
        i = 1
        self.l.append(i)
        self.append_undo(lambda: self.l.remove(i))
        self.l.remove(i)
        self.append_undo(lambda: self.l.append(i))


class Test2(Undo):
    def __init__(self):
        super().__init__()
        self.i = 0

    @Undo.undo_func_decorator
    def increase(self, value=3):
        self.append_undo(lambda origin=self.i: setattr(self, 'i', origin))
        self.i += value


def test_decorator():
    test = Test()
    assert test.i == 0
    test.add()
    assert test.i == 1
    test.undo()
    assert test.i == 0

    test.add(value=2)
    test.add()
    assert test.i == 3
    test.undo(undo_all=True)
    assert test.i == 0

    # ==========================
    try:
        test.nested_decorator()
        assert False
    except AssertionError:
        assert True
        test.purge_undo()
        test._end_of_func = True
    pass

    # ==========================
    try:
        test.no_decorator()
        assert False
    except AssertionError:
        assert True

    # ==========================
    test2 = test.undo_in_undo()
    assert test2.i == 15 and test.i == 5
    test.undo()
    assert test2.i == 0 and test.i == 0

    # ==========================
    test2 = test.undo_in_undo()
    assert test2.i == 15 and test.i == 5
    test.purge_undo()
    assert test2.i == 15 and test.i == 5

    # ==========================
    test.append_remove()
    assert test.l == []
    test.undo()
    assert test.l == []


