import subprocess
from dataclasses import field
from logging import getLogger
from os import makedirs
from os.path import exists, join, isdir
from random import random, randint
from subprocess import Popen, run
from threading import Thread, Condition
from time import sleep
from typing import NamedTuple, Protocol, Callable

import pymysql
from pymysql import DatabaseError
from thinking_runtime.defaults.recognise_runtime import current_runtime, RuntimeMode

from thinking_executor.data.persistence import ProjectPersistenceDirectoryProvider
from thinking_executor_data.terminus.server import Credentials
from thinking_injection.injectable import Injectable
from thinking_reflection.discovery import discover
from thinking_reflection.interfaces import interface

log = getLogger(__name__)


class DoltUserConfig(NamedTuple):
    username: str = "dolt"
    email: str = "dolt@localhost"
    #todo Credentials are in terminus package; extract
    sql_credentials: Credentials = Credentials("dolt", "doltpass")

class DoltDaemonConfig(NamedTuple):
    data_dir: str
    port: int = 3306
    # host: str = "0.0.0.0"
    # host: str = "localhost"
    user_config: DoltUserConfig = DoltUserConfig()
    db_name: str = "thinking"
    command: str = "dolt"
    installed_check: list[str] = ["version"]
    repo_check: list[str] = ["status"] #fixme not used anymore
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
        # self.daemon_process: Popen = None
        # self.log_thread: Thread = None
        self.daemon_handle: Callable[[], int] = None
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
                # self.daemon_config.host,
                ":",
                str(self.daemon_config.port),
                "/",
                self.daemon_config.db_name
            ])
        )

    def initialize(self) -> None:
        if not exists(self.daemon_config.data_dir):
            makedirs(self.daemon_config.data_dir)
        assert self._run_check(*self.daemon_config.installed_check)
        self._reconfigure()
        if self._init_repo():
            self._init_sql()
        self._start()
        self._healthcheck()

    def deinitialize(self, exc: BaseException | None) -> None:
        self._stop()
        self._deconfigure()

    #fixme lots of copypasted code in _run_... methods - normalize it

    def _popen_kwargs(self):
        return dict(
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            cwd=self.daemon_config.data_dir
        )

    def _subprocess(self, *cmd: str, new_session: bool = False) -> Popen:
        full_cmd = [self.daemon_config.command] + list(cmd)
        if new_session:
            full_cmd = " ".join(full_cmd)
        log.info(f"Running: {full_cmd}")
        result = run(
            full_cmd,
            **self._popen_kwargs()
        )
        return result

    def _daemon_process(self, *cmd: str) -> Popen:
        full_cmd = [self.daemon_config.command] + list(cmd)
        # full_cmd = " ".join([self.daemon_config.command] + list(cmd))
        log.info(f"Running: {full_cmd}")
        result = Popen(
            full_cmd,
            **self._popen_kwargs(),
            # shell=True,
            start_new_session=True
        )
        return result

    def _run_query(self, *cmd: str) -> str | None:
        result = self._subprocess(*cmd)
        if result.returncode == 0:
            return result.stdout.strip()
        log.error(result.stdout.strip())
        return None

    def _run_check(self, *cmd: str) -> bool:
        result = self._subprocess(*cmd)
        log = getLogger("daemon.dolt." + cmd[0])
        if result.returncode > 0:
            # for line in result.stdout:
            #     log.error(line.strip())
            log.error(result.stdout.strip())
        else:
            log.info(result.stdout.strip()) #todo debug
        return result.returncode == 0

    def _run_command(self, *cmd: str):
        result = self._subprocess(*cmd)
        if result.returncode > 0:
            log = getLogger("daemon.dolt."+cmd[0])
            # for line in result.stdout:
            #     log.error(line.strip())
            log.error(result.stdout.strip())
        assert result.returncode == 0

    def _run_daemon(self, *cmd: str, log_consumer: Callable[[str], None] = None) -> Callable[[], int]:
        # daemon_process = []
        # def run_daemon():
        #     p = self._subprocess(*cmd, new_session=True)
        #     daemon_process.append(p)
        #     daemon_process[0].wait()
        result = self._daemon_process(*cmd)
        # result = self._subprocess(*cmd, new_session=True)
        # def stream_logs(): ... #fixme
        def stream_logs():
            # while not daemon_process:
            #     sleep(0.1) #todo must be doable in better fashion
            # for line in daemon_process[0].stdout:
            for line in result.stdout:
                log_consumer(line.strip())
            # log_consumer(daemon_process[0].stdout)

        # daemon_thread = Thread(target=run_daemon, daemon=True)
        # daemon_thread.start()
        log_thread = Thread(target=stream_logs, daemon=True)
        log_thread.start()
        return result

        # def handle():
        #     daemon_process[0].terminate()
        #     daemon_thread.join()
        #     return daemon_process[0].returncode
        #
        # # sleep(3) #todo a better healthcheck
        # # return result, log_thread
        # return handle

    def _reconfigure(self):
        self._dolt_user = self._run_query("config", "--global", "--get", "user.name")
        self._run_command("config", "--global", "--set", "user.name", self.daemon_config.user_config.username)
        self._dolt_email = self._run_query("config", "--global", "--get", "user.name")
        self._run_command("config", "--global", "--set", "user.email", self.daemon_config.user_config.email)

    def _deconfigure(self):
        if self._dolt_user:
            self._run_command("config", "--global", "--set", "user.name", self._dolt_user)
        #todo else: unset; we want to leave the runtime with the same config state as when starting up
        if self._dolt_email:
            self._run_command("config", "--global", "--set", "user.email", self._dolt_email)

    def _init_repo(self):
        #todo cleanup repo_check and _run_check
        # initialized = self._run_check(self.daemon_config.repo_check)
        initialized = False
        dot_dolt = join(self.daemon_config.data_dir, ".dolt")
        if exists(dot_dolt) and isdir(dot_dolt):
            initialized = True
        log.info(f"Dolt repo already initialized: {initialized}")
        if not initialized:
            self._run_command("init") #todo consider using --new-format and maybe --fun
            return True
        return False

    def _init_sql(self):
        c = self.daemon_config
        u = c.user_config
        s = u.sql_credentials
        sqls = [
            f"CREATE DATABASE IF NOT EXISTS {c.db_name};",
            f"CREATE USER IF NOT EXISTS '{s.username}'@'%' IDENTIFIED BY '{s.password}';",
            # f"CREATE USER IF NOT EXISTS '{s.username}'@'{c.host}' IDENTIFIED BY '{s.password}';",
            f"ALTER USER '{s.username}'@'%' IDENTIFIED BY '{s.password}';",
            # f"ALTER USER '{s.username}'@'{c.host}' IDENTIFIED BY '{s.password}';",
            f"GRANT ALL ON *.* TO '{s.username}'@'%' WITH GRANT OPTION;"
            # f"GRANT ALL ON *.* TO '{s.username}'@'{c.host}' WITH GRANT OPTION;"
        ]
        for sql in sqls:
            # self._run_command("sql", "-q", '"'+sql+'"')
            self._run_command("sql", "-q", sql)

    def _start(self):
        self.daemon_process = self._run_daemon(
        # self.daemon_process, self.log_thread = self._run_daemon(
        # self.daemon_handle = self._run_daemon(
            # f"sql-server -H % -P {self.daemon_config.port}",
            # f"sql-server -H {self.daemon_config.host} -P {self.daemon_config.port}",
            # f"sql-server -H 0.0.0.0 -P {self.daemon_config.port}",
            "sql-server", "-H", "0.0.0.0", "-P", str(self.daemon_config.port),
            log_consumer=getLogger("dolt-daemon").info
        )

    def _stop(self):
        self.daemon_process.terminate()
        self.daemon_process.wait()
        # code = self.daemon_handle()
        # assert code == 0
        #dont do anything about log_thread - its a daemon anyway

    def _poll(self, cond: Callable[[], bool], retries: int, stepback: float):
        success = False
        for i in range(retries):
            log.info(f"Poll retry {i+1}/{retries}")
            if not cond():
                log.info(f"Fail; sleep for {stepback}s")
                sleep(stepback)
            else:
                success = True
                log.info(f"Success!")
                break
        assert success

    def _dolt_sql_check(self) -> bool:
        #fixme this is useless - it will work in any directory, even the non-dolt ones; select from schemata instead?
        log.info(f"Checking 'dolt sql -q '{self.daemon_config.healthcheck_sql}'")
        return self._run_check("sql", "-q", self.daemon_config.healthcheck_sql)
        # return self._run_check("sql", "-q", "'"+self.daemon_config.healthcheck_sql+"'")
        # return self._run_check(f"sql -q '{self.daemon_config.healthcheck_sql}'")

    def _pymysql_check(self) -> bool:
        c = None
        try:
            log.info(f"Trying to connect via PyMySQL to {self.connection_config.mysql_connection_str}")
            c = pymysql.connect(
                # host=self.daemon_config.host,
                host="localhost",
                port=self.daemon_config.port,
                user=self.daemon_config.user_config.sql_credentials.username,
                password=self.daemon_config.user_config.sql_credentials.password,
                database=self.daemon_config.db_name
            )
            log.info("Connection established")
            return True
        except DatabaseError as e:
            log.error(f"Got a DatabaseError {e}")
            return False
        finally:
            if c is not None:
                c.close()

    def _healthcheck(self):
        self._poll(self._dolt_sql_check, 5, 1)
        self._poll(self._pymysql_check, 5, 1)

    def create_dolt_connection_config(self) -> DoltConectionConfig:
        return self.connection_config