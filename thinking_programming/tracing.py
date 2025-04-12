from functools import wraps
from logging import Logger, getLogger

from sphinx.cmd.quickstart import suffix
from thinking_tests.fluent_decorator import fluent_decorator


@fluent_decorator
def traced(logger_or_name: Logger | str = None):
    if logger_or_name is None:
        logger_or_name = "trace"
    logger = logger_or_name if isinstance(logger_or_name, Logger) else getLogger(logger_or_name)
    def logged(foo):
        @wraps(foo)
        def wrapper(*args, **kwargs):
            logger.info(f">>> {foo.__name__}(*{args}, **{kwargs})")
            out = foo(*args, **kwargs)
            suffix = ""
            if out is not None:
                suffix = f" -> |{out}|"
            logger.info(f"<<< {foo.__name__}(...){suffix}")
            return out
        return wrapper
    return logged
