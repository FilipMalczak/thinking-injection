from math import sqrt

from thinking_reflection.discovery import discover

from kmeans.model import Vector

@discover
class Distance:
    def between(self, v1: Vector, v2: Vector) -> float:
        return sqrt(
            sum(
                x*x
                for x in map(
                    lambda p: p[0] - p[1],
                    zip(v1, v2)
                )
            )
        )