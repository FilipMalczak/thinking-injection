from typing import NamedTuple, Optional

from thinking_injection.typeset import ImmutableTypeSet
from thinking_reflection.interfaces import ConcreteType


#fixme leftover from past implementation; get rid of this
class ImplementationDetails(NamedTuple):
    implementations: ImmutableTypeSet
    primary: Optional[ConcreteType]

    def __str__(self):
        impls = "{" + (", ".join(sorted(x.__name__ for x in self.implementations))) + "}"
        prim = self.primary.__name__ if self.primary is not None else str(None)
        return f"{type(self).__name__}(primary={prim}, implementations={impls})"

    __repr__ = __str__
