from thinking_injection.injectable import Injectable
from thinking_reflection.discovery import discover
from thinking_reflection.interfaces import interface


@discover
class Discovered: pass


class Undiscovered: pass


class AnInjectable(Injectable):
    def inject_requirements(self) -> None: pass


@interface
class AnInterface: pass