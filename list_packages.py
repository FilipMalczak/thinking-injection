"""
Simple utility that will list all the packages and subpackages; use it to generate pyproject.toml:tool.setuptools.packages
"""
import json

from thinking_runtime.bootstrap import bootstrap

bootstrap()

from os import listdir
from os.path import dirname, isdir, join

from thinking_modules.model import ModuleName
from thinking_modules.scan import scan

repo_root = dirname(__file__)
root_pkgs = [n for n in listdir(repo_root) if n.startswith("thinking_") and isdir(join(repo_root, n)) and not n.endswith(".egg-info")]


out = set()
for n in root_pkgs:
    name = ModuleName.of(n)
    for scanned in scan(name):
        if scanned.module_descriptor.is_package:
            out.add(scanned.qualified)
print(json.dumps(sorted(out), indent=4))