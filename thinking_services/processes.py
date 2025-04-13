from logging import getLogger
from subprocess import Popen, run, PIPE, STDOUT
from typing import NamedTuple

from thinking_services.logs import LogConsumer, consume_log_text, consume_log_stream

log = getLogger(__name__)


class Program(NamedTuple):
    base_command: str
    cwd: str = None
    log_consumer: LogConsumer = None

    def run(self, *cmd: str, blocking: bool = True, cwd: str = None, log_consumer: LogConsumer = None) -> Popen:
        full_cmd = [self.base_command] + list(cmd)
        spawn = run if blocking else Popen
        kwargs = {}
        if not blocking:
            kwargs["start_new_session"] = True
        cwd = cwd or self.cwd
        if cwd is not None:
            kwargs["cwd"] = cwd
        consumer = log_consumer or self.log_consumer
        if consumer:
            kwargs.update(dict(
            stdout=PIPE,
            stderr=STDOUT,
            text=True,
            encoding="utf-8"
        ))
        log.debug(f"Running: {full_cmd}")
        result = spawn(full_cmd, **kwargs)
        if consumer:
            method = consume_log_text if blocking else consume_log_stream
            method(consumer, result.stdout)
        return result

    def query(self, *cmd: str) -> str | None:
        result = self.run(*cmd)
        if result.returncode == 0:
            return result.stdout.strip()
        return None

    def check(self, *cmd: str):
        result = self.run(*cmd)
        return result.returncode == 0

    def command(self, *cmd: str):
        assert self.check(*cmd)

    def daemon(self, *cmd: str, log_consumer: LogConsumer = None) -> Popen:
        return self.run(*cmd, blocking=False, log_consumer=log_consumer)