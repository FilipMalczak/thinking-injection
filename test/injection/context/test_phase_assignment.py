from thinking_tests.decorators import case
from thinking_tests.running.start import run_current_module

from thinking_injection.context.configurable.configurator import ContextConfigurator, specialized_configurator
from thinking_injection.context.configurable.impl import ConfigurableContext
from thinking_injection.context.configurable.phase import ConfigurationPhase
from thinking_reflection.interfaces import interface
from thinking_injection.registry.customizable.customizer import TypeRegistryCustomizer


class SpecialPhase(ConfigurationPhase):
    def __init__(self): pass

    @property
    def name(self) -> str:
        return "special"

    def inject_requirements(self): pass

class AnotherPhase(ConfigurationPhase):
    def __init__(self): pass

    @property
    def name(self) -> str:
        return "another"

    def inject_requirements(self): pass


@interface
@specialized_configurator(SpecialPhase)
class SpecialConfigurator(ContextConfigurator):
    def __init__(self):
        self._phase: SpecialPhase = None

    def configure_context(self, customizer: TypeRegistryCustomizer): pass

    def inject_requirements(self, phase: SpecialPhase):
        self._phase = phase

    def phase(self) -> ConfigurationPhase:
        return self._phase

class CorrectSpecialConfigurator(SpecialConfigurator):
    pass # don't change the phase, let it be the required one

class BrokenSpecialConfigurator(SpecialConfigurator):
    def inject_requirements(self, phase: AnotherPhase):
        self._phase = phase

class NotSpecialButInSpecialPhaseConfigurator(ContextConfigurator):
    def __init__(self):
        self._phase: SpecialPhase = None

    def configure_context(self, customizer: TypeRegistryCustomizer): pass

    def inject_requirements(self, phase: SpecialPhase):
        self._phase = phase

    def phase(self) -> ConfigurationPhase:
        return self._phase

@case
def test_specialized_configurator_works_with_correct_phase():
    ctx = ConfigurableContext([SpecialPhase, AnotherPhase, SpecialConfigurator, CorrectSpecialConfigurator])
    with ctx.lifecycle() as index:
        pass #no assertion, this simply should work

@case
def test_specialized_configurator_fails_if_phase_mismatched():
    ctx = ConfigurableContext([SpecialPhase, AnotherPhase, SpecialConfigurator, BrokenSpecialConfigurator])
    reached = False
    exc = None
    try:
        with ctx.lifecycle() as index:
            reached = True
    except BaseException as e:
        exc = e
    assert not reached
    assert exc is not None #fixme this pattern is copied from test_configurable_context; refactor, check exc type

@case
def test_non_specialized_configurator_in_specialized_phase():
    ctx = ConfigurableContext([SpecialPhase, AnotherPhase, SpecialConfigurator, NotSpecialButInSpecialPhaseConfigurator])
    with ctx.lifecycle() as index:
        pass  # no assertion, this simply should work

if __name__=="__main__":
    run_current_module()