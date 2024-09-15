#!/usr/bin/zsh
set -e

here="$(realpath $(dirname $0))"

cd $here

if [ ! -d ./venv ]; then
  python3 -m venv ./venv
fi

source ./venv/bin/activate

pip uninstall -y -r ../thinking-dependencies.txt
pip uninstall -y thinking-injection

pip install build

cd ..
./install_develop.sh

#python3 -m build
#
#artifact=$(ls ./dist | grep '.whl' | sort | tail -1)
#
#pip install "./dist/$artifact"



