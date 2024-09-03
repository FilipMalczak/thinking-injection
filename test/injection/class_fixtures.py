from contextlib import contextmanager
from dataclasses import dataclass
from typing import NamedTuple, Optional, Union

from thinking_injection.injectable import Injectable
from thinking_injection.interfaces import interface
from thinking_injection.lifecycle import HasLifecycle, Initializable


class SimpleClass: pass

class ANamedTuple(NamedTuple):
    x: int
    y: str

@dataclass
class ADataclass:
    x: int
    y: str

class HasLifecycleDuckTyped:
    @contextmanager
    def lifecycle(self):
        yield


class HasLifecycleInheriting(HasLifecycle):
    @contextmanager
    def lifecycle(self):
        yield

class SimpleInitializable(Initializable):
    def initialize(self) -> None: pass

    def deinitialize(self, exc: BaseException | None) -> None: pass










class InjectableNoDeps(Injectable):
    def inject_requirements(self) -> None: pass

class InjectableOneValueDep(Injectable):
    def inject_requirements(self, val: SimpleClass) -> None: pass

class InjectableOneConcreteDep(Injectable):
    def inject_requirements(self, concrete: InjectableNoDeps) -> None: pass

class InjectableTwoConcreteDep(Injectable):
    def inject_requirements(self, concrete1: InjectableNoDeps, concrete2: InjectableOneConcreteDep) -> None: pass






class InjectableOptionalInjectableByTyping(Injectable):
    def inject_requirements(self, optional: Optional[InjectableNoDeps]) -> None: pass

class InjectableOptionalInjectableByOperator(Injectable):
    def inject_requirements(self, optional: InjectableNoDeps | None) -> None: pass


class InjectableOptionalInjectableByUnion(Injectable):
    def inject_requirements(self, optional: Union[InjectableNoDeps, None]) -> None: pass


class InjectableOptionalValueByTyping(Injectable):
    def inject_requirements(self, optional: Optional[SimpleClass]) -> None: pass

class InjectableOptionalValueByOperator(Injectable):
    def inject_requirements(self, optional: SimpleClass | None) -> None: pass


class InjectableOptionalValueByUnion(Injectable):
    def inject_requirements(self, optional: Union[SimpleClass, None]) -> None: pass





@interface
class AnInterface: pass

class Impl1(AnInterface): pass

class Impl2(AnInterface): pass

class Impl11(Impl1): pass


class InjectableCollectiveByInterface(Injectable):
    def inject_requirements(self, x: list[AnInterface]) -> None: pass


class InjectableCollectiveByImpl1(Injectable):
    def inject_requirements(self, x: list[Impl1]) -> None: pass


class InjectableCollectiveByImpl2(Injectable):
    def inject_requirements(self, x: list[Impl2]) -> None: pass


#todo cover defaults
#todo cover kw-only defaults
#todo disallowed varargs and kwargs


class Interesting1(Injectable):
    def inject_requirements(self,
                            a: InjectableNoDeps,
                            b: InjectableOneValueDep | None,
                            c: Impl2,
                            d: AnInterface,
                            e: list[AnInterface],
                            f: list[Impl1]) -> None: pass