#!/usr/bin/env python

import os
import re

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

base_path = os.path.dirname(__file__)

# Get the version (borrowed from SQLAlchemy)
with open(os.path.join(base_path, "src", "urllib3", "_version.py")) as fp:
    version = (
        re.compile(r""".*__version__ = ["'](.*?)['"]""", re.S).match(fp.read()).group(1)
    )

setup(
    name='timeseries-db-lib',
    version=version,
    author='Eduard Stefano',
    author_email='eduard.gorohovski@dupont.com',
    description='A python package for normalization calculations from timeseries data',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/DWPSoftwares/normalization-lib',
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Unlicensed",
        "Operating System :: OS Independent",
    ]
)