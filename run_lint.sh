# YOU MUST ACTIVATE VENV ON YOUR OWN IF YOU USE THIS LOCALLY.
set -e

prospector --full-pep8 --with-tool vulture -o text:./lint_report.txt