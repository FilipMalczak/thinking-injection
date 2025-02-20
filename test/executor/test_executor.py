from logging import getLogger
from os import remove
from os.path import exists

from thinking_tests.decorators import case, setup
from thinking_tests.running.start import run_current_module

from thinking_executor.data.tinydb import TinyDBTestConfiguration
from thinking_executor.executor import TaskExecutor
from thinking_executor.executor_model import Args
from thinking_injection.context.configurable.impl import ConfigurableContext
from thinking_injection.typeset import from_package

log = getLogger(__name__)

class Exc1(Exception): pass
class Exc2(Exception): pass


def setup_context():
    ctx = ConfigurableContext([TinyDBTestConfiguration])
    with ctx.lifecycle() as index:
        config = index.instance(TinyDBTestConfiguration)
        path = config.get_tinydb_parameters().path
        if exists(path):
            remove(path)
    return {
        "ctx": ConfigurableContext([*from_package("thinking_executor")])
    }

#fixme this approach to setup/teardown is irritating when it comes to passing params to cases
# https://github.com/FilipMalczak/thinking-tests/issues/1
with setup(setup_context):
    @case
    def running_twice_in_the_same_session_doesnt_skip(setup):
        ctx = setup["ctx"]
        with ctx.lifecycle() as index:
            executor = index.instance(TaskExecutor)

            trace = []

            def top_level():
                trace.append(executor.current_path)
                def first():
                    trace.append(executor.current_key)

                executor.execute_step(1, first)
                trace.append("INITIAL_END")
            executor.execute_stage("top", top_level)

            assert trace == [ ["top"], 1, "INITIAL_END" ]
            log.info("Rerun")
            trace = []

            executor.execute_stage("top", top_level)

            assert trace == [ ["top"], 1, "INITIAL_END" ]

    @case
    def test_continuing_after_error(setup):
        ctx = setup["ctx"]
        with ctx.lifecycle() as index:
            executor = index.instance(TaskExecutor)

            trace = []

            def top_level():
                trace.append(executor.current_path)
                def first():
                    trace.append(executor.current_key)
                def second(x):
                    trace.append(x)

                executor.execute_step(1, first)
                trace.append("INITIAL_END")
                raise Exc1()

            raised = False
            try:
                executor.execute_stage("top", top_level)
                raise Exc2()
            except Exc1:
                raised = True
            assert raised

            assert trace == [["top"], 1, "INITIAL_END"]
            log.info("Rerun")
            trace = []

            def top_level_again():
                trace.append(executor.current_path)
                def first():
                    trace.append(executor.current_key)
                def second(x):
                    trace.append(x)

                executor.execute_step(1, first)
                trace.append("INITIAL_END")
                executor.execute_step("second", second, Args(("arg1", )))
                trace.append("secondary end")

            executor.execute_stage("top", top_level_again)
        assert trace == [ ["top"], 1, "INITIAL_END", "arg1", "secondary end" ]

    @case
    def test_skipping_steps_between_sessions(setup):
        ctx = setup["ctx"]
        with ctx.lifecycle() as index:
            executor = index.instance(TaskExecutor)
            trace = []

            def top_level():
                trace.append(executor.current_path)

                def first():
                    trace.append(executor.current_key)

                executor.execute_step(1, first)
                trace.append("INITIAL_END")

            executor.execute_stage("top", top_level)

            assert trace == [ ["top"], 1, "INITIAL_END" ]
        log.info("Rerun")
        trace = []

        with ctx.lifecycle() as index:
            executor = index.instance(TaskExecutor)
            executor.execute_stage("top", top_level)

        assert trace == []

    @case
    def running_twice_with_decorators_in_the_same_session_doesnt_skip(setup):
        ctx = setup["ctx"]
        with ctx.lifecycle() as index:
            executor = index.instance(TaskExecutor)
            trace = []

            @executor.stage
            def top_level():
                trace.append(executor.current_path)
                @executor.step(1)
                def first():
                    trace.append(executor.current_key)
                trace.append("INITIAL_END")

            assert trace == [["top_level"], 1, "INITIAL_END"]
            log.info("Rerun")
            trace = []

            @executor.stage
            def top_level():
                trace.append(executor.current_path)

                @executor.step(step_key=1)
                def first():
                    trace.append(executor.current_key)

                trace.append("INITIAL_END")
            assert trace == [["top_level"], 1, "INITIAL_END"]


    @case
    def test_skipping_steps_between_sessions_with_decorators(setup):
        trace = []
        ctx = setup["ctx"]
        with ctx.lifecycle() as index:
            executor = index.instance(TaskExecutor)
            @executor.stage
            def top_level():
                trace.append(executor.current_path)
                @executor.step(1)
                def first():
                    trace.append(executor.current_key)
                trace.append("INITIAL_END")

        assert trace == [["top_level"], 1, "INITIAL_END"]
        log.info("Rerun")
        trace = []

        with ctx.lifecycle() as index:
            executor = index.instance(TaskExecutor)
            @executor.stage
            def top_level():
                trace.append(executor.current_path)

                @executor.step(step_key=1)
                def first():
                    trace.append(executor.current_key)

                trace.append("INITIAL_END")

        assert trace == []

if __name__=="__main__":
    run_current_module()
    # test_continuing_after_error()
    # running_twice_in_the_same_session_doesnt_skip()
    # test_skipping_steps_between_sessions()