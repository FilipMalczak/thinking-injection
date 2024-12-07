from abc import ABC, abstractmethod
from enum import Enum, auto
from logging import getLogger
from types import NoneType
from typing import Protocol, Optional

from frozendict import frozendict
from thinking_tests.decorators import case
from thinking_tests.running.start import run_current_module

from test.util import parametrized_case
from thinking_reflection.definitions import TypeDefinition
from thinking_reflection.discovery import discover
from thinking_reflection.interfaces import interface
from thinking_reflection.model.members import FieldDescriptor, MethodDescriptor
from thinking_reflection.model.source_scope import get_source_scope

log = getLogger(__name__)

class DefinitionKind(Enum):
    SIMPLE = "simple"
    INTERFACE = "interface"
    DISCOVERED = "discovered"

class TypeKind(Enum):
    CLASS = "class"
    PROTOCOL = "protocol"
    ABC = "abc"

def all_combinations():
    for d in DefinitionKind:
        for t in TypeKind:
            yield (d, t)

def _name(d, t):
    if d and t:
        return f"{d.value}_{t.value}"
    x = d or t
    assert x
    return f"common_{x.value}"

def field_name(d, t):
    return _name(d, t)+"_field"

def method_name(d, t):
    return _name(d, t)+"_method"

def value_type_name(d, t):
    return f"{d.value.capitalize()}{t.value.capitalize()}Value"

def fixture_type_name(d, t):
    return f"{d.value.capitalize()}{t.value.capitalize()}"

def value_type(d, t):
    return globals()[value_type_name(d, t)]

def fixture_type(d, t):
    return globals()[fixture_type_name(d, t)]

#use the following snippet to regenerate sources for the classes in this file
# for d, t in all_combinations():
#     print(f"class {value_type_name(d, t)}: pass")
#     print()
#     print()
#     prefix = "" if d == DefinitionKind.SIMPLE else ("@discover\n" if d == DefinitionKind.DISCOVERED else "@interface\n")
#     extends = "" if t == TypeKind.CLASS else ("(ABC)" if t == TypeKind.ABC else "(Protocol)")
#     fields = ""
#     methods = ""
#     for (a,b) in [(d, t), (d, None), (None, t)]:
#         fields += f"    {field_name(a, b)}: {value_type_name(d, t)}\n"
#         methods += f"    def {method_name(a, b)}(self) -> str:\n        return str(self.{field_name(a, b)})\n\n"
#     print(f"""{prefix}class {fixture_type_name(d, t)}{extends}:
# {fields}
# {methods}""")


def expected_fields(*names: str) -> frozendict[str, tuple[FieldDescriptor, ...]]:
    return frozendict({
        n: (FieldDescriptor(int, int), )
        for n in names
    })

###################################################
#
#   GENERATED TYPES: START
#
###################################################

class SimpleClassValue: pass


class SimpleClass:
    simple_class_field: SimpleClassValue
    common_simple_field: SimpleClassValue
    common_class_field: SimpleClassValue

    def simple_class_method(self) -> str:
        return str(self.simple_class_field)

    def common_simple_method(self) -> str:
        return str(self.common_simple_field)

    def common_class_method(self) -> str:
        return str(self.common_class_field)


class SimpleProtocolValue: pass


class SimpleProtocol(Protocol):
    simple_protocol_field: SimpleProtocolValue
    common_simple_field: SimpleProtocolValue
    common_protocol_field: SimpleProtocolValue

    def simple_protocol_method(self) -> str:
        return str(self.simple_protocol_field)

    def common_simple_method(self) -> str:
        return str(self.common_simple_field)

    def common_protocol_method(self) -> str:
        return str(self.common_protocol_field)


class SimpleAbcValue: pass


class SimpleAbc(ABC):
    simple_abc_field: SimpleAbcValue
    common_simple_field: SimpleAbcValue
    common_abc_field: SimpleAbcValue

    def simple_abc_method(self) -> str:
        return str(self.simple_abc_field)

    def common_simple_method(self) -> str:
        return str(self.common_simple_field)

    def common_abc_method(self) -> str:
        return str(self.common_abc_field)


class InterfaceClassValue: pass


@interface
class InterfaceClass:
    interface_class_field: InterfaceClassValue
    common_interface_field: InterfaceClassValue
    common_class_field: InterfaceClassValue

    def interface_class_method(self) -> str:
        return str(self.interface_class_field)

    def common_interface_method(self) -> str:
        return str(self.common_interface_field)

    def common_class_method(self) -> str:
        return str(self.common_class_field)


class InterfaceProtocolValue: pass


@interface
class InterfaceProtocol(Protocol):
    interface_protocol_field: InterfaceProtocolValue
    common_interface_field: InterfaceProtocolValue
    common_protocol_field: InterfaceProtocolValue

    def interface_protocol_method(self) -> str:
        return str(self.interface_protocol_field)

    def common_interface_method(self) -> str:
        return str(self.common_interface_field)

    def common_protocol_method(self) -> str:
        return str(self.common_protocol_field)


