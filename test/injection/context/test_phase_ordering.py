from logging import getLogger

from thinking_tests.decorators import case
from thinking_tests.running.start import run_current_module

from thinking_injection.context.configurable.configurator import ContextConfigurator, FallbacksProvider, \
    DefaultPrimaryImplementations, ForcedPrimaryImplementations
from thinking_injection.context.configurable.impl import ConfigurableContext
from thinking_injection.context.configurable.phase import ConfigurationPhase, AddingFallbackImpls, \
    SettingDefaultPrimaries, ForcingPrimaries
from thinking_injection.registry.customizable.customizer import TypeRegistryCustomizer
from thinking_injection.typeset import from_module
from thinking_reflection.discovery import discover
from thinking_reflection.interfaces import ConcreteType, interface

ACCUMULATOR = []

def trace(x):
    _type = type(x)
    ACCUMULATOR.append(_type)

@interface
class I: pass

class T(I): pass

@discover
class EarlyPhase(ConfigurationPhase):
    def __init__(self): pass

    @property
    def name(self) -> str:
        return "early"

    def inject_requirements(self): pass

@discover
class EarlyAction(ContextConfigurator):
    def __init__(self):
        self._phase: EarlyPhase = None

    def configure_context(self, customizer: TypeRegistryCustomizer):
        trace(self)

    def inject_requirements(self, phase: EarlyPhase):
        self._phase = phase

    def phase(self) -> ConfigurationPhase:
        return self._phase

@discover
class AfterFallbacksPhase(ConfigurationPhase):
    def __init__(self): pass

    @property
    def name(self) -> str:
        return "after_fallbacks"

    def inject_requirements(self, fallbacks: AddingFallbackImpls): pass

@discover
class AfterFallbacksAction(ContextConfigurator):
    def __init__(self):
        self._phase: AfterFallbacksPhase = None

    def configure_context(self, customizer: TypeRegistryCustomizer):
        trace(self)

    def inject_requirements(self, phase: AfterFallbacksPhase):
        self._phase = phase

    def phase(self) -> ConfigurationPhase:
        return self._phase

@discover
class AfterDefaultsPhase(ConfigurationPhase):
    def __init__(self): pass

    @property
    def name(self) -> str:
        return "after_defaults"

    def inject_requirements(self, fallbacks: SettingDefaultPrimaries): pass

@discover
class AfterDefaultsAction(ContextConfigurator):
    def __init__(self):
        self._phase: AfterFallbacksPhase = None

    def configure_context(self, customizer: TypeRegistryCustomizer):
        trace(self)

    def inject_requirements(self, phase: AfterDefaultsPhase):
        self._phase = phase

    def phase(self) -> ConfigurationPhase:
        return self._phase

@discover
class AfterDefaultsAndForcingPhase(ConfigurationPhase):
    def __init__(self): pass

    @property
    def name(self) -> str:
        return "after_defaults_and_forcing"

    def inject_requirements(self, fallbacks: SettingDefaultPrimaries, forcing: ForcingPrimaries): pass

@discover
class AfterDefaultsAndForcingAction(ContextConfigurator):
    def __init__(self):
        self._phase: AfterDefaultsAndForcingPhase = None

    def configure_context(self, customizer: TypeRegistryCustomizer):
        trace(self)

    def inject_requirements(self, phase: AfterDefaultsAndForcingPhase):
        self._phase = phase

    def phase(self) -> ConfigurationPhase:
        return self._phase

@discover
class TracingFallbackProvider(FallbacksProvider):
    def fallbacks(self) -> dict[type, ConcreteType]:
        return {I: T}

    def configure_context(self, customizer: TypeRegistryCustomizer):
        trace(self)
        return FallbacksProvider.configure_context(self, customizer)

@discover
class TracingDefaultsProvider(DefaultPrimaryImplementations):
    def primaries(self) -> dict[type, ConcreteType]:
        return {I: T}

    def configure_context(self, customizer: TypeRegistryCustomizer):
        trace(self)
        return DefaultPrimaryImplementations.configure_context(self, customizer)

@discover
class TracingEnforcer(ForcedPrimaryImplementations):
    def forced(self):
        return {I: T}

    def configure_context(self, customizer: TypeRegistryCustomizer):
        trace(self)
        return ForcedPrimaryImplementations.configure_context(self, customizer)

log = getLogger(__name__)

@case
def test_phase_ordering():
    ctx = ConfigurableContext(from_module(__name__))
    with ctx.lifecycle() as index:
        pass
    #order is based on phases order; that in turn is based on dependencies and qualified names ordering;
    # e.g. AddingFallbackImpls is before EarlyPhase even though both are depencyless
    # still, order is deterministic
    assert ACCUMULATOR == [
        TracingFallbackProvider,
        EarlyAction,
        AfterFallbacksAction,
        TracingEnforcer,
        TracingDefaultsProvider,
        AfterDefaultsAndForcingAction,
        AfterDefaultsAction
    ]

if __name__=="__main__":
    run_current_module()