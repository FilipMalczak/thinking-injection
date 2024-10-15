from typing import Protocol, Self, NamedTuple

from thinking_injection.discovery import discover
from thinking_injection.injectable import Injectable
from thinking_injection.interfaces import interface


@interface
class ConfigurationPhase(Injectable, Protocol):
    @property
    def name(self) -> str: pass



@discover
class AddingFallbackImpls(ConfigurationPhase):
    @property
    def name(self) -> str:
        return "fallbacks"

    def inject_requirements(self): pass


@discover
class SettingDefaultPrimaries:
    @property
    def name(self) -> str:
        return "defaults"

    def inject_requirements(self, phase: AddingFallbackImpls): pass


@discover
class ForcingPrimaries:
    @property
    def name(self) -> str:
        return "forcing"

    def inject_requirements(self, phase: AddingFallbackImpls): pass
