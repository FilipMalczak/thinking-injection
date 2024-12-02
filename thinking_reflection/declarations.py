from abc import ABC
from collections.abc import Callable
from inspect import signature, get_annotations, Signature, Parameter
from logging import getLogger
from typing import NamedTuple, Optional, Protocol, runtime_checkable, Self

from frozendict import frozendict
from thinking_modules.model import ModuleName

from thinking_reflection.descriptor_protocol import AnyDescriptor
from thinking_reflection.inspect_mate import is_regular_method
from thinking_reflection.model.classes import TypeDescriptor
from thinking_reflection.model.members import FieldDescriptor, MethodDescriptor, UNSUPPORTED
from thinking_reflection.model.source_scope import get_source_scope, DescriptorSourceScope, SourceScope

log = getLogger(__name__)

def wrap_values[T, T2](d: frozendict[str, T], m: Callable[[T], T2]) -> frozendict[str, T2]:
    return frozendict({
        k: m(v)
        for k, v in d.items()
    })

def _to_nonflat_tuple(x):
    return (x, )

class TypeDeclaration(NamedTuple):
    raw_type: type
    fields: frozendict[str, FieldDescriptor]
    methods: frozendict[str, MethodDescriptor]

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

    @classmethod
    def of(cls, t: type) -> Self:
        return analyse_declaration(t)

    @property
    def supertypes(self) -> tuple[type, ...]:
        return self.raw_type.__mro__

    @property
    def type_descriptor(self) -> TypeDescriptor:
        return TypeDescriptor(wrap_values(self.fields, _to_nonflat_tuple), wrap_values(self.methods, _to_nonflat_tuple))

@runtime_checkable
class Analyser[A, T, D](Protocol):
    def can_analyse(self, subject: A) -> bool: pass

    def analyse(self, subject: T) -> D: pass

@runtime_checkable
class DescriptorAnalyser[T: AnyDescriptor](Analyser[AnyDescriptor, T, FieldDescriptor], Protocol):
    def get_source_scope(self, subject: AnyDescriptor) -> Optional[DescriptorSourceScope]: pass

class PropertyAnalyser(DescriptorAnalyser[property]):
    def can_analyse(self, descriptor: AnyDescriptor) -> bool:
        return isinstance(descriptor, property)

    def get_source_scope(self, subject: AnyDescriptor) -> DescriptorSourceScope:
        def describe_source_scope(foo):
            if foo is not None:
                return get_source_scope(foo)
            return None
        return DescriptorSourceScope(None, describe_source_scope(subject.fget), describe_source_scope(subject.fset))

    def analyse(self, descriptor: property) -> FieldDescriptor:

        def get_type():
            if descriptor.fget is None:
                return UNSUPPORTED
            s = signature(descriptor.fget)
            result = s.return_annotation
            if result is Signature.empty:
                result = object
            return result
        def set_type():
            if descriptor.fset is None:
                return UNSUPPORTED
            s = signature(descriptor.fset)
            if len(s.parameters) < 2:
                return UNSUPPORTED
            result = list(s.parameters.values())[1].annotation
            if result is Parameter.empty:
                result = object
            return result

        return FieldDescriptor(
            get_type(),
            set_type()
        )

class IgnoringAnalyser(DescriptorAnalyser[AnyDescriptor]):
    def can_analyse(self, subject: AnyDescriptor) -> bool:
        return True

    def get_source_scope(self, subject: AnyDescriptor) -> Optional[DescriptorSourceScope]:
        return None

    def analyse(self, subject: AnyDescriptor) -> FieldDescriptor:
        raise NotImplementedError()
#
# def analyse_descriptor(desc: AnyDescriptor) -> FieldDescriptor:
#     for a in DESCRIPTOR_ANALYSERS:
#         if a.can_analyse(desc):
#             return a.analyse(desc)
#     assert False #todo

def is_public(name):
    #dunder methods are public by default, since they indicate some protocol
    #todo add __init__, __new__, etc sxclusion
    # see test_definitions.SimpleClass
    return not name.startswith("_") or (name.startswith("__") and not name.startswith("___"))

def is_abstract(foo):
    try:
        return foo.__isabstractmethod__
    except AttributeError:
        return False

class TypeAnalyser(Analyser[type, type, TypeDeclaration], Protocol): pass

