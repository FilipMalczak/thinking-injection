
from thinking_runtime.bootstrap import bootstrap

bootstrap()

if __name__=="__main__":
    from thinking_injection.context.simple import SimpleContext
    from thinking_injection.typeset import from_package

    from kmeans.clusterizer import Clusterizer

    ctx = SimpleContext(from_package("kmeans"))
    with ctx.lifecycle() as index:
        clusterizer = index.instance(Clusterizer)
        print(clusterizer.run())

