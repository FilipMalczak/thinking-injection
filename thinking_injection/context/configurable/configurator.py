from typing import Protocol, runtime_checkable, Callable

from thinking_injection.registry.customizable.customizer import TypeRegistryCustomizer
from thinking_injection.context.configurable.phase import ConfigurationPhase


@runtime_checkable
class ContextConfigurator(Protocol):
    #name is a mouthful, but since its a protocol, we don't want simple configure() (that can be used in other context)
    # to clash with this
    def configure_context(self, customizer: TypeRegistryCustomizer): pass

    def phase(self) -> ConfigurationPhase: pass


SPECIALIZED_CONFIGURATOR_PHASES: dict[type, type[ConfigurationPhase]] = {}


def specialized_configurator[T: type[ContextConfigurator]](p: type[ConfigurationPhase]) -> Callable[[T], T]:
    def register(t: T) -> T:
        assert t not in SPECIALIZED_CONFIGURATOR_PHASES #todo msg
        SPECIALIZED_CONFIGURATOR_PHASES[t] = p
        return t
    return register


def declares_allowed_phase(configurator: ContextConfigurator) -> bool:
    for c, p in SPECIALIZED_CONFIGURATOR_PHASES.items():
        if isinstance(configurator, c):
            if configurator.phase() != p:
                return False
    return True

#todo specialized configurators, like "add fallback" or "force impl"