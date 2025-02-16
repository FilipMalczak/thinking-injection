# Clustering

Example project that utilizes executor (and contextful executor).

Naively implements a k-means algorithm. Given a pretty large dataset (as found 
[here](https://github.com/deric/clustering-benchmark/blob/master/src/main/resources/datasets/real-world/letter.arff))
and purposefully slow computations each iteration takes significant amount of time. That makes it a perfect example
for using the task executor.

Besides that, the project is a good example of using runtime facets. In [__setup__.py](./__setup__.py) we register two
facets - `SMALL` and `SHORT`, activated by presence of `SMALL_DATASET` and `SHORT_RUN` envvars respectively. These facets
are later used (by checking `... in current_runtime().facets.by_name`) to determine the [dataset size](./kmeans/dataset.py)
and the [number of iterations](./kmeans/clusterizer.py).