set -x
#the following will make this script fail if the program itself fails
set -e

#./setup.sh >/dev/null 2>/dev/null

source ./venv/bin/activate >/dev/null 2>/dev/null

export SMALL_DATASET=1
export SHORT_RUN=1
python3 ./app.py
