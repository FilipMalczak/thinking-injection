#set -x
#set -e

#./setup.sh >/dev/null 2>/dev/null

source ./venv/bin/activate >/dev/null 2>/dev/null

assert_success(){
  if [ $1 -gt 0 ]; then
    echo "Last command wasn't succesful! Exiting with its result code"
    exit $1
  fi
}

assert_equals(){
#  set +x
  if [ "$1" != "$2" ]; then
    echo "Expected $1"
    echo "Got $2"
    exit 1
  else
    echo "Match: $1"
  fi
#  set -x
}

run(){
  python -m app ${@:1} 2>./log.txt
  result=$?
  if [ $result -gt 0 ]; then
    cat ./log.txt
  else
    rm ./log.txt
  fi
  return $result
}

test_case(){
  txt=$(run ${@:2})
  assert_success $?
  assert_equals "$1" "$txt"
}

test_case '(Value(2.0) + Value(3.0)) = 5.0' 2 3 +
test_case '(((Value(1.0) + Value(2.0)) * Value(4.0)) - Value(5.0)) = 7.0'
test_case '((((Value(-8.0) + Value(6.0)) * Value(-5.0)) - Value(4.0)) / Value(3.0)) = 2.0' -8 6 + -5 '*' 4 - 3 /

