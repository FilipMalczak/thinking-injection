import sys
from os.path import abspath, dirname, join

#  this piece puts the thinking-injection in repo root, so that one can develop it while using this project as test harness
sys.path.insert(0, abspath(join(dirname(__file__), "..")))