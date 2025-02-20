from random import Random

from thinking_reflection.discovery import discover

from kmeans.model import Vector, VECTOR_LENGTH

@discover
class Vectors:
    def __init__(self):
        self.r = Random()

    def avg(self, vs: list[Vector]) -> Vector:
        result = [ 0 ] * VECTOR_LENGTH
        if vs:

            for v in vs:
                for i in range(VECTOR_LENGTH):
                    result[i] += v[i]
            result = [ x/len(vs) for x in result ]
        return result

    def random(self) -> Vector:
        return [ self.r.uniform(0, 15) for i in range(VECTOR_LENGTH) ]