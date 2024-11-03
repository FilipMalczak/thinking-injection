# YOU MUST ACTIVATE VENV ON YOUR OWN IF YOU USE THIS LOCALLY.
prospector --profile project-profile \
  -o text:./lint_report.txt \
  -o xunit:./lint_report.xml \
  --zero-exit
RESULT=$?
echo "== LINT REPORT =="
cat ./lint_report.txt
echo "-- /LINT REPORT --"
exit $RESULT