class BaseTypeAnalyser(TypeAnalyser):
    def _method_filter(self, name: str, foo: Callable) -> bool: pass
    def _descriptor_filter(self, name: str, desc: AnyDescriptor) -> bool: pass
    def _annotation_filter(self, name: str, t: type) -> bool: pass

    def analyse(self, subject: type) -> TypeDeclaration:
        fields = {}
        methods = {}
        for name, t in get_annotations(subject).items():
            if self._annotation_filter(name, t):
                fields[name] = FieldDescriptor(t, t)
        type_scope = get_source_scope(subject)
        if type_scope:
            for name in dir(subject):
                log.info(f"Subject name: {name}")
                val = getattr(subject, name)
                if is_regular_method(subject, name):
                    log.info(f"{name} is a regular method")
                    try:
                        val_scope = get_source_scope(val)
                    except:
                        raise
                    log.info(f"Scope: {val_scope}")
                    if val_scope in type_scope and self._method_filter(name, val):
                        methods[name] = MethodDescriptor(signature(val), val_scope)
                        log.info(f"Method: {methods[name]}")
                    else:
                        log.info(f"Ignoring ({val_scope in type_scope}, {self._method_filter(name, val)})")
                # descriptors override the annotation
                elif isinstance(val, AnyDescriptor):
                    log.info(f"{name} is a descriptor")
                    for analyser in DESCRIPTOR_ANALYSERS:
                        if analyser.can_analyse(val):
                            desc_scope = analyser.get_source_scope(val)
                            if desc_scope:
                                log.info(f"Scope: {desc_scope}")
                                if desc_scope in type_scope and self._descriptor_filter(name, val):
                                    fields[name] = analyser.analyse(val)
                                    log.info(f"Field: {fields[name]}")
                                    break
                                else:
                                    log.info(f"Ignoring ({desc_scope in type_scope}, {self._descriptor_filter(name, val)})")
                            else:
                                log.info(f"No-source element {val}, ignoring")
                else:
                    log.info(f"Ignoring {name}")
                    pass #this explicitly ignores class-level fields
        else:
            log.info(f"No-source subject {subject}, ignoring")
        return TypeDeclaration(subject, frozendict(fields), frozendict(methods))

class ProtocolAnalyser(BaseTypeAnalyser):
    def can_analyse(self, subject: type) -> bool:
        return Protocol in subject.__bases__

    def _annotation_filter(self, name: str, t: type) -> bool:
        return True

    def _method_filter(self, name: str, foo: Callable) -> bool:
        return True

    def _descriptor_filter(self, name: str, desc: AnyDescriptor) -> bool:
        return True

class ABCAnalyser(BaseTypeAnalyser):
    def can_analyse(self, subject: type) -> bool:
        return ABC in subject.__bases__

    def _annotation_filter(self, name: str, t: type) -> bool:
        return True

    def _method_filter(self, name: str, foo: Callable) -> bool:
        return is_public(name) or is_abstract(foo)

    def _descriptor_filter(self, name: str, desc: AnyDescriptor) -> bool:
        return is_public(name) or is_abstract(desc)

class CommonAnalyser(BaseTypeAnalyser):
    def can_analyse(self, subject: type) -> bool:
        return True

    def _annotation_filter(self, name: str, t: type) -> bool:
        return is_public(name)

    def _method_filter(self, name: str, foo: Callable) -> bool:
        return is_public(name)

    def _descriptor_filter(self, name: str, desc: AnyDescriptor) -> bool:
        return is_public(name)

DESCRIPTOR_ANALYSERS: list[DescriptorAnalyser] = [
    PropertyAnalyser(),
    IgnoringAnalyser()
]

TYPE_ANALYSERS: list[TypeAnalyser] = [
    ProtocolAnalyser(),
    ABCAnalyser(),
    CommonAnalyser()
]

def register_descriptor_analyser(t: type[DescriptorAnalyser]):
    DESCRIPTOR_ANALYSERS.insert(0, t())

def register_type_analyser(t: type[TypeAnalyser]):
    TYPE_ANALYSERS.insert(0, t())

def analyse_declaration(t: type) -> TypeDeclaration:
    for a in TYPE_ANALYSERS:
        if a.can_analyse(t):
            return a.analyse(t)
    assert False # CommonAnalyser should have worked as a fallback
