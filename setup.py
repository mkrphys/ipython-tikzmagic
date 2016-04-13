from __future__ import with_statement

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import tikzmagic

classifiers = [
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 3",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: BSD License",
    "Topic :: Scientific/Engineering :: Visualization",
    "Topic :: Software Development :: Libraries",
    "Topic :: Utilities",
    "Framework :: IPython"
]

with open("README.md", "r") as fp:
    long_description = fp.read()

setup(
    name="ipython-tikzmagic",
    version=tikzmagic.__version__,
    author=tikzmagic.__author__,
    url="https://github.com/mkrphys/ipython-tikzmagic",
    py_modules=["tikzmagic"],
    description="IPython magics for generating figures with TikZ",
    long_description=long_description,
    license="BSD",
    classifiers=classifiers
)
