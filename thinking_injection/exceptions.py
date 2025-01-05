from thinking_programming.exceptions import InvalidStateException
from thinking_reflection.interfaces import is_concrete


class InvalidThinkingStateException(InvalidStateException): pass


class InvalidInternalTypeException(InvalidThinkingStateException):
    def __init__(self, msg: str, instance: object, expected_type: type):
        self.instance: object = instance
        self.expected_type: type = expected_type
        InvalidThinkingStateException.__init__(self, msg)

    @classmethod
    def guard(cls, type_or_instance: object | type, expected_type: type):
        if isinstance(type_or_instance, type):
            if not issubclass(type_or_instance, expected_type):
                raise cls(f"Type {type_or_instance} is supposed to a subclass of {expected_type}", type_or_instance, expected_type)
        else:
            if not isinstance(type_or_instance, expected_type):
                raise cls(f"Object {type_or_instance} was supposed to an instance of {expected_type}", type_or_instance, expected_type)


class ConcreteTypeExpectedException(InvalidThinkingStateException):
    def __init__(self, subject: type):
        self.subject = subject
        InvalidThinkingStateException.__init__(self, f"Type {subject} is expected to be a concrete type; is an interface instead")

    @classmethod
    def guard(cls, subject: type):
        if not is_concrete(subject):
            raise cls(subject)


class InvalidInjectionPointException(InvalidThinkingStateException):
    issues: tuple[str, ...]
