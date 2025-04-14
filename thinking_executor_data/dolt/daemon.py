from logging import getLogger
from os import makedirs
from os.path import exists, join, isdir
from random import randint
from subprocess import Popen
from typing import NamedTuple, Protocol

import pymysql
from pymysql import DatabaseError
from thinking_runtime.defaults.recognise_runtime import current_runtime, RuntimeMode

from thinking_executor.data.persistence import ProjectPersistenceDirectoryProvider
from thinking_executor_data.terminus.server import Credentials
from thinking_injection.injectable import Injectable
from thinking_reflection.discovery import discover
from thinking_reflection.interfaces import interface
from thinking_services.polling import poll, NamedPredicate, ConstantStepback
from thinking_services.processes import Program

log = getLogger(__name__)


class DoltUserConfig(NamedTuple):
    username: str = "dolt"
    email: str = "dolt@localhost"
    #todo Credentials are in terminus package; extract
    sql_credentials: Credentials = Credentials("dolt", "doltpass")

class DoltDaemonConfig(NamedTuple):
    data_dir: str
    port: int = 3306
    user_config: DoltUserConfig = DoltUserConfig()
    db_name: str = "thinking"
    command: str = "dolt"
    installed_check: list[str] = ["version"]
    repo_check: list[str] = ["status"]
    # fixme this is useless - it will work in any directory, even the non-dolt ones; select from schemata instead?
    healthcheck_sql: str = "select current_timestamp();"

@interface
class DoltDaemonConfigFactory(Protocol):
    def create_dolt_daemon_config(self) -> DoltDaemonConfig: ...


@discover
class CommonDoltConfigFactory(Injectable, DoltDaemonConfigFactory):
    def __init__(self):
        self.dir_provider: ProjectPersistenceDirectoryProvider = None

    def inject_requirements(self, dir_provider: ProjectPersistenceDirectoryProvider) -> None:
        self.dir_provider = dir_provider

    def create_dolt_daemon_config(self) -> DoltDaemonConfig:
        if current_runtime().mode == RuntimeMode.TEST:
            return DoltDaemonConfig(f"{self.dir_provider.project_data_dir()}/dolt",
                                       port=randint(49152, 65535))
        else:
            return DoltDaemonConfig(f"{self.dir_provider.project_data_dir()}/dolt")


class DoltConectionConfig(NamedTuple):
    mysql_connection_str: str


@interface
class DoltConnectionConfigFactory(Protocol):
    def create_dolt_connection_config(self) -> DoltConectionConfig: ...


@discover
class DoltDaemon(Injectable, DoltConnectionConfigFactory):
    def __init__(self):
        self.daemon_config: DoltDaemonConfig = None
        self.connection_config: DoltConectionConfig = None
        self.executable: Program = None
        self.daemon_process: Popen = None
        self._dolt_user: str = None
        self._dolt_email: str = None

    def inject_requirements(self, config_factory: DoltDaemonConfigFactory) -> None:
        self.daemon_config = config_factory.create_dolt_daemon_config()
        self.connection_config = DoltConectionConfig(
            "".join([
                "mysql+pymysql://",
                self.daemon_config.user_config.sql_credentials.username,
                ":",
                self.daemon_config.user_config.sql_credentials.password,
                "@",
                "localhost",
                ":",
                str(self.daemon_config.port),
                "/",
                self.daemon_config.db_name
            ])
        )

    def initialize(self) -> None:
        if not exists(self.daemon_config.data_dir):
            makedirs(self.daemon_config.data_dir)
        self.executable = Program(self.daemon_config.command, self.daemon_config.data_dir, log.debug)
        assert self.executable.check(*self.daemon_config.installed_check)
        self._reconfigure()
        if self._init_repo():
            self._init_sql()
        self._start()
        self._healthcheck()

    def deinitialize(self, exc: BaseException | None) -> None:
        self._stop()
        self._deconfigure()

    def _reconfigure(self):
        """
        We store previous values of config variables to revert the changes we apply here.
        We use --global because we may be operating before the repo exists (so, there may be no context for --local).
        """
        self._dolt_user = self.executable.query("config", "--global", "--get", "user.name")
        self.executable.command("config", "--global", "--set", "user.name", self.daemon_config.user_config.username)
        self._dolt_email = self.executable.query("config", "--global", "--get", "user.name")
        self.executable.command("config", "--global", "--set", "user.email", self.daemon_config.user_config.email)

    def _deconfigure(self):
        """
        See _reconfigure for explanations. This should revert the config changes.
        """
        if self._dolt_user:
            self.executable.command("config", "--global", "--set", "user.name", self._dolt_user)
        else:
            self.executable.command("config", "--global", "--unset", "user.name")
        if self._dolt_email:
            self.executable.command("config", "--global", "--set", "user.email", self._dolt_email)
        else:
            self.executable.command("config", "--global", "--unset", "user.email")

    def _init_repo(self) -> bool:
        """
        Returned value indicates whether the repo is new (True) or not.
        Before returning should check the status of the repo (run repo_check command from the daemon config
        and fail if it fails).
        """
        try:
            initialized = False
            dot_dolt = join(self.daemon_config.data_dir, ".dolt")
            if exists(dot_dolt) and isdir(dot_dolt):
                initialized = True
            log.debug(f"Dolt repo already initialized: {initialized}")
            if not initialized:
                self.executable.command("init") #todo consider using --new-format and maybe --fun
                return True
            return False
        finally:
            assert self.executable.check(*self.daemon_config.repo_check)

    def _init_sql(self):
        c = self.daemon_config
        u = c.user_config
        s = u.sql_credentials
        sqls = [
            f"CREATE DATABASE IF NOT EXISTS {c.db_name};",
            f"CREATE USER IF NOT EXISTS '{s.username}'@'%' IDENTIFIED BY '{s.password}';",
            f"ALTER USER '{s.username}'@'%' IDENTIFIED BY '{s.password}';",
            f"GRANT ALL ON *.* TO '{s.username}'@'%' WITH GRANT OPTION;"
        ]
        for sql in sqls:
            self.executable.command("sql", "-q", sql)

    def _start(self):
        self.daemon_process = self.executable.daemon(
            "sql-server", "-H", "0.0.0.0", "-P", str(self.daemon_config.port)
        )

    def _stop(self):
        self.daemon_process.terminate()
        self.daemon_process.wait()

    def _dolt_sql_check(self) -> bool:
        return self.executable.check("sql", "-q", self.daemon_config.healthcheck_sql)

    def _pymysql_check(self) -> bool:
        c = None
        try:
            log.debug(f"Trying to connect via PyMySQL to {self.connection_config.mysql_connection_str}")
            c = pymysql.connect(
                host="localhost",
                port=self.daemon_config.port,
                user=self.daemon_config.user_config.sql_credentials.username,
                password=self.daemon_config.user_config.sql_credentials.password,
                database=self.daemon_config.db_name
            )
            log.debug("Connection established")
            return True
        except DatabaseError as e:
            log.debug(f"Got a DatabaseError {e}")
            return False
        finally:
            if c is not None:
                c.close()

    def _healthcheck(self):
        poll(NamedPredicate("dolt sql -q ...", self._dolt_sql_check), 5, ConstantStepback(1))
        #retries number is higher for pymysql check - that's mostly for CI sake, where the resources may be more scarce
        poll(NamedPredicate("pymysql connect", self._pymysql_check), 10, ConstantStepback(1))

    def create_dolt_connection_config(self) -> DoltConectionConfig:
        return self.connection_config