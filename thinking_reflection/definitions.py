from typing import NamedTuple, Self

from lazy import lazy
from pydot import frozendict
from thinking_modules.immutable import Immutable

from thinking_injection.typeset import types
from thinking_reflection.declarations import TypeDeclaration
from thinking_reflection.interfaces import known_interfaces
from thinking_reflection.model.classes import unique_concat, TypeDescriptor

def safe_issubclass(*args) -> bool:
    try:
        return issubclass(*args)
    except TypeError:
        #todo check message
        #todo I think I wrote it already
        return False

class TypeSpecification(Immutable):
    this: TypeDeclaration
    nominal_supertypes: tuple[TypeDeclaration, ...]
    structural_supertypes: tuple[TypeDeclaration, ...]

    @classmethod
    def empty(cls) -> Self:
        #todo make TypeDeclaration.empty()
        return cls(TypeDeclaration(object, frozendict(), frozendict()), tuple(), tuple())

    @classmethod
    def from_declaration(cls, d: TypeDeclaration) -> Self:
        return cls(
            d,
            tuple(
                TypeDeclaration.of(x)
                for x in d.supertypes
            ),
            tuple(
                TypeDeclaration.of(x)
                for x in known_interfaces()
                if safe_issubclass(d.raw_type, x)
            )
        )

    @lazy
    def all(self) -> tuple[TypeDeclaration, ...]:
        return unique_concat(tuple([self.this]), self.nominal_supertypes, self.structural_supertypes)

    def add(self, other: Self) -> Self:
        return TypeSpecification(
            self.this,
            unique_concat(self.nominal_supertypes, other.nominal_supertypes),
            unique_concat(tuple(other.this, ), self.structural_supertypes, other.structural_supertypes)
        )

    def __add__(self, other) -> Self:
        assert isinstance(other, TypeSpecification) #todo msg
        return self.add(other)

class TypeDefinition(NamedTuple):
    types: TypeSpecification
    type_descriptor: TypeDescriptor

    @classmethod
    def empty(cls) -> Self:
        return cls(TypeSpecification.empty(), TypeDescriptor.empty())

    @classmethod
    def from_declaration(cls, d: TypeDeclaration) -> Self:
        spec = TypeSpecification.from_declaration(d)
        desc = TypeDescriptor.empty()
        for x in spec.all:
            desc += x.type_descriptor
        return cls(spec, desc)

    @classmethod
    def of(cls, t: type) -> Self:
        return cls.from_declaration(TypeDeclaration.of(t))

    def add_descriptor(self, x: TypeDescriptor) -> Self:
        return TypeDefinition(self.types, self.type_descriptor + x)

    def add_declaration(self, x: TypeDeclaration) -> Self:
        return TypeDefinition(
            self.types,
            self.type_descriptor + x.type_descriptor
        )

    def add_definition(self, other: Self) -> Self:
        return TypeDefinition(
            self.types + other.types,
            self.type_descriptor + other.type_descriptor
        )

    def add(self, x) -> Self:
        if isinstance(x, TypeDescriptor):
            return self.add_descriptor(x)
        elif isinstance(x, TypeDeclaration):
            return self.add_declaration(x)
        elif isinstance(x, TypeDefinition):
            return self.add_definition(x)
        return self #todo or exception?

    def __add__(self, other) -> Self:
        assert isinstance(other, (TypeDescriptor, TypeDeclaration, TypeDefinition))
        return self.add(other)