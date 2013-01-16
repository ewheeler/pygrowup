#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
import distribute_setup
distribute_setup.use_setuptools()

from setuptools import setup, find_packages


setup(
    name="pygrowup",
    version=__import__('pygrowup').get_version().replace(' ', '-'),
    license="BSD",

    packages=find_packages(),
    include_package_data=True,

    author="Evan Wheeler",
    author_email="evanmwheeler@gmail.com",

    maintainer="Evan Wheeler",
    maintainer_email="evanmwheeler@gmail.com",

    description="Calculate z-scores of anthropometric measurements based on WHO and CDC child growth standards",
    long_description=open('README').read(),
    url="http://github.com/ewheeler/pygrowup",
    download_url="https://github.com/ewheeler/pygrowup/archive/0.7b0.tar.gz",
    classifiers=[
        'Intended Audience :: Healthcare Industry',
        'Programming Language :: Python :: 2.5',
        'License :: OSI Approved :: BSD License',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
    ],
)
