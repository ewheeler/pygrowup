#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from setuptools import setup, find_packages


setup(
    name="pygrowup",
    version="0.4",
    license="BSD",

    packages = find_packages(),
    include_package_data = True,

    author="Evan Wheeler",
    author_email="evanmwheeler@gmail.com",

    maintainer="Evan Wheeler",
    maintainer_email="evanmwheeler@gmail.com",

    description="Calculate z-scores of anthropometric measurements based on the WHO Child Growth Standards",
    url="http://github.com/ewheeler/pygrowup"
)
