from threading import Thread
from typing import Callable, Iterable

LogConsumer = Callable[[str], None]


def consume_log_text(consumer: LogConsumer, stdout: str):
    for line in stdout.split("\n"):
        consumer(line.rstrip())


def consume_log_stream(consumer: LogConsumer, stdout: Iterable[str]):
    def target():
        for line in stdout:
            consumer(line.rstrip())

    Thread(target=target, daemon=True).start()
