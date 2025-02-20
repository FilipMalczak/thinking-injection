from dataclasses import dataclass

from thinking_executor.executor_model import Args
from thinking_reflection.discovery import discover
from thinking_runtime.defaults.recognise_runtime import current_runtime

from kmeans.dataset import DatasetLoader
from kmeans.distance import Distance
from kmeans.model import Vector
from kmeans.vectors import Vectors
from thinking_executor.data.tiny_schema import TinyDBTableWithSchema, tiny_table, Query
from thinking_executor.data.tinydb import TinyDBLifecycle
from thinking_executor.executor import SimpleTaskExecutor
from thinking_injection.injectable import Injectable
from thinking_programming.serialization import SerializableMixin


@tiny_table("centroids")
@dataclass
class Centroids(SerializableMixin):
    iteration: int
    points: list[Vector]

CENTROIDS_COUNT = 26

ITERATIONS = 10 if "SHORT" in current_runtime().facets.by_name else 100

@tiny_table("assignments")
@dataclass
class Assignments(SerializableMixin):
    iteration: int
    centroid_idx: list[int] # centroid_idx[a] = b means that dataset vector #a is closest to centroid #b

@discover
class Clusterizer(Injectable):
    def __init__(self):
        self.distance: Distance = None
        self.vectors: Vectors = None
        self.centroids: TinyDBTableWithSchema = None
        self.assignments: TinyDBTableWithSchema = None
        self.exec: SimpleTaskExecutor = None

    def inject_requirements(self, dataset: DatasetLoader, distance: Distance, vectors: Vectors, tiny: TinyDBLifecycle, exec: SimpleTaskExecutor) -> None:
        self.points = dataset.data
        self.distance = distance
        self.vectors = vectors
        self.centroids = tiny.get_table_of(Centroids)
        self.assignments = tiny.get_table_of(Assignments)
        self.exec = exec

    def run(self):
        @self.exec.stage
        def kmeans():
            @self.exec.step
            def intialize_centroids():
                self.centroids.insert(Centroids(-1, [ self.vectors.random() for i in range(CENTROIDS_COUNT) ]))
            @self.exec.stage
            def iterations():
                for i in range(ITERATIONS):
                    @self.exec.stage(i, stage_args=Args.of(i))
                    def iteration(iter):
                        previous = self.centroids.get(Query().iteration == (iter-1))
                        @self.exec.step
                        def assign():
                            assignments = []
                            for point in self.points:
                                closest_idx = 0
                                closest_distance = self.distance.between(point, previous.points[0])
                                for c_idx, centroid in enumerate(previous.points[1:], 1):
                                    dist = self.distance.between(point, centroid)
                                    if dist < closest_distance:
                                        closest_idx = c_idx
                                        closest_distance = dist
                                assignments.append(closest_idx)
                            self.assignments.insert(Assignments(i, assignments))
                        @self.exec.step
                        def recalculate():
                            assignments = self.assignments.get(Query().iteration == iter).centroid_idx
                            grouped = [ [] for i in range(CENTROIDS_COUNT) ]
                            for i, c_idx in enumerate(assignments):
                                grouped[c_idx].append(self.points[i])
                            recalculated = [
                                self.vectors.avg(grouped[c_idx])
                                for c_idx in range(CENTROIDS_COUNT)
                            ]
                            self.centroids.insert(Centroids(iter, recalculated))
        return self.centroids.get(Query().iteration == (ITERATIONS-1)).points