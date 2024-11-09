from thinking_types.discovery import discover
from thinking_injection.injectable import Injectable
from thinking_types.interfaces import interface


@discover
class Discovered: pass


class Undiscovered: pass


class AnInjectable(Injectable):
    def inject_requirements(self) -> None: pass


@interface
class AnInterface: pass