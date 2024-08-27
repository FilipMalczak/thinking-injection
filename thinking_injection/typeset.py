from importlib import import_module

from recursive_import import import_package_recursively
from thinking_runtime.modules import ModulePointer, resolve_module_name, ModuleName

from thinking_injection.discovery import DISCOVERED_TYPES

TypeSet = set[type]
ImmutableTypeSet = frozenset[type]

def types(*t: type) -> TypeSet:
    return set(*t)

#todo extract to runtime
def declaring_module_name(x: object) -> ModuleName:
    return resolve_module_name(x.__module__)

#todo ditto
def is_ancestor(child: ModuleName, ancestor: ModuleName) -> bool:
    #todo ModuleName.__len__
    return len(child.parts) > len(ancestor.parts) and ancestor.parts[:len(child.parts)] == child.parts

#todo ditto
def is_in_pkg(x: object, pkg_name: ModuleName) -> bool:
    mod_name = resolve_module_name(x)
    return is_ancestor(mod_name, pkg_name) or mod_name == pkg_name

def from_package(pkg: ModulePointer) -> TypeSet:
    pkg_name = resolve_module_name(pkg)
    assert pkg_name.is_package#todo msg
    import_package_recursively(pkg_name.quailified)
    return set(
        t
        for t in DISCOVERED_TYPES
        if is_in_pkg(t, pkg_name)
    )

def from_module(mod: ModulePointer) -> TypeSet:
    mod_name = resolve_module_name(mod)
    assert not mod_name.is_package# todo msg
    import_module(mod.quailified)
    return set(
        t
        for t in DISCOVERED_TYPES
        if resolve_module_name(t) == mod_name
    )

def freeze(types: TypeSet) -> ImmutableTypeSet:
    return frozenset(types)