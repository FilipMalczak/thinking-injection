from enum import Enum, auto
from typing import Protocol, NamedTuple

from thinking_injection.injectable import Injectable
from thinking_reflection.discovery import discover
from thinking_reflection.interfaces import interface

class MountMode(Enum):
    RO = auto()
    RW = auto()

Path = str

class Mount(NamedTuple):
    path: Path
    mode: MountMode

Volumes = dict[Path, Mount]

Port = int #todo some constraints maybe?

Ports = dict[Port, Port]

class ContainerStatus(Enum):
    #todo STARTING?
    RUNNING = auto()
    FINISHED = auto()

class Container(Protocol):
    name: str
    image: str
    volumes: Volumes
    ports: Ports

    status: ContainerStatus

    def stop(self):
        """
        Should be blocking and idempotent. TBD about exit codes and whatnot.
        """


@interface
class ContainerClient[C: Container](Protocol):
    def run(self, img: str, *, name: str = None, cmd: str = None, volumes: Volumes = None, ports: Ports = None) -> C: ...

@interface
class ContainerClientFactory[Client: ContainerClient](Protocol):
    def client(self) -> Client: ...


@discover
class DockerClientProxy(ContainerClient, Injectable):
    def __init__(self):
        self.delegate: ContainerClient = None

    def inject_requirements(self, factory: ContainerClientFactory):
        self.delegate = factory.client()

    def run(self, img: str, *, name: str = None, cmd: str = None, volumes: Volumes = None, ports: Ports = None) -> Container:
        return self.delegate.run(img, name=name, cmd=cmd, volumes=volumes, ports=ports)
