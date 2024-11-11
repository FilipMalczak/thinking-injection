from enum import Enum
from inspect import Signature
from typing import NamedTuple, Optional, reveal_type

from pydot import frozendict
from thinking_modules.model import ModuleName

from thinking_reflection.source_scope import SourceScope, get_source_scope

UNSUPPORTED = Enum("UnsupportedEnum", ["UNSUPPORTED"]).UNSUPPORTED

AccessorType = Optional[type] | UNSUPPORTED

class FieldDeclaration(NamedTuple):
    get_type: AccessorType
    set_type: AccessorType

    @property
    def value_type(self) -> type:
        if self.get_type is not UNSUPPORTED:
            return self.get_type
        assert self.set_type is not UNSUPPORTED
        return self.set_type

class MethodDeclaration(NamedTuple):
    signature: Signature
    source_scope: SourceScope

class TypeDeclaration(NamedTuple):
    raw_type: type
    fields: frozendict[str, FieldDeclaration]
    methods: frozendict[str, MethodDeclaration]

    #todo caching
    @property
    def source_scope(self) -> SourceScope:
        return get_source_scope(self.raw_type)

    @property
    def name(self) -> str:
        return self.raw_type.__name__

    @property
    def module_name(self) -> ModuleName:
        return ModuleName.of(self.raw_type)

    @property
    def bases(self) -> tuple[type, ...]:
        return self.raw_type.__bases__

    @property
    def supertypes(self) -> tuple[type, ...]:
        return self.raw_type.__mro__