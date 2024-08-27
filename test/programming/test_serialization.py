from dataclasses import dataclass
from enum import auto, Enum

from thinking_tests.decorators import case
from thinking_tests.start import run_current_module

from thinking_programming.serialization import SerializableMixin, PolymorphicSerializableMixin

#fixme notably it fails tits over for namedtuples; gotta work on that and that why there are only dataclass tests
#todo work

@dataclass
class X(SerializableMixin):
    a: str
    b: list[int]

@dataclass
class A(SerializableMixin):
    x: int
    y: str
    z: list[int]
    w: dict[int, X]

@case
def case_X():
    x = X("x1", [5])
    e = {
        "a": "x1",
        "b": [5]
    }
    assert x.serialize() == e
    assert X.deserialize(e) == x

@case
def case_X_w_None():
    x = X(None, None)
    e = {"a": None, "b": None}
    assert x.serialize() == e
    assert X.deserialize(e) == x

@case
def case_A():
    a = A(
        1,
        "x",
        [2, 3],
        {
            1: X("x1", [5]),
            2: X("x2", [6, 7]),
            3: X("x3", [])
        }
    )
    e = {
        "x": 1,
        "y": "x",
        "z": [2, 3],
        "w": {
            1: {
                "a": "x1",
                "b": [5]
            },
            2: {
                "a": "x2",
                "b": [6, 7]
            },
            3: {
                "a": "x3",
                "b": []
            }
        }
    }
    assert a.serialize() == e
    assert A.deserialize(e) == a

class E(Enum):
    E1 = auto()
    E2 = auto()

@dataclass
class EW(SerializableMixin):
    e: E

@case
def test_enums():
    a = EW(E.E1)
    e = {"e": "E1"}
    assert a.serialize() == e
    assert EW.deserialize(e) == a

class Poly(PolymorphicSerializableMixin): pass

@dataclass
class P1(Poly):
    a: str

@dataclass
class P2(Poly):
    b: int

@case
def case_Poly():
    p1 = P1("a")
    e1 = {'a': 'a', '__type_id__': f'{__name__}.P1'}
    p2 = P2(3)
    e2 = {'b': 3, '__type_id__': f'{__name__}.P2'}
    assert p1.serialize() == e1
    assert Poly.deserialize(e1) == p1
    assert p2.serialize() == e2
    assert Poly.deserialize(e2) == p2

if __name__=="__main__":
    run_current_module()
