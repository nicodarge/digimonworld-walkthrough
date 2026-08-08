"""Make tools/ importable so `pytest` works from the repo root with no setup.

The build scripts are a flat directory of modules rather than a package -- they
are run as `python tools/build.py`, which puts tools/ on sys.path by itself.
The tests import them directly, so they have to do the same.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
