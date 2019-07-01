#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name="inginious-stats",
    version="0.1dev0",
    description="Plugin to add demo an improved statistic page in course administration",
    packages=find_packages(),
    install_requires=["inginious>=0.5.dev0"],
    tests_require=[],
    extras_require={},
    scripts=[],
    include_package_data=True,
    author="OpenWeek 2019",
    author_email="openweek@listes.uclouvain.be",
    license="AGPL 3",
    url="https://github.com/OpenWeek/inginious-stats"
)