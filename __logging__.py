from thinking_runtime.defaults.logging_config import logging_config
from thinking_runtime.defaults.recognise_runtime import current_runtime, RuntimeMode, DEBUG

if current_runtime().mode == RuntimeMode.TEST:
    #CI logs should be short; local logs can sometimes be more detailed
    if "CI" not in current_runtime().facets.by_name:
        logging_config.level = DEBUG
    for h in logging_config.handlers.files:
        h.disable()
