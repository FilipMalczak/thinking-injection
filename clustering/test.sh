set -x
#the following will make this script fail if the program itself fails
set -e

#./setup.sh >/dev/null 2>/dev/null

[ -f ./kmeans.json ] && rm ./kmeans.json || echo "DB not present"

source ./venv/bin/activate >/dev/null 2>/dev/null

export SMALL_DATASET=1
export SHORT_RUN=1

# if you're running on MacOS, you may wanna use gdate instead (after installing coreutils)
# otherwise it may not support %N (nanoseconds)
# in GH Actions the MacOS runner should support it anyway

echo "First run - it should actually execute the experiment"
BEFORE_FIRST=$(date +%s%N)
python3 ./app.py
AFTER_FIRST=$(date +%s%N)
FIRST_DURATION=$(( AFTER_FIRST-BEFORE_FIRST ))
FIRST_DURATION_MS=$(( FIRST_DURATION/1000000 ))
echo "First run took ${FIRST_DURATION_MS}ms"

echo "Second run - shouldn't execute any steps, just confirm that stages structure hasn't changed"
BEFORE_SECOND=$(date +%s%N)
python3 ./app.py
AFTER_SECOND=$(date +%s%N)
SECOND_DURATION=$(( AFTER_SECOND-BEFORE_SECOND ))
SECOND_DURATION_MS=$(( SECOND_DURATION/1000000 ))
echo "Second run took ${SECOND_DURATION_MS}ms"

if [[ $SECOND_DURATION -gt $FIRST_DURATION ]]; then
  echo "Second run was longer than the first!"
  exit 1
fi
echo "Second run was shorter than the first, everythin checks out"
