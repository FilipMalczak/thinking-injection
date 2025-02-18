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

## What's the fuss about?

OK, so why is executor module useful? Imagine that this algorithm is BIGGER. Millions of points. Thousands of iterations.
Vectors in `R^1000` space (and not `R^2`). Each iteration may take minutes or even hours, the whole run may take days.

Now imagine that halfway through you lost the power (and never invested in UPS). For the sake of our example, we'll use 
`KeyboardInterrupt` with `SHORT` facet enabled. 

> There is small difference - sessions interrupted by `Ctrl+C` have state of `Interrupted`, those stopped by
> dedicated `thinking_programming.outcome.ToBeContinuedException` are marked as `ToBeContinued` and any other 
> non-succesful session will have state of `Failure`.
> 
> The `ToBeContinued` is useful if you are writing the code incrementally. You may want to wait until some stage ends,
> investigate the results and then decide what are the further instructions.

You'll find the full logs of first session 
[here](./session_2025-02-18 13:18:20.712131.log) and for the second session - [here](./session_2025-02-18 13:18:27.349383.log).
The [./kmeans.json](./kmeans.json) file is the TinyDB JSON file used by executor for tracking sessions and tasks.

> TinyDB doesn't pretty print JSONs out of the box, so be prepared for a looooong line of data. 
> Use some [pretty printer](https://jsonformatter.org/json-pretty-print) for easier reading.
> 
> For the sake of simplicity the clustering algorithm is using the same DB for storing centroids and assingment data.
> That doesn't need to be the case. Other `thinking` projects provide (or will provide) integration with version-controlled
> databases.
> 
> FIXME
> At the moment of writing this there is a leftover field `invoked_steps` in context session object that is always an empty list.
> Ignore it, it will get cleaned up when we provide version-controlled DBs.

Here are the logs of the executor for the first run (the interrupted one):
```
[  INFO  ] 2025-02-18 13:18:20,989 | thinking_executor.executor @183 :: Task STAGE:kmeans@0 hasn't been executed yet
[  INFO  ] 2025-02-18 13:18:20,989 | thinking_executor.executor @183 :: Task STEP:kmeans/intialize_centroids@0/0 hasn't been executed yet
[  INFO  ] 2025-02-18 13:18:20,992 | thinking_executor.executor @193 :: Task finished executing at 2025-02-18 13:18:20.992866
[  INFO  ] 2025-02-18 13:18:20,996 | thinking_executor.executor @183 :: Task STAGE:kmeans/iterations@0/1 hasn't been executed yet
[  INFO  ] 2025-02-18 13:18:20,996 | thinking_executor.executor @183 :: Task STAGE:kmeans/iterations/0@0/1/0 hasn't been executed yet
[  INFO  ] 2025-02-18 13:18:20,997 | thinking_executor.executor @183 :: Task STEP:kmeans/iterations/0/assign@0/1/0/0 hasn't been executed yet
[  INFO  ] 2025-02-18 13:18:22,163 | thinking_executor.executor @193 :: Task finished executing at 2025-02-18 13:18:22.163563
[  INFO  ] 2025-02-18 13:18:22,170 | thinking_executor.executor @183 :: Task STEP:kmeans/iterations/0/recalculate@0/1/0/1 hasn't been executed yet
[  INFO  ] 2025-02-18 13:18:22,199 | thinking_executor.executor @193 :: Task finished executing at 2025-02-18 13:18:22.199576
[  INFO  ] 2025-02-18 13:18:22,205 | thinking_executor.executor @193 :: Task finished executing at 2025-02-18 13:18:22.205718
[  INFO  ] 2025-02-18 13:18:22,212 | thinking_executor.executor @183 :: Task STAGE:kmeans/iterations/1@0/1/1 hasn't been executed yet
[  INFO  ] 2025-02-18 13:18:22,217 | thinking_executor.executor @183 :: Task STEP:kmeans/iterations/1/assign@0/1/1/0 hasn't been executed yet
[  INFO  ] 2025-02-18 13:18:23,364 | thinking_executor.executor @193 :: Task finished executing at 2025-02-18 13:18:23.364041
[  INFO  ] 2025-02-18 13:18:23,374 | thinking_executor.executor @183 :: Task STEP:kmeans/iterations/1/recalculate@0/1/1/1 hasn't been executed yet
[  INFO  ] 2025-02-18 13:18:23,406 | thinking_executor.executor @193 :: Task finished executing at 2025-02-18 13:18:23.406677
[  INFO  ] 2025-02-18 13:18:23,415 | thinking_executor.executor @193 :: Task finished executing at 2025-02-18 13:18:23.415031
[  INFO  ] 2025-02-18 13:18:23,435 | thinking_executor.executor @183 :: Task STAGE:kmeans/iterations/2@0/1/2 hasn't been executed yet
[  INFO  ] 2025-02-18 13:18:23,445 | thinking_executor.executor @183 :: Task STEP:kmeans/iterations/2/assign@0/1/2/0 hasn't been executed yet
[  INFO  ] 2025-02-18 13:18:24,602 | thinking_executor.executor @193 :: Task finished executing at 2025-02-18 13:18:24.602274
[  INFO  ] 2025-02-18 13:18:24,616 | thinking_executor.executor @183 :: Task STEP:kmeans/iterations/2/recalculate@0/1/2/1 hasn't been executed yet
[  INFO  ] 2025-02-18 13:18:24,653 | thinking_executor.executor @193 :: Task finished executing at 2025-02-18 13:18:24.653359
[  INFO  ] 2025-02-18 13:18:24,664 | thinking_executor.executor @193 :: Task finished executing at 2025-02-18 13:18:24.664350
[  INFO  ] 2025-02-18 13:18:24,678 | thinking_executor.executor @183 :: Task STAGE:kmeans/iterations/3@0/1/3 hasn't been executed yet
[  INFO  ] 2025-02-18 13:18:24,690 | thinking_executor.executor @183 :: Task STEP:kmeans/iterations/3/assign@0/1/3/0 hasn't been executed yet
[  INFO  ] 2025-02-18 13:18:25,853 | thinking_executor.executor @193 :: Task finished executing at 2025-02-18 13:18:25.853699
[  INFO  ] 2025-02-18 13:18:25,871 | thinking_executor.executor @183 :: Task STEP:kmeans/iterations/3/recalculate@0/1/3/1 hasn't been executed yet
[  INFO  ] 2025-02-18 13:18:25,915 | thinking_executor.executor @193 :: Task finished executing at 2025-02-18 13:18:25.915824
[  INFO  ] 2025-02-18 13:18:25,929 | thinking_executor.executor @193 :: Task finished executing at 2025-02-18 13:18:25.929787
[  INFO  ] 2025-02-18 13:18:25,943 | thinking_executor.executor @151 :: Task STAGE:kmeans/iterations/3@0/1/3 stopped before finishing (outcome: Result(result=KeyboardInterrupt()))
[  INFO  ] 2025-02-18 13:18:25,943 | thinking_executor.executor @151 :: Task STAGE:kmeans/iterations@0/1 stopped before finishing (outcome: Result(result=KeyboardInterrupt()))
[  INFO  ] 2025-02-18 13:18:25,943 | thinking_executor.executor @151 :: Task STAGE:kmeans@0 stopped before finishing (outcome: Result(result=KeyboardInterrupt()))
```

Now we rerun the app and the executor logs will look like:

```
[  INFO  ] 2025-02-18 13:18:27,633 | thinking_executor.executor @183 :: Task STAGE:kmeans@0 hasn't been executed yet
[  INFO  ] 2025-02-18 13:18:27,638 | thinking_executor.executor @176 :: Task STEP:kmeans/intialize_centroids@0/0 has already been executed on 2025-02-18 13:18:20.989301 (finished on 2025-02-18 13:18:20.992866)
[  INFO  ] 2025-02-18 13:18:27,642 | thinking_executor.executor @183 :: Task STAGE:kmeans/iterations@0/1 hasn't been executed yet
[  INFO  ] 2025-02-18 13:18:27,647 | thinking_executor.executor @176 :: Task STAGE:kmeans/iterations/0@0/1/0 has already been executed on 2025-02-18 13:18:20.996884 (finished on 2025-02-18 13:18:22.205718)
[  INFO  ] 2025-02-18 13:18:27,653 | thinking_executor.executor @176 :: Task STAGE:kmeans/iterations/1@0/1/1 has already been executed on 2025-02-18 13:18:22.212826 (finished on 2025-02-18 13:18:23.415031)
[  INFO  ] 2025-02-18 13:18:27,660 | thinking_executor.executor @176 :: Task STAGE:kmeans/iterations/2@0/1/2 has already been executed on 2025-02-18 13:18:23.435371 (finished on 2025-02-18 13:18:24.664350)
[  INFO  ] 2025-02-18 13:18:27,665 | thinking_executor.executor @176 :: Task STAGE:kmeans/iterations/3@0/1/3 has already been executed on 2025-02-18 13:18:24.678812 (finished on 2025-02-18 13:18:25.929787)
[  INFO  ] 2025-02-18 13:18:27,671 | thinking_executor.executor @183 :: Task STAGE:kmeans/iterations/4@0/1/4 hasn't been executed yet
[  INFO  ] 2025-02-18 13:18:27,687 | thinking_executor.executor @183 :: Task STEP:kmeans/iterations/4/assign@0/1/4/0 hasn't been executed yet
[  INFO  ] 2025-02-18 13:18:28,872 | thinking_executor.executor @193 :: Task finished executing at 2025-02-18 13:18:28.872626
[  INFO  ] 2025-02-18 13:18:28,901 | thinking_executor.executor @183 :: Task STEP:kmeans/iterations/4/recalculate@0/1/4/1 hasn't been executed yet
[  INFO  ] 2025-02-18 13:18:28,957 | thinking_executor.executor @193 :: Task finished executing at 2025-02-18 13:18:28.957265
[  INFO  ] 2025-02-18 13:18:28,974 | thinking_executor.executor @193 :: Task finished executing at 2025-02-18 13:18:28.974000
[  INFO  ] 2025-02-18 13:18:28,995 | thinking_executor.executor @183 :: Task STAGE:kmeans/iterations/5@0/1/5 hasn't been executed yet
[  INFO  ] 2025-02-18 13:18:29,014 | thinking_executor.executor @183 :: Task STEP:kmeans/iterations/5/assign@0/1/5/0 hasn't been executed yet
[  INFO  ] 2025-02-18 13:18:30,226 | thinking_executor.executor @193 :: Task finished executing at 2025-02-18 13:18:30.226595
[  INFO  ] 2025-02-18 13:18:30,265 | thinking_executor.executor @183 :: Task STEP:kmeans/iterations/5/recalculate@0/1/5/1 hasn't been executed yet
[  INFO  ] 2025-02-18 13:18:30,322 | thinking_executor.executor @193 :: Task finished executing at 2025-02-18 13:18:30.322798
[  INFO  ] 2025-02-18 13:18:30,343 | thinking_executor.executor @193 :: Task finished executing at 2025-02-18 13:18:30.343763
[  INFO  ] 2025-02-18 13:18:30,371 | thinking_executor.executor @183 :: Task STAGE:kmeans/iterations/6@0/1/6 hasn't been executed yet
[  INFO  ] 2025-02-18 13:18:30,394 | thinking_executor.executor @183 :: Task STEP:kmeans/iterations/6/assign@0/1/6/0 hasn't been executed yet
[  INFO  ] 2025-02-18 13:18:31,582 | thinking_executor.executor @193 :: Task finished executing at 2025-02-18 13:18:31.582486
[  INFO  ] 2025-02-18 13:18:31,612 | thinking_executor.executor @183 :: Task STEP:kmeans/iterations/6/recalculate@0/1/6/1 hasn't been executed yet
[  INFO  ] 2025-02-18 13:18:31,676 | thinking_executor.executor @193 :: Task finished executing at 2025-02-18 13:18:31.676799
[  INFO  ] 2025-02-18 13:18:31,712 | thinking_executor.executor @193 :: Task finished executing at 2025-02-18 13:18:31.712072
[  INFO  ] 2025-02-18 13:18:31,750 | thinking_executor.executor @183 :: Task STAGE:kmeans/iterations/7@0/1/7 hasn't been executed yet
[  INFO  ] 2025-02-18 13:18:31,777 | thinking_executor.executor @183 :: Task STEP:kmeans/iterations/7/assign@0/1/7/0 hasn't been executed yet
[  INFO  ] 2025-02-18 13:18:32,998 | thinking_executor.executor @193 :: Task finished executing at 2025-02-18 13:18:32.998728
[  INFO  ] 2025-02-18 13:18:33,033 | thinking_executor.executor @183 :: Task STEP:kmeans/iterations/7/recalculate@0/1/7/1 hasn't been executed yet
[  INFO  ] 2025-02-18 13:18:33,098 | thinking_executor.executor @193 :: Task finished executing at 2025-02-18 13:18:33.098633
[  INFO  ] 2025-02-18 13:18:33,122 | thinking_executor.executor @193 :: Task finished executing at 2025-02-18 13:18:33.122926
[  INFO  ] 2025-02-18 13:18:33,157 | thinking_executor.executor @183 :: Task STAGE:kmeans/iterations/8@0/1/8 hasn't been executed yet
[  INFO  ] 2025-02-18 13:18:33,186 | thinking_executor.executor @183 :: Task STEP:kmeans/iterations/8/assign@0/1/8/0 hasn't been executed yet
[  INFO  ] 2025-02-18 13:18:34,402 | thinking_executor.executor @193 :: Task finished executing at 2025-02-18 13:18:34.402814
[  INFO  ] 2025-02-18 13:18:34,443 | thinking_executor.executor @183 :: Task STEP:kmeans/iterations/8/recalculate@0/1/8/1 hasn't been executed yet
[  INFO  ] 2025-02-18 13:18:34,514 | thinking_executor.executor @193 :: Task finished executing at 2025-02-18 13:18:34.514563
[  INFO  ] 2025-02-18 13:18:34,542 | thinking_executor.executor @193 :: Task finished executing at 2025-02-18 13:18:34.542966
[  INFO  ] 2025-02-18 13:18:34,580 | thinking_executor.executor @183 :: Task STAGE:kmeans/iterations/9@0/1/9 hasn't been executed yet
[  INFO  ] 2025-02-18 13:18:34,614 | thinking_executor.executor @183 :: Task STEP:kmeans/iterations/9/assign@0/1/9/0 hasn't been executed yet
[  INFO  ] 2025-02-18 13:18:35,812 | thinking_executor.executor @193 :: Task finished executing at 2025-02-18 13:18:35.812687
[  INFO  ] 2025-02-18 13:18:35,866 | thinking_executor.executor @183 :: Task STEP:kmeans/iterations/9/recalculate@0/1/9/1 hasn't been executed yet
[  INFO  ] 2025-02-18 13:18:35,935 | thinking_executor.executor @193 :: Task finished executing at 2025-02-18 13:18:35.935636
[  INFO  ] 2025-02-18 13:18:35,964 | thinking_executor.executor @193 :: Task finished executing at 2025-02-18 13:18:35.964472
[  INFO  ] 2025-02-18 13:18:36,004 | thinking_executor.executor @193 :: Task finished executing at 2025-02-18 13:18:36.004833
[  INFO  ] 2025-02-18 13:18:36,032 | thinking_executor.executor @193 :: Task finished executing at 2025-02-18 13:18:36.032511
```

Of course if the second session would get interrupted, the third one would skip everything that's been done in the first
and second session.
