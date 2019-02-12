#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Setup file for daedalus.
    Use setup.cfg to configure your project.

    This file was generated with PyScaffold 3.1.
    PyScaffold helps you to put up the scaffold of your new Python project.
    Learn more under: https://pyscaffold.org/
"""
import sys

from pkg_resources import require, VersionConflict
from setuptools import setup, find_packages

try:
    require('setuptools>=38.2.4')
except VersionConflict:
    print("Error: version of setuptools is too old (<38.2.4)!")
    sys.exit(1)


if __name__ == "__main__":
    setup(packages=find_packages(exclude=['tests', 'docs', 'dist', 'build']))
