from abc import ABC, abstractmethod

from thinking_injection.discovery import discover
from thinking_injection.injectable import Injectable
from thinking_injection.interfaces import interface


@interface
class ConfigurationPhase(Injectable, ABC):
    @property
    @abstractmethod
    def name(self) -> str: pass

    def __str__(self):
        return type(self).__name__

    def __repr__(self):
        return f"ConfigurationPhase[{type(self).__name__}]"


@discover
class AddingFallbackImpls(ConfigurationPhase):
    def __init__(self): pass

    @property
    def name(self) -> str:
        return "fallbacks"

    def inject_requirements(self): pass


@discover
class SettingDefaultPrimaries(ConfigurationPhase):
    def __init__(self): pass

    @property
    def name(self) -> str:
        return "defaults"

    def inject_requirements(self, phase: AddingFallbackImpls): pass


@discover
class ForcingPrimaries(ConfigurationPhase):
    def __init__(self): pass

    @property
    def name(self) -> str:
        return "forcing"

    def inject_requirements(self, phase: AddingFallbackImpls): pass
