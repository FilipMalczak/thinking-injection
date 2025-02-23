from dataclasses import dataclass

import docker

from thinking_containers.protocol import Container, ContainerClient, ContainerClientFactory, Volumes, Ports, \
    ContainerStatus
from thinking_programming.exceptions import UnreachableInstructionException

# import docker
# BackendContainer = docker.models.containers.Container
# BackendClient = docker.client.DockerClient
# from docker.models.containers import Container as BackendContainer
# from docker.client import DockerClient as BackendClient

@dataclass
class DockerContainer(Container):
    backend: object#: BackendContainer
    volumes: Volumes
    ports: Ports

    @property
    def name(self) -> str:
        return self.backend.name

    @property
    def image(self) -> str:
        return self.backend.image

    @property
    def status(self) -> ContainerStatus:
        raw_status = self.backend.status
        if raw_status == "running":
            return ContainerStatus.RUNNING
        elif raw_status == "exited":
            return ContainerStatus.FINISHED
        UnreachableInstructionException.guard(f"Unrecognized status response {raw_status}")

    def stop(self):
        """
        Should be blocking and idempotent. TBD about exit codes and whatnot.
        """
        self.backend.stop()


class DockerClient(ContainerClient[DockerContainer]):
    def __init__(self, backend: object):
    # def __init__(self, backend: BackendClient):
        self.backend: object = backend

    def run(self, img: str, *, name: str = None, cmd: str = None, volumes: Volumes = None, ports: Ports = None) -> DockerContainer:
        v = {
            k: { "bind": v.path, "mode": v.mode.name.lower() }
            for k, v in (volumes or dict()).items()
        }
        p = ports or dict()
        backend = self.backend.containers.run(img, cmd, name=name, ports=p, volumes=v, detach=True)
        return DockerContainer(backend, v, p)


class DockerFromEnvClientFactory(ContainerClientFactory[DockerClient]):
    def client(self) -> DockerClient:
        return DockerClient(docker.from_env())

class UnixSocketDockerClientFactory(ContainerClientFactory[DockerClient]):
    def client(self) -> DockerClient:
        return DockerClient(docker.DockerClient('unix://var/run/docker.sock'))