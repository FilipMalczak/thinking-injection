from dataclasses import field, dataclass
from typing import NamedTuple

from thinking_injection.typeset import TypeSet, TypeAliasing


#fixme fields should be immutable too
class ContextScope(NamedTuple):
    types: TypeSet
    defaults: TypeAliasing = field(default_factory=dict)
    forced: TypeAliasing = field(default_factory=dict)

    @classmethod
    def of(cls, *types: type, defaults: TypeAliasing = None, forced: TypeAliasing = None):
        assert types #todo msg
        types = set(types)
        defaults = defaults or {}
        forced = forced or {}
        assert all(
            isinstance(k, type) and
            isinstance(v, type) and
            k in types and
            v in types and
            issubclass(v, k)
            for k, v in defaults.items()
        ) #todo msg
        assert all(
            isinstance(k, type) and
            isinstance(v, type) and
            k in types and
            v in types and
            issubclass(v, k)
            for k, v in forced.items()
        )  # todo msg
        return cls(types, defaults, forced)

    #todo of_package, of_module, __add__ (disallows duplicates), __or__ (like +, but in case of duplicates in defaults and forced - uses left side)