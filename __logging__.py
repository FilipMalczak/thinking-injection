from thinking_runtime.defaults.logging_config import logging_config
from thinking_runtime.defaults.recognise_runtime import current_runtime, RuntimeMode, DEBUG

if current_runtime().mode == RuntimeMode.TEST:
    logging_config.level = DEBUG
    for h in logging_config.handlers.files:
        h.disable()
