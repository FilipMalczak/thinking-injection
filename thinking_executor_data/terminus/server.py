from collections import defaultdict
from logging import getLogger
from os.path import abspath, join
from random import randint
from time import sleep
from typing import NamedTuple, Protocol

from thinking_runtime.defaults.recognise_runtime import current_runtime, RuntimeMode
from thinking_tests.current import current_case_id

from thinking_services.containers.protocol import Container, ContainerClient, HostMount, VolumeDefinition, LocalVolume, NamedVolume
from thinking_executor.data.persistence import ProjectPersistenceDirectoryProvider
from thinking_injection.injectable import Injectable
from thinking_programming.names import make_uuid
from thinking_reflection.discovery import discover
from thinking_reflection.interfaces import interface


#todo this is pretty reusable; shouldn't be in server nor in client; can be used for other technologies too
class Credentials(NamedTuple):
    username: str
    password: str

class TerminusContainerConfig(NamedTuple):
    storage: VolumeDefinition
    localhost_port: int = 6363
    admin: Credentials = Credentials("admin", "root")
    image: str = "terminusdb/terminusdb-server:latest"

@interface
class TerminusContainerConfigFactory(Protocol):
    def get_terminus_container_config(self) -> TerminusContainerConfig: ...

#todo create ...Customizer that provides port, admin pass and image (optionals); make it optional dependency for the factory impl

if current_runtime().mode == RuntimeMode.APP:
    @discover
    class DefaultTerminusContainerConfigFactory(Injectable, TerminusContainerConfigFactory):
        def __init__(self):
            self.data_dir: str = None

        def inject_requirements(self, persistence: ProjectPersistenceDirectoryProvider) -> None:
            self.data_dir = abspath(join(persistence.project_data_dir(), "terminusdb"))

        def get_terminus_container_config(self) -> TerminusContainerConfig:
            return TerminusContainerConfig(
                LocalVolume(self.data_dir)
            )
else:
    log = getLogger(__name__)

    @discover
    class TestTerminusContainerConfigFactory(Injectable, TerminusContainerConfigFactory):
        _CLEANED: dict[str, bool] = defaultdict(lambda: False)

        def __init__(self):
            self.named_volume: NamedVolume = None
            self.local_port: int = None
            self.client: ContainerClient = None

        def inject_requirements(self, client: ContainerClient) -> None:
            self.client = client

        def initialize(self) -> None:
            volume_name = make_uuid("TerminusDbVolume", current_case_id())
            log.debug(f"Volume name for case '{current_case_id()}' is {volume_name}")
            if not self._CLEANED[volume_name]:
                log.debug(f"Volume {volume_name} not cleaned in this runtime yet")
                vol_in = volume_name in self.client.volumes()
                if vol_in:
                    log.debug("Volume already present, removing it")
                    del self.client.volumes()[volume_name]
                else:
                    log.debug(f"Volume {volume_name} doesn't need cleaning")
                self._CLEANED[volume_name] = True
            else:
                log.debug(f"Volume {volume_name} already cleaned in this runtime")
            self.named_volume = self.client.volumes()[volume_name]
            self.local_port = randint(49152, 65535)
            log.info(f"Exposing TerminusDB locally under port {self.local_port}")

        def get_terminus_container_config(self) -> TerminusContainerConfig:
            return TerminusContainerConfig(
                self.named_volume,
                self.local_port
            )

class TerminusContainerLifecycle(Injectable):
    def __init__(self):
        self.container: Container = None
        self.container_client: ContainerClient = None
        self.container_config: TerminusContainerConfig = None

    def inject_requirements(self, container_client: ContainerClient, config_factory: TerminusContainerConfigFactory) -> None:
        self.container_config = config_factory.get_terminus_container_config()
        self.container_client = container_client

    def initialize(self) -> None:
        #todo this can probably be loosened up somehow
        assert self.container_config.admin.username == "admin", f"Admin username must be 'admin'! Is {self.container_config.admin.username} instead"
        self.container = self.container_client.run(
            self.container_config.image,
            ports={
                #todo make port inside the container match the host port; should make container logs more useful
                6363: self.container_config.localhost_port
            },
            volumes={"/app/terminusdb/storage": HostMount(self.container_config.storage)},
            envvars={
                "TERMINUSDB_ADMIN_PASS": self.container_config.admin.password
            }
        )
        sleep(4) #fixme it should be replaced with a healthcheck, but I don't think I'm gonna invest in terminus, so no point in doing it now

    def deinitialize(self, exc: BaseException | None) -> None:
        self.container.stop()