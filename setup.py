# !/usr/bin/env python

from setuptools import setup, find_packages

with open("README.md") as f:
    long_description = f.read()


setup(
    name="xerializer",
    packages=find_packages(".", exclude=["tests"]),
    version="0.1.0",
    description="",
    install_requires=["numpy", "pytz", "hydra-core", "frozendict", "jztools"],
    author="Joaquin Zepeda",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/zepedaj/xerializer",
)
