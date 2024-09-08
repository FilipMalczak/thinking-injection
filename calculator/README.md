# calculator

This is an overcomplicated implementation of a reverse polish notation calculator with 4 basic operators.

It's supposed to showcase basic capabilities of `thinking-injection`, being package scan, type discovery, injecting
concrete type and injecting all implementations of an interface.

Bseides being a showcase, it's also a part of test harness, so instead of using published versions uses dependencies
from `develop` branches and locally built version of `thinking-injection`. See [./setup.sh](./setup.sh) for details
of that process.

## Usage:

```shell
cd <repo>/calculator
./setup.sh
source ./venv/bin/activate # setup.sh will create venv if required, but you need to activate it manually
python -m app # will calculate default expression
python -m app 1 2 + 4 '*' 6 # * has a shell meaning, wrap it in '' to avoid unrolling
```