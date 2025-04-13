from thinking_runtime.defaults.recognise_runtime import current_runtime
from thinking_tests.running.test_config import test_config

if "CI" not in current_runtime().facets.by_name:
    # disable coverage locally, but not in CI pipeline
    test_config.coverage.enabled = False
