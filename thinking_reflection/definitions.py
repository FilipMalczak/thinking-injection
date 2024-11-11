from collections import defaultdict
from dataclasses import dataclass, fields, field
from typing import NamedTuple, Self

from frozendict import frozendict

from thinking_reflection.declarations import analyse_declaration
from thinking_reflection.model import TypeDeclaration, AccessorType, MethodDeclaration


class FieldDefinition(NamedTuple):
    get_types: tuple[AccessorType, ...]
    set_types: tuple[AccessorType, ...]


@dataclass
class MutableFieldDefinition:
    get_types: list[AccessorType, ...] = field(default_factory=list)
    set_types: list[AccessorType, ...] = field(default_factory=list)

    def freeze(self) -> FieldDefinition:
        return FieldDefinition(tuple(self.get_types), tuple(self.set_types))


class MethodDefinition(NamedTuple):
    declarations: tuple[MethodDeclaration, ...]


@dataclass
class MutableMethodDefinition:
    declarations: list[MethodDeclaration, ...] = field(default_factory=list)

    def freeze(self) -> MethodDefinition:
        return MethodDefinition(tuple(self.declarations))

class TypeDefinition(NamedTuple):
    declaration: TypeDeclaration
    fields: frozendict[str, FieldDefinition]
    methods: frozendict[str, MethodDefinition]
    #todo add non-structural supertypes (basically, protocols; scan interfaces for that); append declarations from there at the end when resolving

    @classmethod
    def resolve(cls, declaration: TypeDeclaration) -> Self:
        fields = defaultdict(MutableFieldDefinition)
        methods = defaultdict(MutableMethodDefinition)
        for decl in [declaration] + [analyse_declaration(x) for x in declaration.supertypes]:
            for f, fd in decl.fields.items():
                field = fields[f]
                field.get_types.append(fd.get_type)
                field.set_types.append(fd.set_type)
            for m, md in decl.methods.items():
                methods[m].declarations.append(md)
        return cls(
            declaration,
            frozendict({k: v.freeze() for k, v in fields.items()}),
            frozendict({k: v.freeze() for k, v in methods.items()})
        )

    @classmethod
    def of(cls, t: type) -> Self:
        return cls.resolve(analyse_declaration(t))
