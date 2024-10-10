import sys
from os.path import abspath, dirname, join

#  this piece puts the thinking-injection in repo root at the beginning of the path,
#  so that one can develop it while using this project as test harness
#
# you should still run setup.sh every now and then to make sure that the transitive dependencies are up to date
sys.path.insert(0, abspath(join(dirname(__file__), "..")))