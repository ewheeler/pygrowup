#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
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
    download_url="https://github.com/ewheeler/pygrowup/archive/0.8.2.tar.gz",
    install_requires=[
        "six",
    ],
    classifiers=[
        'Intended Audience :: Healthcare Industry',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: BSD License',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
    ],
)
