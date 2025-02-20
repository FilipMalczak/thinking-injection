from os.path import join, dirname

from lazy import lazy
from thinking_reflection.discovery import discover
from thinking_runtime.defaults.recognise_runtime import current_runtime

from kmeans.model import Vector

DATASET_NAME = "letter_500.arff" if "SMALL" in current_runtime().facets.by_name else "letter.arff"

@discover
class DatasetLoader:
    @lazy
    def data(self) -> list[Vector]:
        def iterate():
            arff = join(dirname(__file__), DATASET_NAME)
            with open(arff) as f:
                for line in f:
                    if not line.startswith("%") and not line.startswith("@"):
                        parts = line.split(",")
                        parts = parts[:16]
                        yield tuple(map(int, parts))
        return list(iterate())