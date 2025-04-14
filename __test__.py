from thinking_runtime.defaults.recognise_runtime import current_runtime
from thinking_tests.running.test_config import test_config

# disable coverage locally, but not in CI pipeline
if "CI" not in current_runtime().facets.by_name:
    test_config.coverage.enabled = False
