from logging import getLogger
from typing import NamedTuple, Protocol

from terminusdb_client import Client

from thinking_executor.session import PersistentSessionManager
from thinking_executor_data.terminus.server import Credentials, TerminusContainerConfig, TerminusContainerLifecycle
from thinking_executor_data.terminus.utils import not_found_as_None
from thinking_injection.injectable import Injectable
from thinking_reflection.discovery import discover
from thinking_reflection.interfaces import interface


log = getLogger(__name__)


class ServerUrl(NamedTuple):
    protocol: str
    host: str
    port: int

    @property
    def connection_string(self):
        return f"{self.protocol}://{self.host}:{self.port}/"

class TerminusConnectionConfig(NamedTuple):
    admin: Credentials
    server_url: ServerUrl
    team: str = "thinking"
    database: str = "thinking"
    worker: Credentials = Credentials("thinking", "poorpassword")

@interface
class TerminusConnectionConfigFactory(Protocol):
    def get_terminus_connection_config(self) -> TerminusConnectionConfig: ...

@discover
class DefaultTerminusConnectionConfigFactory(Injectable, TerminusConnectionConfigFactory):
    def __init__(self):
        self.container_config: TerminusContainerConfig = None

    def inject_requirements(self, container_lifecycle: TerminusContainerLifecycle) -> None:
        self.container_config = container_lifecycle.container_config

    def get_terminus_connection_config(self) -> TerminusConnectionConfig:
        return TerminusConnectionConfig(
            self.container_config.admin,
            ServerUrl("http", "localhost", self.container_config.localhost_port)
        )

class TerminusClientLifecycle(Injectable):
    def __init__(self):
        self.client: Client = None
        self.connection_config: TerminusConnectionConfig = None

    def inject_requirements(self, config_factory: TerminusConnectionConfigFactory) -> None:
        self.connection_config = config_factory.get_terminus_connection_config()

    def initialize(self) -> None:
        self.client = Client(self.connection_config.server_url.connection_string)
        self._setup()
        self.client.connect(
            team=self.connection_config.team,
            db=self.connection_config.database,
            user=self.connection_config.worker.username,
            key=self.connection_config.worker.password
        )
        #it's the storage (or maybe repo) that should register schema; don't do that here


    def _setup(self):
        log.info(f"Connecting to TerminusDB instance: {self.connection_config.server_url.connection_string}")
        self.client.connect(user=self.connection_config.admin.username, key=self.connection_config.admin.password)
        if not_found_as_None(self.client.get_organization, self.connection_config.team) is None:
            self.client.create_organization(self.connection_config.team)
        if not_found_as_None(self.client.get_database, self.connection_config.database, self.connection_config.team) is None:
            self.client.create_database(self.connection_config.database, self.connection_config.team)
        role_definition = {
            "name": "thinking",
            "action": [
                "schema_read_access",
                "instance_read_access",
                "schema_write_access",
                "instance_write_access",
                "commit_write_access",
                "commit_read_access",
                "branch",
                #todo not sure if these 2 are really needed
                "meta_read_access",
                "class_frame",
            ]
        }
        if not role_definition["name"] in (x["name"] for x in self.client.get_available_roles()):
            self.client.add_role(role_definition)
        else:
            self.client.change_role(role_definition)
        if not_found_as_None(self.client.get_user, self.connection_config.worker.username) is None:
            self.client.add_user(*self.connection_config.worker)
        else:
            self.client.change_user_password(*self.connection_config.worker)
        #granting role is idempotent, so no checks here
        for user in (self.connection_config.admin.username, self.connection_config.worker.username):
            self.client.change_capabilities({
                "operation": "grant",
                "scope": "Organization/"+self.connection_config.team,
                "user": "User/"+user,
                "roles": [ "Role/"+role_definition["name"] ]
            })
        self.client.close() #closing the admin connection; initialize() will go forth and reconnect as user

    def deinitialize(self, exc: BaseException | None) -> None:
        self.client.close()
        self.client = None