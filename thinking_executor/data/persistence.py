#todo come up with better name for this module
from collections import defaultdict
from logging import getLogger
from os import makedirs
from os.path import abspath, exists, isdir
from shutil import rmtree
from typing import Protocol

from thinking_runtime.defaults.recognise_runtime import current_runtime, RuntimeMode

from thinking_injection.lifecycle import Initializable
from thinking_reflection.discovery import discover
from thinking_reflection.interfaces import interface


@interface
class ProjectPersistenceDirectoryProvider(Protocol):
    def project_data_dir(self) -> str: ...

if current_runtime().mode == RuntimeMode.TEST:
    from thinking_tests.current import current_case_name, current_case_id

    log = getLogger("TestDataConfiguration")

    @discover
    class TestDataConfiguration(ProjectPersistenceDirectoryProvider, Initializable):
        _CLEANED: dict[str, bool] = defaultdict(lambda: False)

        def initialize(self) -> None:
            out = abspath(f"./test-data/{current_case_id().replace(":", "-").replace(" ", "_")}")
            if not TestDataConfiguration._CLEANED[out]:
                log.info(f"Cleaning test data directory {out}")
                if exists(out):
                    assert isdir(out), f"{out} already exists, but isn't a directory"
                    try:
                        rmtree(out)
                    except:
                        log.error("Error while removing "+out)
                        raise
                makedirs(out)
                TestDataConfiguration._CLEANED[out] = True
            else:
                log.info(f"Test data directory {out} has already been cleaned")
            self.dir_path = out

        def project_data_dir(self) -> str:
            return self.dir_path