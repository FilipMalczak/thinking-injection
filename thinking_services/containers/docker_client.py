from dataclasses import dataclass
from enum import Enum
from logging import getLogger

from docker.errors import ImageNotFound, NotFound

from thinking_programming.guard import Guard
from thinking_services.containers.protocol import Container, ContainerClient, ContainerClientFactory, Volumes, Ports, \
    ContainerStatus, VolumesClient, NamedVolume, VolumeDefinition, LocalVolume
from thinking_programming.exceptions import UnreachableInstructionException

##############################################################################################
#                                                                                            #
#      IMPORTANT!!!                                                                          #
#                                                                                            #
##############################################################################################
#
# this file cannot be named docker.py or there will be weird import conflicts; hence the _client suffix
#
# for the same reason we have test.containers.test_docker_client and not test.docker.<whatwever>

import docker

from thinking_services.logs import LogConsumer, consume_log_stream

BackendContainer = docker.models.containers.Container
BackendClient = docker.client.DockerClient


log = getLogger(__name__)
build_log = getLogger(__name__+".build")

@dataclass
class DockerContainer(Container):
    backend: BackendContainer
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
        elif raw_status == "exited": #todo this may be an issue; sometimes its 'created' even after exit
            return ContainerStatus.FINISHED
        UnreachableInstructionException.guard(f"Unrecognized status response {raw_status}")

    def stop(self):
        """
        Should be blocking and idempotent. TBD about exit codes and whatnot.
        """
        self.backend.stop()
        self.backend.wait()
        self.backend.remove()

class DockerVolumesClient(VolumesClient):
    def __init__(self, backend: BackendClient):
        self.backend: BackendClient = backend

    def create(self, name: str) -> NamedVolume:
        log.debug(f"Creating volume {name}")
        self.backend.volumes.create(name)
        return NamedVolume(name)

    def exists(self, name: str) -> bool:
        try:
            self.backend.volumes.get(name)
            return True
        except NotFound:
            return False

    def delete(self, name: str):
        #fixme try NotFound may bubble up
        log.debug(f"Deleting volume {name}")
        self.backend.volumes.get(name).remove()

class DockerClient(ContainerClient[DockerContainer]):
    def __init__(self, backend: BackendClient):
        self.backend: BackendClient = backend
        self.backend.ping()

    def volumes(self) -> VolumesClient:
        return DockerVolumesClient(self.backend)

    def _consumer(self, log_consumer: LogConsumer | None, logger_name: str, method_name: str = "debug") -> LogConsumer | None:
        if log_consumer is Guard:
            log_consumer = getattr(getLogger(logger_name), method_name)
        return log_consumer

    #todo unused; probably should be deleted
    def build(self, dir: str, filename: str, name: str, tag: str = "latest",
              overwrite: bool=False, log_consumer: LogConsumer = Guard):
        fullname = f"{name}:{tag}"
        exists = False
        try:
            self.backend.images.get(fullname)
            exists = True
        except ImageNotFound:
            pass
        should_build = True
        if exists:
            if overwrite:
                self.backend.images.remove(fullname)
            else:
                should_build = False
        if should_build:
            _, logs = self.backend.images.build(
                path=dir,
                dockerfile=filename,
                tag=fullname
            )
            if log_consumer is not None:
                log_consumer = self._consumer(log_consumer, __name__+".build."+name)
                consume_log_stream(log_consumer, (line["stream"].strip() for line in logs))

    def _prepare_volume(self, definition: VolumeDefinition) -> str:
        if isinstance(definition, LocalVolume):
            return definition.host_path
        elif isinstance(definition, NamedVolume):
            return definition.volume_name
        else:
            UnreachableInstructionException.guard(f"Unknown volume definition type: {type(definition)} ({definition})")

    def _prepare_volumes(self, volumes: Volumes) -> dict:
        out = {}
        for container_path, details in volumes.items():
            out[self._prepare_volume(details.definition)] = {
                "bind": container_path,
                "mode": details.mode.name.lower()
            }
        return out

    def run(self, img: str, *,
            name: str = None,
            cmd: str = None,
            volumes: Volumes = None,
            ports: Ports = None,
            envvars: dict[str, str | int] = None,
            log_consumer: LogConsumer = Guard) -> DockerContainer:
        volumes = volumes or dict()
        v = self._prepare_volumes(volumes)
        p = ports or dict()
        repo, colon, tag = img.rpartition(":")  # if tag is missing, then rpartition will return ('', '', img)
        if not repo:
            log.debug("Tag was missing, setting it to 'latest'")
            repo = tag
            tag = "latest"
            img += ":" + tag
        try:
            self.backend.images.get(img)
        except ImageNotFound:
            log.debug(f"Image {img} not found, pulling")
            #todo customize exception that may be raised here (or dont?)
            self.backend.images.pull(repo, tag)
            log.debug("Image pulled")
            #todo it would be nice to get pull logs too

        envvars = envvars or dict()
        envvars = {
            k: str(v)
            for k, v in envvars.items()
        }
        #todo should we expose envvars too?
        backend = self.backend.containers.run(
            img,
            cmd,
            name=name,
            ports=p,
            volumes=v,
            detach=True,
            environment=envvars or dict(),
            extra_hosts={"host.docker.internal": "host-gateway"}
        )

        if log_consumer is not None:
            log_consumer = self._consumer(log_consumer, __name__+".run"+backend.name)
            consume_log_stream(log_consumer, (line.decode("utf-8") for line in backend.logs(stream=True)))
        return DockerContainer(backend, volumes, p)

class DockerFromEnvClientFactory(ContainerClientFactory[DockerClient]):
    def client(self) -> DockerClient:
        return DockerClient(docker.from_env())

class UnixSocketDockerClientFactory(ContainerClientFactory[DockerClient]):
    def client(self) -> DockerClient:
        return DockerClient(docker.DockerClient('unix://var/run/docker.sock'))