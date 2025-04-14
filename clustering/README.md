# Clustering

Example project that utilizes executor.

Naively implements a k-means algorithm. Given a pretty large dataset (as found 
[here](https://github.com/deric/clustering-benchmark/blob/master/src/main/resources/datasets/real-world/letter.arff))
and purposefully slow computations each iteration takes significant amount of time. That makes it a perfect example
for using the task executor.

Besides that, the project is a good example of using runtime facets. In [`__setup__.py`](./__setup__.py) we register two
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
[here](./session_2025-04-14 13:49:56.159982.log) and for the second session - [here](./session_2025-04-14 13:51:00.644107.log).
The [./kmeans.json](./kmeans.json) file is the TinyDB JSON file used by executor for tracking sessions and tasks.

> TinyDB doesn't pretty print JSONs out of the box, so be prepared for a looooong line of data. 
> Use some [pretty printer](https://jsonformatter.org/json-pretty-print) for easier reading.
> 
> For the sake of simplicity the clustering algorithm is using the same DB for storing centroids and assignment data.
> That doesn't need to be the case. [Other `thinking` projects](../thinking_executor_data) provide (or will provide) 
> integration with version-controlled databases.

Here are the logs of the executor for the first run (the interrupted one):
```
(...)
[  INFO  ] 2025-04-14 13:49:56,358 | thinking_executor.executor @198 :: Task STAGE:kmeans@0 hasn't been executed yet
[  INFO  ] 2025-04-14 13:49:56,358 | thinking_executor.executor @198 :: Task STEP:kmeans/intialize_centroids@0/0 hasn't been executed yet
[  INFO  ] 2025-04-14 13:49:56,365 | thinking_executor.executor @211 :: Task finished executing at 2025-04-14 13:49:56.365711
[  INFO  ] 2025-04-14 13:49:56,369 | thinking_executor.executor @198 :: Task STAGE:kmeans/iterations@0/1 hasn't been executed yet
[  INFO  ] 2025-04-14 13:49:56,370 | thinking_executor.executor @198 :: Task STAGE:kmeans/iterations/0@0/1/0 hasn't been executed yet
[  INFO  ] 2025-04-14 13:49:56,371 | thinking_executor.executor @198 :: Task STEP:kmeans/iterations/0/assign@0/1/0/0 hasn't been executed yet
[  INFO  ] 2025-04-14 13:49:57,439 | thinking_executor.executor @211 :: Task finished executing at 2025-04-14 13:49:57.439117
[  INFO  ] 2025-04-14 13:49:57,446 | thinking_executor.executor @198 :: Task STEP:kmeans/iterations/0/recalculate@0/1/0/1 hasn't been executed yet
[  INFO  ] 2025-04-14 13:49:57,479 | thinking_executor.executor @211 :: Task finished executing at 2025-04-14 13:49:57.479189
[  INFO  ] 2025-04-14 13:49:57,485 | thinking_executor.executor @211 :: Task finished executing at 2025-04-14 13:49:57.485427
[  INFO  ] 2025-04-14 13:49:57,499 | thinking_executor.executor @198 :: Task STAGE:kmeans/iterations/1@0/1/1 hasn't been executed yet
[  INFO  ] 2025-04-14 13:49:57,506 | thinking_executor.executor @198 :: Task STEP:kmeans/iterations/1/assign@0/1/1/0 hasn't been executed yet
[  INFO  ] 2025-04-14 13:49:58,541 | thinking_executor.executor @211 :: Task finished executing at 2025-04-14 13:49:58.541775
[  INFO  ] 2025-04-14 13:49:58,552 | thinking_executor.executor @198 :: Task STEP:kmeans/iterations/1/recalculate@0/1/1/1 hasn't been executed yet
[  INFO  ] 2025-04-14 13:49:58,592 | thinking_executor.executor @211 :: Task finished executing at 2025-04-14 13:49:58.592720
[  INFO  ] 2025-04-14 13:49:58,601 | thinking_executor.executor @211 :: Task finished executing at 2025-04-14 13:49:58.601151
[  INFO  ] 2025-04-14 13:49:58,611 | thinking_executor.executor @198 :: Task STAGE:kmeans/iterations/2@0/1/2 hasn't been executed yet
[  INFO  ] 2025-04-14 13:49:58,618 | thinking_executor.executor @198 :: Task STEP:kmeans/iterations/2/assign@0/1/2/0 hasn't been executed yet
[  INFO  ] 2025-04-14 13:49:59,669 | thinking_executor.executor @211 :: Task finished executing at 2025-04-14 13:49:59.669810
[  INFO  ] 2025-04-14 13:49:59,684 | thinking_executor.executor @198 :: Task STEP:kmeans/iterations/2/recalculate@0/1/2/1 hasn't been executed yet
[  INFO  ] 2025-04-14 13:49:59,746 | thinking_executor.executor @211 :: Task finished executing at 2025-04-14 13:49:59.746173
[  INFO  ] 2025-04-14 13:49:59,757 | thinking_executor.executor @211 :: Task finished executing at 2025-04-14 13:49:59.757787
[  INFO  ] 2025-04-14 13:49:59,772 | thinking_executor.executor @198 :: Task STAGE:kmeans/iterations/3@0/1/3 hasn't been executed yet
[  INFO  ] 2025-04-14 13:49:59,783 | thinking_executor.executor @198 :: Task STEP:kmeans/iterations/3/assign@0/1/3/0 hasn't been executed yet
[ ERROR  ] 2025-04-14 13:50:00,311 | thinking_executor.executor @164 :: Task STEP:kmeans/iterations/3/assign@0/1/3/0 stopped before finishing (outcome: Result(result=KeyboardInterrupt()))
[ ERROR  ] 2025-04-14 13:50:00,311 | thinking_executor.executor @164 :: Task STAGE:kmeans/iterations/3@0/1/3 stopped before finishing (outcome: Result(result=KeyboardInterrupt()))
[ ERROR  ] 2025-04-14 13:50:00,312 | thinking_executor.executor @164 :: Task STAGE:kmeans/iterations@0/1 stopped before finishing (outcome: Result(result=KeyboardInterrupt()))
[ ERROR  ] 2025-04-14 13:50:00,312 | thinking_executor.executor @164 :: Task STAGE:kmeans@0 stopped before finishing (outcome: Result(result=KeyboardInterrupt()))
(...)
```

Now we rerun the app and the executor logs will look like:

```
(...)
[  INFO  ] 2025-04-14 13:51:00,901 | thinking_executor.executor @198 :: Task STAGE:kmeans@0 hasn't been executed yet
[  INFO  ] 2025-04-14 13:51:00,905 | thinking_executor.executor @189 :: Task STEP:kmeans/intialize_centroids@0/0 has already been executed on 2025-04-14 13:49:56.358554 (finished on 2025-04-14 13:49:56.365711)
[  INFO  ] 2025-04-14 13:51:00,909 | thinking_executor.executor @198 :: Task STAGE:kmeans/iterations@0/1 hasn't been executed yet
[  INFO  ] 2025-04-14 13:51:00,913 | thinking_executor.executor @200 :: Task STAGE:kmeans/iterations/0@0/1/0 has already been executed on 2025-04-14 13:49:56.370219 (finished on 2025-04-14 13:49:57.485427)
[  INFO  ] 2025-04-14 13:51:00,913 | thinking_executor.executor @201 :: Rerunning STAGE:kmeans/iterations/0@0/1/0 nontheless, as it is a stage
[  INFO  ] 2025-04-14 13:51:00,924 | thinking_executor.executor @189 :: Task STEP:kmeans/iterations/0/assign@0/1/0/0 has already been executed on 2025-04-14 13:49:56.371286 (finished on 2025-04-14 13:49:57.439117)
[  INFO  ] 2025-04-14 13:51:00,928 | thinking_executor.executor @189 :: Task STEP:kmeans/iterations/0/recalculate@0/1/0/1 has already been executed on 2025-04-14 13:49:57.446226 (finished on 2025-04-14 13:49:57.479189)
[  INFO  ] 2025-04-14 13:51:00,928 | thinking_executor.executor @211 :: Task finished executing at 2025-04-14 13:51:00.928331
[  INFO  ] 2025-04-14 13:51:00,932 | thinking_executor.executor @200 :: Task STAGE:kmeans/iterations/1@0/1/1 has already been executed on 2025-04-14 13:49:57.499860 (finished on 2025-04-14 13:49:58.601151)
[  INFO  ] 2025-04-14 13:51:00,932 | thinking_executor.executor @201 :: Rerunning STAGE:kmeans/iterations/1@0/1/1 nontheless, as it is a stage
[  INFO  ] 2025-04-14 13:51:00,942 | thinking_executor.executor @189 :: Task STEP:kmeans/iterations/1/assign@0/1/1/0 has already been executed on 2025-04-14 13:49:57.506633 (finished on 2025-04-14 13:49:58.541775)
[  INFO  ] 2025-04-14 13:51:00,946 | thinking_executor.executor @189 :: Task STEP:kmeans/iterations/1/recalculate@0/1/1/1 has already been executed on 2025-04-14 13:49:58.552972 (finished on 2025-04-14 13:49:58.592720)
[  INFO  ] 2025-04-14 13:51:00,946 | thinking_executor.executor @211 :: Task finished executing at 2025-04-14 13:51:00.946640
[  INFO  ] 2025-04-14 13:51:00,950 | thinking_executor.executor @200 :: Task STAGE:kmeans/iterations/2@0/1/2 has already been executed on 2025-04-14 13:49:58.611865 (finished on 2025-04-14 13:49:59.757787)
[  INFO  ] 2025-04-14 13:51:00,950 | thinking_executor.executor @201 :: Rerunning STAGE:kmeans/iterations/2@0/1/2 nontheless, as it is a stage
[  INFO  ] 2025-04-14 13:51:00,961 | thinking_executor.executor @189 :: Task STEP:kmeans/iterations/2/assign@0/1/2/0 has already been executed on 2025-04-14 13:49:58.618650 (finished on 2025-04-14 13:49:59.669810)
[  INFO  ] 2025-04-14 13:51:00,964 | thinking_executor.executor @189 :: Task STEP:kmeans/iterations/2/recalculate@0/1/2/1 has already been executed on 2025-04-14 13:49:59.684699 (finished on 2025-04-14 13:49:59.746173)
[  INFO  ] 2025-04-14 13:51:00,965 | thinking_executor.executor @211 :: Task finished executing at 2025-04-14 13:51:00.965071
[  INFO  ] 2025-04-14 13:51:00,968 | thinking_executor.executor @198 :: Task STAGE:kmeans/iterations/3@0/1/3 hasn't been executed yet
[  INFO  ] 2025-04-14 13:51:00,979 | thinking_executor.executor @198 :: Task STEP:kmeans/iterations/3/assign@0/1/3/0 hasn't been executed yet
[  INFO  ] 2025-04-14 13:51:02,059 | thinking_executor.executor @211 :: Task finished executing at 2025-04-14 13:51:02.059471
[  INFO  ] 2025-04-14 13:51:02,083 | thinking_executor.executor @198 :: Task STEP:kmeans/iterations/3/recalculate@0/1/3/1 hasn't been executed yet
[  INFO  ] 2025-04-14 13:51:02,142 | thinking_executor.executor @211 :: Task finished executing at 2025-04-14 13:51:02.142356
[  INFO  ] 2025-04-14 13:51:02,156 | thinking_executor.executor @211 :: Task finished executing at 2025-04-14 13:51:02.156251
[  INFO  ] 2025-04-14 13:51:02,174 | thinking_executor.executor @198 :: Task STAGE:kmeans/iterations/4@0/1/4 hasn't been executed yet
[  INFO  ] 2025-04-14 13:51:02,190 | thinking_executor.executor @198 :: Task STEP:kmeans/iterations/4/assign@0/1/4/0 hasn't been executed yet
[  INFO  ] 2025-04-14 13:51:03,268 | thinking_executor.executor @211 :: Task finished executing at 2025-04-14 13:51:03.268021
[  INFO  ] 2025-04-14 13:51:03,290 | thinking_executor.executor @198 :: Task STEP:kmeans/iterations/4/recalculate@0/1/4/1 hasn't been executed yet
[  INFO  ] 2025-04-14 13:51:03,353 | thinking_executor.executor @211 :: Task finished executing at 2025-04-14 13:51:03.353740
[  INFO  ] 2025-04-14 13:51:03,370 | thinking_executor.executor @211 :: Task finished executing at 2025-04-14 13:51:03.370514
[  INFO  ] 2025-04-14 13:51:03,405 | thinking_executor.executor @198 :: Task STAGE:kmeans/iterations/5@0/1/5 hasn't been executed yet
[  INFO  ] 2025-04-14 13:51:03,422 | thinking_executor.executor @198 :: Task STEP:kmeans/iterations/5/assign@0/1/5/0 hasn't been executed yet
[  INFO  ] 2025-04-14 13:51:04,517 | thinking_executor.executor @211 :: Task finished executing at 2025-04-14 13:51:04.517427
[  INFO  ] 2025-04-14 13:51:04,543 | thinking_executor.executor @198 :: Task STEP:kmeans/iterations/5/recalculate@0/1/5/1 hasn't been executed yet
[  INFO  ] 2025-04-14 13:51:04,612 | thinking_executor.executor @211 :: Task finished executing at 2025-04-14 13:51:04.612493
[  INFO  ] 2025-04-14 13:51:04,631 | thinking_executor.executor @211 :: Task finished executing at 2025-04-14 13:51:04.631055
[  INFO  ] 2025-04-14 13:51:04,665 | thinking_executor.executor @198 :: Task STAGE:kmeans/iterations/6@0/1/6 hasn't been executed yet
[  INFO  ] 2025-04-14 13:51:04,690 | thinking_executor.executor @198 :: Task STEP:kmeans/iterations/6/assign@0/1/6/0 hasn't been executed yet
[  INFO  ] 2025-04-14 13:51:05,780 | thinking_executor.executor @211 :: Task finished executing at 2025-04-14 13:51:05.780053
[  INFO  ] 2025-04-14 13:51:05,821 | thinking_executor.executor @198 :: Task STEP:kmeans/iterations/6/recalculate@0/1/6/1 hasn't been executed yet
[  INFO  ] 2025-04-14 13:51:05,896 | thinking_executor.executor @211 :: Task finished executing at 2025-04-14 13:51:05.896647
[  INFO  ] 2025-04-14 13:51:05,919 | thinking_executor.executor @211 :: Task finished executing at 2025-04-14 13:51:05.919179
[  INFO  ] 2025-04-14 13:51:05,950 | thinking_executor.executor @198 :: Task STAGE:kmeans/iterations/7@0/1/7 hasn't been executed yet
[  INFO  ] 2025-04-14 13:51:05,973 | thinking_executor.executor @198 :: Task STEP:kmeans/iterations/7/assign@0/1/7/0 hasn't been executed yet
[  INFO  ] 2025-04-14 13:51:07,073 | thinking_executor.executor @211 :: Task finished executing at 2025-04-14 13:51:07.073695
[  INFO  ] 2025-04-14 13:51:07,121 | thinking_executor.executor @198 :: Task STEP:kmeans/iterations/7/recalculate@0/1/7/1 hasn't been executed yet
[  INFO  ] 2025-04-14 13:51:07,203 | thinking_executor.executor @211 :: Task finished executing at 2025-04-14 13:51:07.203750
[  INFO  ] 2025-04-14 13:51:07,228 | thinking_executor.executor @211 :: Task finished executing at 2025-04-14 13:51:07.228322
[  INFO  ] 2025-04-14 13:51:07,260 | thinking_executor.executor @198 :: Task STAGE:kmeans/iterations/8@0/1/8 hasn't been executed yet
[  INFO  ] 2025-04-14 13:51:07,286 | thinking_executor.executor @198 :: Task STEP:kmeans/iterations/8/assign@0/1/8/0 hasn't been executed yet
[  INFO  ] 2025-04-14 13:51:08,387 | thinking_executor.executor @211 :: Task finished executing at 2025-04-14 13:51:08.387818
[  INFO  ] 2025-04-14 13:51:08,434 | thinking_executor.executor @198 :: Task STEP:kmeans/iterations/8/recalculate@0/1/8/1 hasn't been executed yet
[  INFO  ] 2025-04-14 13:51:08,535 | thinking_executor.executor @211 :: Task finished executing at 2025-04-14 13:51:08.535775
[  INFO  ] 2025-04-14 13:51:08,575 | thinking_executor.executor @211 :: Task finished executing at 2025-04-14 13:51:08.575204
[  INFO  ] 2025-04-14 13:51:08,611 | thinking_executor.executor @198 :: Task STAGE:kmeans/iterations/9@0/1/9 hasn't been executed yet
[  INFO  ] 2025-04-14 13:51:08,641 | thinking_executor.executor @198 :: Task STEP:kmeans/iterations/9/assign@0/1/9/0 hasn't been executed yet
[  INFO  ] 2025-04-14 13:51:09,746 | thinking_executor.executor @211 :: Task finished executing at 2025-04-14 13:51:09.746080
[  INFO  ] 2025-04-14 13:51:09,797 | thinking_executor.executor @198 :: Task STEP:kmeans/iterations/9/recalculate@0/1/9/1 hasn't been executed yet
[  INFO  ] 2025-04-14 13:51:09,891 | thinking_executor.executor @211 :: Task finished executing at 2025-04-14 13:51:09.891729
[  INFO  ] 2025-04-14 13:51:09,920 | thinking_executor.executor @211 :: Task finished executing at 2025-04-14 13:51:09.920911
[  INFO  ] 2025-04-14 13:51:09,951 | thinking_executor.executor @211 :: Task finished executing at 2025-04-14 13:51:09.951276
[  INFO  ] 2025-04-14 13:51:09,993 | thinking_executor.executor @211 :: Task finished executing at 2025-04-14 13:51:09.993607
(...)
```

Of course if the second session would get interrupted, the third one would skip everything that's been done in the first
and second session.

### Niceties and post mortem investigations

Logs aren't the only tool that can be useful to you.

To understand what happened and when, we store metadata of each run. We are keeping track of runtime sessions (in other
words, python process runtimes), context sessions (DI context lifecycles; single runtime session may consist of 
multiple context sessions, even though it will usually be single context session per runtime session) and we track which
was the last runtime session. If you open [./kmeans.json](./kmeans.json), you'll see something like:

> Again, in case of this example project we are using same TinyDB file for execution metadata and experiment data. Have
> a look at [`thinking_executor_data`](../thinking_executor_data) for a better way to do this.
> 
> Remember NOT TO modify these objects by hand - they are reference for the executor infrastructure, if you break 
> something, you won't be able to easily fix things.
> 
> Besides, TinyDB doesn't pretty-print JSON by default, so what you'll find in the DB will differ in formatting.

```json
{
  "runtime-sessions": {
    "1": {
      "sid": "357f3b64-402f-4c3c-b3c2-885a31e1e21e",
      "metadata": {
        "runtime": {
          "mode": "APP",
          "active_facet_names": [ "SHORT" ],
          "started_on": 1744631396.159982
        },
        "hostname": "(...)",
        "pid": 111363
      },
      "context_sessions": {
        "0": {
          "session_no": 0,
          "sanitized": true,
          "started_on": 1744631396.30448,
          "invoked_steps": [
            {
              "path": [ "kmeans", "intialize_centroids" ],
              "order": [ 0, 0 ],
              "task_type": "STEP"
            },
            {
              "path": [ "kmeans", "iterations", 0, "assign" ],
              "order": [ 0, 1, 0, 0 ],
              "task_type": "STEP"
            },
            {
              "path": [ "kmeans", "iterations", 0, "recalculate" ],
              "order": [ 0, 1, 0, 1 ],
              "task_type": "STEP"
            },
            {
              "path": [ "kmeans", "iterations", 1, "assign" ],
              "order": [ 0, 1, 1, 0 ],
              "task_type": "STEP"
            },
            {
              "path": [ "kmeans", "iterations", 1, "recalculate" ],
              "order": [ 0, 1, 1, 1 ],
              "task_type": "STEP"
            },
            {
              "path": [ "kmeans",  "iterations", 2, "assign" ],
              "order": [ 0, 1, 2, 0 ],
              "task_type": "STEP"
            },
            {
              "path": [ "kmeans", "iterations", 2, "recalculate" ],
              "order": [ 0, 1, 2, 1],
              "task_type": "STEP"
            },
            {
              "path": [ "kmeans", "iterations", 3, "assign" ],
              "order": [ 0, 1, 3, 0 ],
              "task_type": "STEP"
            }
          ]
        }
      }
    },
    "2": {
      "sid": "cc6a7e84-c3b5-418f-a0e0-3a8820fac05b",
      "metadata": {
        "runtime": {
          "mode": "APP",
          "active_facet_names": [
            "SHORT"
          ],
          "started_on": 1744631460.644107
        },
        "hostname": "(...)",
        "pid": 111462
      },
      "context_sessions": {
        "0": {
          "session_no": 0,
          "sanitized": true,
          "started_on": 1744631460.835147,
          "invoked_steps": [
            {
              "path": [ "kmeans", "iterations", 3, "assign" ],
              "order": [ 0, 1, 3, 0 ],
              "task_type": "STEP"
            },
            {
              "path": [ "kmeans", "iterations", 3, "recalculate" ],
              "order": [ 0, 1, 3, 1 ],
              "task_type": "STEP"
            },
            {
              "path": [ "kmeans", "iterations", 4, "assign" ],
              "order": [ 0, 1, 4, 0 ],
              "task_type": "STEP"
            },
            {
              "path": [ "kmeans", "iterations", 4, "recalculate" ],
              "order": [ 0, 1, 4, 1 ],
              "task_type": "STEP"
            },
            {
              "path": [ "kmeans", "iterations", 5, "assign" ],
              "order": [ 0, 1, 5, 0 ],
              "task_type": "STEP"
            },
            {
              "path": [ "kmeans", "iterations", 5, "recalculate" ],
              "order": [ 0, 1, 5, 1 ],
              "task_type": "STEP"
            },
            {
              "path": [ "kmeans", "iterations", 6, "assign" ],
              "order": [ 0, 1, 6, 0 ],
              "task_type": "STEP"
            },
            {
              "path": [ "kmeans", "iterations", 6, "recalculate" ],
              "order": [ 0, 1, 6, 1 ],
              "task_type": "STEP"
            },
            {
              "path": [ "kmeans", "iterations", 7, "assign" ],
              "order": [ 0, 1, 7, 0 ],
              "task_type": "STEP"
            },
            {
              "path": [ "kmeans", "iterations", 7, "recalculate" ],
              "order": [ 0, 1, 7, 1 ],
              "task_type": "STEP"
            },
            {
              "path": [ "kmeans", "iterations", 8, "assign" ],
              "order": [ 0, 1, 8, 0 ],
              "task_type": "STEP"
            },
            {
              "path": [ "kmeans", "iterations", 8, "recalculate" ],
              "order": [ 0, 1, 8, 1 ],
              "task_type": "STEP"
            },
            {
              "path": [ "kmeans", "iterations", 9, "assign" ],
              "order": [ 0, 1, 9, 0 ],
              "task_type": "STEP"
            },
            {
              "path": [ "kmeans", "iterations", 9, "recalculate" ],
              "order": [0, 1, 9, 1 ],
              "task_type": "STEP"
            }
          ]
        }
      }
    }
  },
  "globals": {
    "1": {
      "sid": "cc6a7e84-c3b5-418f-a0e0-3a8820fac05b",
      "__type_id__": "thinking_executor.globals_manager.LastSession"
    }
  }
}
```