from thinking_programming.exceptions import UnreachableInstructionException


class Guard:
    @classmethod
    def _explain(cls):
        UnreachableInstructionException.guard("This type shouldn't be constructed nor subclassed, its only supposed to be used as a magic constant")

    def __init__(self):
        type(self)._explain()

    @classmethod
    def __init_subclass__(cls, **kwargs):
        cls._explain()
