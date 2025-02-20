import sys
from os.path import abspath, dirname, join

from thinking_runtime.defaults.recognise_runtime import register_facet, facet, envvar

#  this piece puts the thinking-injection in repo root at the beginning of the path,
#  so that one can develop it while using this project as test harness
#
# you should still run setup.sh every now and then to make sure that the transitive dependencies are up to date
# sys.path.insert(0, abspath(join(dirname(__file__), ".."))) #todo uncomment

register_facet(facet("SMALL", envvar("SMALL_DATASET").is_present))
register_facet(facet("SHORT", envvar("SHORT_RUN").is_present))