from enum import Enum
from inspect import Signature
from typing import Optional, NamedTuple

from thinking_reflection.model.source_scope import SourceScope

UNSUPPORTED = Enum("UnsupportedEnum", ["UNSUPPORTED"]).UNSUPPORTED

AccessorType = Optional[type] | UNSUPPORTED


class FieldDescriptor(NamedTuple):
    get_type: AccessorType
    set_type: AccessorType

    @property
    def value_type(self) -> type:
        if self.get_type is not UNSUPPORTED:
            return self.get_type
        assert self.set_type is not UNSUPPORTED
        return self.set_type


class MethodDescriptor(NamedTuple):
    signature: Signature
    source_scope: SourceScope
