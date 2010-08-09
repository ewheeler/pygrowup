#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from setuptools import setup, find_packages


setup(
    name="PyGrowup",
    version="0.2",
    license="BSD",

    py_modules = ["pygrowup"],

    data_files=[("tables", ['tables/lhfa_boys_2_5_zscores.json',\
        'tables/lhfa_girls_2_5_zscores.json',\
        'tables/wfh_boys_2_5_zscores.json',\
        'tables/wfl_girls_0_2_zscores.json',\
        'tables/lhfa_boys_0_2_zscores.json',\
        'tables/lhfa_girls_0_2_zscores.json',\
        'tables/wfa_boys_0_5_zscores.json',\
        'tables/wfh_girls_2_5_zscores.json',\
        'tables/lhfa_boys_0_5_zscores.json',\
        'tables/lhfa_girls_0_5_zscores.json',\
        'tables/wfa_girls_0_5_zscores.json',\
        'tables/wfl_boys_0_2_zscores.json']),\
        ("", ['test.csv'])],

    author="Evan Wheeler",
    author_email="evanmwheeler@gmail.com",

    maintainer="Evan Wheeler",
    maintainer_email="evanmwheeler@gmail.com",

    description="Calculate z-scores of anthropometric measurements based on the WHO Child Growth Standards",
    url="http://github.com/ewheeler/pygrowup"
)
