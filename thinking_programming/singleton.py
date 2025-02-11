class NastySingleton:
    def __new__(cls, *args, **kwargs):
        try:
            return cls.__instance__
        except AttributeError:
            cls.__instance__ = object.__new__(cls, *args, **kwargs)
            return cls.__instance__

#todo extract test
class X(NastySingleton): pass

assert X() is X()
