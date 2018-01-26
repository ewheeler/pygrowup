import os
import os.path
from setuptools import setup, find_packages


def get_readme(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="pygrowup",
    version=__import__('pygrowup').get_version().replace(' ', '-'),
    packages=find_packages(),

    install_requires=[
            'unittest2;python_version<"3.4"',
        ],

    author="Jon Baldivieso",
    author_email="jbaldivieso@gmail.com",

    maintainer="Jon Baldivieso",
    maintainer_email="jbaldivieso@gmail.com",

    description="Calculate z-scores of anthropometric measurements based on "
    "WHO child growth standards",
    # long_description=get_readme('README.md'),
    license="GPLv3",
    url="https://github.org/jbaldivieso/pygrowup2",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
    ],
)
