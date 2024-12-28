from abc import ABC, abstractmethod
from typing import Callable, Optional

from thinking_injection.context.configurable.phase import ConfigurationPhase, AddingFallbackImpls, \
    SettingDefaultPrimaries, ForcingPrimaries
from thinking_injection.injectable import Injectable
from thinking_injection.registry.customizable.customizer import TypeRegistryCustomizer
from thinking_reflection.interfaces import interface, ConcreteType


@interface
class ContextConfigurator(Injectable, ABC):
    #name is a mouthful, but since its a protocol, we don't want simple configure() (that can be used in other context)
    # to clash with this
    @abstractmethod
    def configure_context(self, customizer: TypeRegistryCustomizer): pass

    @abstractmethod
    def phase(self) -> ConfigurationPhase: pass


SPECIALIZED_CONFIGURATOR_PHASES: dict[type, type[ConfigurationPhase]] = {}


def specialized_configurator[T: type[ContextConfigurator]](p: type[ConfigurationPhase]) -> Callable[[T], T]:
    def register(t: T) -> T:
        assert issubclass(t, ContextConfigurator) #ignore IDE warning, any @interface is @runtime_checkable
        assert t not in SPECIALIZED_CONFIGURATOR_PHASES #todo msg
        SPECIALIZED_CONFIGURATOR_PHASES[t] = p
        return t
    return register


def required_phase(configurator: ContextConfigurator) -> Optional[type[ConfigurationPhase]]:
    for c, p in SPECIALIZED_CONFIGURATOR_PHASES.items():
        # fixme not a clue why isinstance won't work here
        if issubclass(type(configurator), c):
            return p
    return None


def declares_allowed_phase(configurator: ContextConfigurator) -> bool:
    required = required_phase(configurator)
    if required is None:
        return True
    # fixme not a clue why isinstance won't work here
    return issubclass(type(configurator.phase()), required)


@interface
@specialized_configurator(AddingFallbackImpls)
class FallbacksProvider(ContextConfigurator):
    def __init__(self):
        self._phase: AddingFallbackImpls = None

    @abstractmethod
    def fallbacks(self) -> dict[type, ConcreteType]: pass

    def configure_context(self, customizer: TypeRegistryCustomizer):
        fallbacks = self.fallbacks()
        assert fallbacks #todo msg; assert is type mapping
        for i, impl in fallbacks.items():
            if not customizer.implementations[i].all:
                customizer.register(impl)

    def inject_requirements(self, phase: AddingFallbackImpls):
        self._phase = phase

    def phase(self) -> ConfigurationPhase:
        return self._phase


@interface
@specialized_configurator(SettingDefaultPrimaries)
class DefaultPrimaryImplementations(ContextConfigurator):
    def __init__(self):
        self._phase: SettingDefaultPrimaries = None

    @abstractmethod
    def primaries(self) -> dict[type, ConcreteType]: pass

    def configure_context(self, customizer: TypeRegistryCustomizer):
        primaries = self.primaries()
        assert primaries  # todo msg; assert is type mapping
        for t, impl in primaries.items():
            impls = customizer.implementations[t]
            if impls.primary is None and len(impls.all) > 1:
                assert impl in impls.all #todo msg; there's a test for this, remember when you're creating dedicated exceptions
                customizer.implementations[t].primary = impl

    def inject_requirements(self, phase: SettingDefaultPrimaries):
        self._phase = phase

    def phase(self) -> ConfigurationPhase:
        return self._phase


@interface
@specialized_configurator(ForcingPrimaries)
class ForcedPrimaryImplementations(ContextConfigurator):
    def __init__(self):
        self._phase: ForcingPrimaries = None

    @abstractmethod
    def forced(self) -> dict[type, ConcreteType]: pass

    def configure_context(self, customizer: TypeRegistryCustomizer):
        forced = self.forced()
        assert forced  # todo msg; assert is type mapping
        for t, impl in forced.items():
            impls = customizer.implementations[t]
            if impl not in impls.all:
                customizer.register(impl)
            impls.primary = impl

    def inject_requirements(self, phase: ForcingPrimaries):
        self._phase = phase

    def phase(self) -> ConfigurationPhase:
        return self._phase

#todo tests that check that fallbacks/defaults/forced return sane values
