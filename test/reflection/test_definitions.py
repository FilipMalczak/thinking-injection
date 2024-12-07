from abc import ABC, abstractmethod
from typing import Protocol, Optional

from frozendict import frozendict
from thinking_tests.decorators import case
from thinking_tests.running.start import run_current_module

from test.reflection.test_definitions_by_matrix import DiscoveredClass, SimpleAbc, expected_fields, field_name, \
    DefinitionKind, TypeKind, DiscoveredAbc, DiscoveredClassValue, DiscoveredAbcValue, SimpleAbcValue
from thinking_injection.registry.simple import TypeDescriptor
from thinking_reflection.definitions import TypeDefinition
from thinking_reflection.discovery import discover
from thinking_reflection.interfaces import interface
from thinking_reflection.model.members import FieldDescriptor, MethodDescriptor
from thinking_reflection.model.source_scope import SourceScope, get_source_scope


class Clean: pass

@case
def test_degenerate_type_has_empty_definition():
    d = TypeDefinition.of(Clean)
    assert not d.type_descriptor.fields
    assert not d.type_descriptor.methods

class CompositeType(DiscoveredClass, DiscoveredAbc, SimpleAbc):
    def xyz(self, deadbeef: Optional[str]) -> int: return 0

@case
def test_example_composite_type():
    d = TypeDefinition.of(CompositeType)
    assert d.type_descriptor.fields == frozendict({
        "discovered_class_field": (FieldDescriptor(DiscoveredClassValue, DiscoveredClassValue), ),
        "discovered_abc_field": (FieldDescriptor(DiscoveredAbcValue, DiscoveredAbcValue, ), ),
        "simple_abc_field": (FieldDescriptor(SimpleAbcValue, SimpleAbcValue), ),
        "common_discovered_field": (
            FieldDescriptor(DiscoveredClassValue, DiscoveredClassValue),
            FieldDescriptor(DiscoveredAbcValue, DiscoveredAbcValue)
        ),
        "common_simple_field": (FieldDescriptor(SimpleAbcValue, SimpleAbcValue), ),
        "common_class_field": (FieldDescriptor(DiscoveredClassValue, DiscoveredClassValue), ),
        "common_abc_field": (
            FieldDescriptor(DiscoveredAbcValue, DiscoveredAbcValue),
            FieldDescriptor(SimpleAbcValue, SimpleAbcValue)
        )
    })
    m = d.type_descriptor.methods
    assert isinstance(m, frozendict)
    expected_methods = { #maps name to ordered lists of types in which the methods are declared
        "xyz": [CompositeType],
        "discovered_class_method": [DiscoveredClass],
        "discovered_abc_method": [DiscoveredAbc],
        "simple_abc_method": [SimpleAbc],
        "common_discovered_method": [DiscoveredClass, DiscoveredAbc],
        "common_simple_method": [SimpleAbc],
        "common_class_method": [DiscoveredClass],
        "common_abc_method": [DiscoveredAbc, SimpleAbc]
    }
    assert set(m.keys()) == set(expected_methods.keys())
    for method_name in expected_methods:
        v = m[method_name]
        e = expected_methods[method_name]
        assert isinstance(v, tuple)
        assert len(v) == len(e)
        for m_desc, owner in zip(v, e):
            assert isinstance(m_desc, MethodDescriptor)
            assert m_desc.source_scope in get_source_scope(owner)
            #todo test signatures

#missing: declarations->definitions; adding stuff

if __name__ == "__main__":

    run_current_module()
