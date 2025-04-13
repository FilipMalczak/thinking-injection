from enum import Enum, auto
from logging import getLogger
from typing import Protocol, NamedTuple

from thinking_injection.injectable import Injectable
from thinking_programming.guard import Guard
from thinking_programming.readwrite import ReadWrite
from thinking_reflection.discovery import discover
from thinking_reflection.interfaces import interface
from thinking_services.logs import LogConsumer

log = getLogger(__name__)


Path = str

class LocalVolume(NamedTuple):
    host_path: str

class NamedVolume(NamedTuple):
    volume_name: str

VolumeDefinition = LocalVolume | NamedVolume

ContainerPath = Path

class HostMount(NamedTuple):
    definition: VolumeDefinition
    mode: ReadWrite = ReadWrite.RW

Volumes = dict[ContainerPath, HostMount]

Port = int #todo some constraints maybe?
ContainerPort = Port
HostPort = Port

Ports = dict[ContainerPort, HostPort]

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

    def stop(self): #todo return ContainerExit which should be a daemon thread (so, it can be joined) and have exit_code property
        """
        Should be blocking and idempotent. TBD about exit codes and whatnot.
        """

class VolumesClient(Protocol):
    def create(self, name: str) -> NamedVolume: ... #todo what should happen if already exists?

    def exists(self, name: str) -> bool: ...

    def delete(self, name: str): ... #todo what should happen if doesnt exist? define a specialized exception

    def __getitem__(self, item: str) -> NamedVolume:
        if not self.exists(item):
            log.debug(f"Volume {item} doesn't exist, creating it")
            return self.create(item)
        else:
            log.debug(f"Volume {item} already exists")
        return NamedVolume(item)

    def __contains__(self, item: str | NamedVolume) -> bool:
        if isinstance(item, NamedVolume):
            item = item.volume_name
        result = self.exists(item)
        return result

    def __delitem__(self, key: str):
        self.delete(key)

#todo only run is tested
@interface
class ContainerClient[C: Container](Protocol):
    def build(self, dir: str, filename: str, name: str, tag: str = "latest", overwrite: bool=False): ...

    def run(self, img: str, *, name: str = None, cmd: str = None, volumes: Volumes = None, ports: Ports = None, envvars: dict[str, str | int] = None) -> C:
        """
        Ports and volumes have keys inside the container and value referring to the host.
        """

    def volumes(self) -> VolumesClient: ...

@interface
class ContainerClientFactory[Client: ContainerClient](Protocol):
    def client(self) -> Client: ...


@discover
class ContainerClientProxy(ContainerClient, Injectable):
    def __init__(self):
        self.delegate: ContainerClient = None

    def inject_requirements(self, factory: ContainerClientFactory):
        self.delegate = factory.client()

    def build(self, dir: str, filename: str, name: str, tag: str = "latest",
              overwrite: bool = False, log_consumer: LogConsumer = Guard):
        return self.delegate.build(dir, filename, name, tag, overwrite)

    def run(self, img: str, *, name: str = None, cmd: str = None, volumes: Volumes = None, ports: Ports = None, envvars: dict[str, str] = None) -> Container:
        return self.delegate.run(img, name=name, cmd=cmd, volumes=volumes, ports=ports)

    def volumes(self) -> VolumesClient:
        return self.delegate.volumes()