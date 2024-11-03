# YOU MUST ACTIVATE VENV ON YOUR OWN IF YOU USE THIS LOCALLY.
prospector --full-pep8 \
  --with-tool vulture \
  --ignore-paths calculator \
  -o text:./lint_report.txt \
  -o xunit:./lint_report.xml \
  --zero-exit