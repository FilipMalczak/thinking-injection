import json
from os import makedirs
from os.path import abspath, join

from thinking_containers.protocol import ContainerClient, Container, HostMount, LocalVolume
from thinking_executor.data.persistence import ProjectPersistenceDirectoryProvider
from thinking_executor_data.dolt.daemon import DoltDaemon
from thinking_injection.injectable import Injectable


class DoltUi: #don't extend Injectable (they are automatically discovered)
    def __init__(self):
        self.containers: ContainerClient = None
        self.ui_container: Container = None
        self.connection_store: str = None
        self.daemon: DoltDaemon = None

    def inject_requirements(self, containers: ContainerClient, dirs: ProjectPersistenceDirectoryProvider, daemon: DoltDaemon) -> None:
        self.containers = containers
        self.connection_store = abspath(join(dirs.project_data_dir(), "dolt-workbench", "connection-store"))
        self.daemon = daemon

    def _initialize_connection_store(self):
        #todo cleanup if needed?
        makedirs(self.connection_store)

    def _fill_connection_store(self):
        data = {
            "name": self.daemon.daemon_config.db_name,
            "connectionUrl": self.daemon.connection_config.mysql_connection_str.replace("mysql+pymysql://", "mysql://").replace("localhost", "host.docker.internal"),
            "port": self.daemon.daemon_config.port,
            "hideDoltFeatures": False,
            "useSSL": False,
            "type": "mysql",
            "isLocalDolt": False,
            "isDolt": True
        }
        with open(join(self.connection_store, "store.json"), "w") as f:
            json.dump([data], f)

    def _run_ui_container(self):
        self.ui_container = self.containers.run(
            "dolthub/dolt-workbench:latest",
            ports={9002: 9002, 3000: 3000},
            volumes={"/app/graphql-server/store": HostMount(LocalVolume(self.connection_store))}
        )

    def initialize(self) -> None:
        self._initialize_connection_store()
        self._fill_connection_store()
        self._run_ui_container()

    def deinitialize(self, exc: BaseException | None) -> None:
        self.ui_container.stop()