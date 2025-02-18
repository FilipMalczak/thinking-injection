set -x
#the following will make this script fail if the program itself fails
set -e

#./setup.sh >/dev/null 2>/dev/null

[ -f ./kmeans.json ] && rm ./kmeans.json || echo "DB not present"

source ./venv/bin/activate >/dev/null 2>/dev/null

export SMALL_DATASET=1

echo "First run - it should actually execute the experiment"
BEFORE_FIRST=$(date +%s)
python3 ./app.py
AFTER_FIRST=$(date +%s)
FIRST_DURATION=$(( AFTER_FIRST-BEFORE_FIRST ))
echo "First run took ${FIRST_DURATION}s"

echo "Second run - shouldn't execute any steps, just confirm that stages structure hasn't changed"
BEFORE_SECOND=$(date +%s)
python3 ./app.py
AFTER_SECOND=$(date +%s)
SECOND_DURATION=$(( AFTER_SECOND-BEFORE_SECOND ))
echo "Second run took ${SECOND_DURATION}s"

if [[ $SECOND_DURATION -gt $FIRST_DURATION ]]; then
  echo "Second run was longer than the first!"
  exit 1
fi
echo "Second run was shorter than the first, everythin checks out"
