#This script will install requirements from thinking family from develop branch on GitHub if they aren't installed yet.
# Should work with bash too, shebang is aligned with my machine (running Linux Mint).
# Used mainly in CI.
# YOU MUST ACTIVATE VENV ON YOUR OWN IF YOU USE THIS LOCALLY.
set -e

for r in $(cat ./thinking-dependencies.txt)
do
  echo "Installing $r from develop branch"
  pip install "https://github.com/FilipMalczak/$r/archive/develop.zip"
done