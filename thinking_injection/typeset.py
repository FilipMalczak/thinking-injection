from importlib import import_module

from thinking_modules.definitions import type_
from thinking_modules.model import ModuleName, ModuleNamePointer
from thinking_modules.scan import scan

from thinking_injection.discovery import DISCOVERED_TYPES

TypeSet = set[type]
ImmutableTypeSet = frozenset[type]

def types(*t: type) -> TypeSet:
    return set(*t)

def from_package(pkg: ModuleNamePointer) -> TypeSet:
    pkg_name = ModuleName.resolve(pkg)
    assert pkg_name.module_descriptor.is_package#todo msg
    for m in scan(pkg_name):
        m.import_()
    return set(
        t
        for t in DISCOVERED_TYPES
        if type_(t).defined_in_package(pkg_name)
    )

def from_module(mod: ModuleNamePointer) -> TypeSet:
    mod_name = ModuleName.resolve(mod)
    assert not mod_name.module_descriptor.is_package# todo msg
    import_module(mod_name.qualified)
    return set(
        t
        for t in DISCOVERED_TYPES
        if ModuleName.resolve(t) == mod_name
    )

def freeze(types: TypeSet) -> ImmutableTypeSet:
    return frozenset(types)