
INTERFACES: set[type] = set()

def interface[T: type](t: T) -> T:
    INTERFACES.add(t)
    return t

def is_interface[T: type](t: T) -> bool:
    return t in INTERFACES


def is_concrete[T: type](t: T) -> bool:
    return not is_interface(t)


class InterfaceMeta(type):
    @classmethod
    def __subclasscheck__(cls, subclass):
        return is_interface(subclass)


class Interface(metaclass=InterfaceMeta): pass

class InterfaceTypeMeta(type):
    @classmethod
    def __instancecheck__(self, instance):
        return isinstance(instance, type) and is_interface(instance)


class InterfaceType(type, metaclass=InterfaceTypeMeta): pass


class ConcreteClassMeta(type):
    @classmethod
    def __subclasscheck__(cls, subclass):
        return is_concrete(subclass)

class ConcreteClass(metaclass=ConcreteClassMeta): pass


class ConcreteTypeMeta(type):
    @classmethod
    def __instancecheck__(self, instance):
        return isinstance(instance, type) and is_concrete(instance)

class ConcreteType(type, metaclass=ConcreteTypeMeta): pass

AnyType = InterfaceType | ConcreteType

class X: pass


assert is_concrete(X)
assert issubclass(X, ConcreteClass)
assert isinstance(X, ConcreteType)

@interface
class I: pass

assert is_interface(I)
assert issubclass(I, Interface)
assert isinstance(I, InterfaceType)
#todo extract tests