class InterfaceAbcValue: pass


@interface
class InterfaceAbc(ABC):
    interface_abc_field: InterfaceAbcValue
    common_interface_field: InterfaceAbcValue
    common_abc_field: InterfaceAbcValue

    def interface_abc_method(self) -> str:
        return str(self.interface_abc_field)

    def common_interface_method(self) -> str:
        return str(self.common_interface_field)

    def common_abc_method(self) -> str:
        return str(self.common_abc_field)


class DiscoveredClassValue: pass


@discover
class DiscoveredClass:
    discovered_class_field: DiscoveredClassValue
    common_discovered_field: DiscoveredClassValue
    common_class_field: DiscoveredClassValue

    def discovered_class_method(self) -> str:
        return str(self.discovered_class_field)

    def common_discovered_method(self) -> str:
        return str(self.common_discovered_field)

    def common_class_method(self) -> str:
        return str(self.common_class_field)


class DiscoveredProtocolValue: pass


@discover
class DiscoveredProtocol(Protocol):
    discovered_protocol_field: DiscoveredProtocolValue
    common_discovered_field: DiscoveredProtocolValue
    common_protocol_field: DiscoveredProtocolValue

    def discovered_protocol_method(self) -> str:
        return str(self.discovered_protocol_field)

    def common_discovered_method(self) -> str:
        return str(self.common_discovered_field)

    def common_protocol_method(self) -> str:
        return str(self.common_protocol_field)


class DiscoveredAbcValue: pass


@discover
class DiscoveredAbc(ABC):
    discovered_abc_field: DiscoveredAbcValue
    common_discovered_field: DiscoveredAbcValue
    common_abc_field: DiscoveredAbcValue

    def discovered_abc_method(self) -> str:
        return str(self.discovered_abc_field)

    def common_discovered_method(self) -> str:
        return str(self.common_discovered_field)

    def common_abc_method(self) -> str:
        return str(self.common_abc_field)

###################################################
#
#   GENERATED TYPES: END
#
###################################################

@interface
class StructuralSupertype(Protocol):
    def structural_foo(self) -> None: ...


