from logging import getLogger

from thinking_tests.decorators import case
from thinking_tests.running.start import run_current_module

from thinking_executor_data.dolt.daemon import DoltDaemon
from thinking_injection.context.configurable.impl import ConfigurableContext
from thinking_injection.typeset import from_packages


log = getLogger(__name__)

@case
def daemon_starts_up():
    ctx = ConfigurableContext([
        *from_packages("thinking_executor", "thinking_executor_data.common", "thinking_executor_data.dolt"),
    ])
    with ctx.lifecycle() as idx:
        daemon = idx.instance(DoltDaemon)
        log.info(daemon.executable.query("sql", "-q", "show databases;"))
        thinking_db = daemon.executable.query("sql", "-r", "csv", "-q", f"select schema_name from information_schema.schemata where schema_name = '{daemon.daemon_config.db_name}';")
        expected = f"""SCHEMA_NAME
{daemon.daemon_config.db_name}"""

        assert thinking_db == expected, f"Actual: |{thinking_db}|; expected: |{expected}|"

if __name__=="__main__":
    run_current_module()