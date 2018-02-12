from textwrap import dedent
import pytest
import pickle

from modelx.core.api import *
from modelx.core import system


# ---- Test impl ----

@pytest.fixture
def pickletest():

    model = new_model('TestModel')
    space = model.new_space()

    func1 = dedent("""\
    def single_value(x):
        return 5 * x
    """)

    func2 = dedent("""\
    def mult_single_value(x):
        return 2 * single_value(x)
    """)

    func1 = space.new_cells(func=func1)
    func2 = space.new_cells(func=func2)

    func2(5)

    byte_obj = pickle.dumps(model._impl)
    unpickled = pickle.loads(byte_obj)

    return [model._impl, unpickled]


def test_unpickled_model(pickletest):

    model, unpickeld = pickletest

    errors = []

    if not model.name == unpickeld.name:
        errors.append("name did not match")

    if not hasattr(model, 'interface'):
        errors.append("no interface")

    if not hasattr(model, 'cellgraph'):
        errors.append("no cellgraph")

    assert not errors, "errors:\n{}".format("\n".join(errors))



def test_pickle_dynamic_space():

    param = dedent("""\
    def param(x):
        return {'bases': _self}
    """)

    fibo = dedent("""\
    def fibo(n):
        return x * n""")

    model, space = new_model(), new_space(name='Space1', paramfunc=param)
    space.new_cells(func=fibo)

    check = space[2].fibo(3) == 6

    byte_obj = pickle.dumps(model._impl)
    unpickled = pickle.loads(byte_obj)
    unpickled.restore_state(system)
    model = unpickled.interface

    check = check and model.Space1[2].fibo(3) == 6
    assert check