for combination in all_combinations():
    @parametrized_case(f"Definitions of fixture types should be correct", params=combination)
    def test_fixture_definition(d, t):
        fixture = fixture_type(d, t)
        log.info(f"D: {d} T: {t} F: {fixture.__name__}")
        definition = TypeDefinition.of(fixture)
        val_type = value_type(d, t)
        field_desc = FieldDescriptor(val_type, val_type)
        assert definition.type_descriptor.fields == frozendict({
            field_name(d, t): (field_desc, ),
            field_name(None, t): (field_desc, ),
            field_name(d, None): (field_desc, )
        })
        m = definition.type_descriptor.methods
        assert isinstance(m, frozendict)
        expected_method_names = { method_name(d, t), method_name(None, t), method_name(d, None) }
        assert set(m.keys()) == expected_method_names
        for m_name in expected_method_names:
            v = m[m_name]
            assert isinstance(v, tuple)
            assert len(v) == 1
            assert isinstance(v[0], MethodDescriptor)
            assert v[0].source_scope in get_source_scope(fixture)
            assert set(v[0].signature.parameters.keys()) == {'self'}
            assert v[0].signature.return_annotation == str


    @parametrized_case(f"Definitions of types extending single fixture should be correct", params=combination)
    def test_subclass_definition(d, t):
        fixture = fixture_type(d, t)

        class TestedType(fixture):
            # suffix 123 is there so that protocols from other tests don't collide with these tests
            x123: bool

            def foo123(self, bar: set) -> list: ...

        definition = TypeDefinition.of(TestedType)

        val_type = value_type(d, t)
        fixture_field_desc = FieldDescriptor(val_type, val_type)
        assert definition.type_descriptor.fields == frozendict({
            "x123": (FieldDescriptor(bool, bool), ),
            field_name(d, t): (fixture_field_desc,),
            field_name(None, t): (fixture_field_desc,),
            field_name(d, None): (fixture_field_desc,)
        })
        m = definition.type_descriptor.methods
        assert isinstance(m, frozendict)
        expected_method_names = {"foo123", method_name(d, t), method_name(None, t), method_name(d, None)}
        assert set(m.keys()) == expected_method_names
        for m_name in expected_method_names:
            v = m[m_name]
            assert isinstance(v, tuple)
            try:
                assert len(v) == 1
            except:
                raise
            assert isinstance(v[0], MethodDescriptor)
            v = v[0]
            if m_name == "foo123":
                assert v.source_scope in get_source_scope(TestedType)
                assert set(v.signature.parameters.keys()) == {'self', "bar"}
                #todo test bar annotation
                assert v.signature.return_annotation == list
            else:
                assert v.source_scope in get_source_scope(fixture)
                assert set(v.signature.parameters.keys()) == {'self'}
                assert v.signature.return_annotation == str


    #todo ditto, but for 2 nominal supertypes
    @parametrized_case(f"Definitions of types extending single fixture and the structural protocol should be correct", params=combination)
    def test_structural_subclass_definition(d, t):
        fixture = fixture_type(d, t)

        class TestedType(fixture):
            # suffix 123 is there so that protocols from other tests don't collide with these tests
            x123: bool

            def foo123(self, bar: set) -> list: ...

            def structural_foo(self, struct: int) -> str: ...

        definition = TypeDefinition.of(TestedType)

        val_type = value_type(d, t)
        fixture_field_desc = FieldDescriptor(val_type, val_type)
        assert definition.type_descriptor.fields == frozendict({
            "x123": (FieldDescriptor(bool, bool),),
            field_name(d, t): (fixture_field_desc,),
            field_name(None, t): (fixture_field_desc,),
            field_name(d, None): (fixture_field_desc,)
        })
        m = definition.type_descriptor.methods
        assert isinstance(m, frozendict)
        expected_method_names = {
            "foo123",
            method_name(d, t), method_name(None, t), method_name(d, None),
            "structural_foo"
        }
        assert set(m.keys()) == expected_method_names
        for m_name in expected_method_names:
            v = m[m_name]
            assert isinstance(v, tuple)
            if m_name == "structural_foo":
                assert len(v) == 2
                assert v[0].source_scope in get_source_scope(TestedType)
                assert set(v[0].signature.parameters.keys()) == {'self', "struct"}
                #todo test struct annotation is int
                assert v[0].signature.return_annotation == str
                assert v[1].source_scope in get_source_scope(StructuralSupertype)
                assert set(v[1].signature.parameters.keys()) == {'self'}
                assert v[1].signature.return_annotation == NoneType
            else:
                assert len(v) == 1
                assert isinstance(v[0], MethodDescriptor)
                v = v[0]
                if m_name == "foo123":
                    assert v.source_scope in get_source_scope(TestedType)
                    assert set(v.signature.parameters.keys()) == {'self', "bar"}
                    # todo test bar annotation is set
                    assert v.signature.return_annotation == list
                else:
                    assert v.source_scope in get_source_scope(fixture)
                    assert set(v.signature.parameters.keys()) == {'self'}
                    assert v.signature.return_annotation == str

    for another in all_combinations():
        if another != combination:
            @parametrized_case("Definitions of types extending two fixtures should be correct", params=combination+another)
            def test_subclass_w_multiple_superclasses_definition(d, t, dd, tt):
                fixture1 = fixture_type(d, t)
                fixture2 = fixture_type(dd, tt)
                class TestedType(fixture1, fixture2):
                    y123: str

                    def baz123(self, xyz: int, abc: bool) -> set: ...

                definition = TypeDefinition.of(TestedType)

                val_type1 = value_type(d, t)
                val_type2 = value_type(dd, tt)
                fixture_field_desc1 = FieldDescriptor(val_type1, val_type1)
                fixture_field_desc2 = FieldDescriptor(val_type2, val_type2)
                field_expectations = {
                    "y123": (FieldDescriptor(str, str), )
                }
                def _put(k, v):
                    if k in field_expectations:
                        field_expectations[k] += (v, )
                    else:
                        field_expectations[k] = (v, )
                _put(field_name(d, t), fixture_field_desc1)
                _put(field_name(d, None), fixture_field_desc1)
                _put(field_name(None, t), fixture_field_desc1)
                _put(field_name(dd, tt), fixture_field_desc2)
                _put(field_name(dd, None), fixture_field_desc2)
                _put(field_name(None, tt), fixture_field_desc2)
                assert definition.type_descriptor.fields == frozendict(field_expectations)
                m = definition.type_descriptor.methods
                assert isinstance(m, frozendict)
                method_expectations = {} # maps method name to list of types where they were declared
                def _put(k, v):
                    if k in method_expectations:
                        method_expectations[k] += [ v ]
                    else:
                        method_expectations[k] = [v]
                _put("baz123", TestedType)
                _put(method_name(d, t), fixture1)
                _put(method_name(d, None), fixture1)
                _put(method_name(None, t), fixture1)
                _put(method_name(dd, tt), fixture2)
                _put(method_name(dd, None), fixture2)
                _put(method_name(None, tt), fixture2)
                assert set(m.keys()) == set(method_expectations.keys())
                for m_name, declaration_sites in method_expectations.items():
                    v = m[m_name]
                    assert isinstance(v, tuple)
                    assert len(v) == len(declaration_sites)
                    assert all(isinstance(x, MethodDescriptor) for x in v)
                    for desc, site in zip(v, declaration_sites):
                        assert desc.source_scope in get_source_scope(site)
                        if m_name == "baz123":
                            assert set(desc.signature.parameters.keys()) == {'self', "xyz", "abc"}
                            # todo test param annotations
                            assert desc.signature.return_annotation == set
                        else:
                            assert set(desc.signature.parameters.keys()) == {'self'}
                            assert desc.signature.return_annotation == str




if __name__ == "__main__":
    run_current_module()