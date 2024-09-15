from thinking_runtime.defaults.logging_config import logging_config

for h in logging_config.handlers.files:
    print("disabling", h)
    h.disable()
