from importlib import import_module

from thinking_modules.definitions import type_
from thinking_modules.model import ModuleName, ModuleNamePointer
from thinking_modules.scan import scan

from thinking_reflection.discovery import DISCOVERED_TYPES

#todo all typesets should be immutable, remove distinction or rename TypeSet to MutableTypeSet + remove Immutable prefix
TypeSet = set[type]
ImmutableTypeSet = frozenset[type]
AnyTypeSet = TypeSet | ImmutableTypeSet


TypeAliasing = dict[type, type]


def types(*t: type) -> TypeSet:
    return set(*t) if t else {}


class InvalidModuleStyleException(Exception):
    def __init__(self, mod_name, should_be_package, is_package):
        self.mod_name = mod_name,
        self.should_be_package = should_be_package
        self.is_package = is_package
        Exception.__init__(self, f"Module {mod_name} should{'' if should_be_package else 'n\'t'} be a package, "
                                 f"but it in fact is{'' if is_package else 'n\'t'}")


def from_package(pkg: ModuleNamePointer) -> TypeSet:
    """
    :raise InvalidModuleStyleException:
    """
    pkg_name = ModuleName.resolve(pkg)
    if not pkg_name.module_descriptor.is_package:
        raise InvalidModuleStyleException(pkg_name, True, False)
    for m in scan(pkg_name):
        m.import_()
    return set(
        t
        for t in DISCOVERED_TYPES
        if type_(t).defined_in_package(pkg_name)
    )


def from_module(mod: ModuleNamePointer) -> TypeSet:
    """
    :raise InvalidModuleStyleException:
    """
    mod_name = ModuleName.resolve(mod)
    if mod_name.module_descriptor.is_package:
        raise InvalidModuleStyleException(mod_name, False, True)
    import_module(mod_name.qualified)
    return set(
        t
        for t in DISCOVERED_TYPES
        if ModuleName.resolve(t) == mod_name
    )


def freeze(types: TypeSet) -> ImmutableTypeSet:
    return frozenset(types)
