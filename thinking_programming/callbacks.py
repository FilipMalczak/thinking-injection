from dataclasses import dataclass, field
from functools import wraps
from logging import getLogger
from typing import TypeVar, Union, dataclass_transform

from thinking_tests.fluent_decorator import fluent_decorator

logger = getLogger(__name__)

_IS_CALLBACK = "__is_callback_method__"
_IS_REVERSE_ORDER = "__is_callback_order_reversed__"

@fluent_decorator
def callback_method(reverse_order_of_composing=False):
    def decorator(f):
        setattr(f, _IS_CALLBACK, True)
        setattr(f, _IS_REVERSE_ORDER, reverse_order_of_composing)
        return f
    return decorator

def _callback_methods(t: type):
    return list(
        filter(
            lambda x: getattr(x, _IS_CALLBACK, False),
            (
                getattr(t, x)
                for x in dir(t)
            )
        )
    )

_composite_types = {}

T = TypeVar("T")

@dataclass
class Composite:
    delegates: list[T] = field(default_factory=list)

    def add_delegate(self, *delegates: T):
        self.delegates.extend(delegates)

    def clean_delegates(self):
        self.delegates = []

    def __str__(self):
        return _str(self, "delegates")

    __repr__ = __str__

#todo @cached
@dataclass_transform()
def CompositeCallback(t: type[T]) -> type[T, Composite]:
    if t.__name__ in _composite_types:
        return _composite_types[t.__name__]
    type_name = f"Composite{t.__name__}"
    def impl(m):
        order = reversed if getattr(m, _IS_REVERSE_ORDER) else lambda x: x
        @wraps(m)
        def wrapper(self, *args, **kwargs):
            for delegate in order(self.delegates):
                getattr(delegate, m.__name__)(*args, **kwargs)
        return wrapper
    methods = {
        m.__name__: impl(m)
        for m in _callback_methods(t)
    }
    out = type(type_name, (Composite, t), methods)
    _composite_types[t.__name__] = out
    return out

def compose(callbacks: Union[list[T], T], t: type[T]) -> T:
    if isinstance(callbacks, t): #pycharm will complain, but ignore it
        return callbacks
    if len(callbacks) == 0:
        return t()
    if len(callbacks) == 1:
        return callbacks[0]
    #todo flatten; if any element is already composite, add its delegates to results delegates (recursively)
    return CompositeCallback(t)(list(callbacks))
