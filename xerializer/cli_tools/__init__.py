
from . import base_functions, numpy_functions  # noqa - Registers the base functions.
from .utils import register, namespace


__all__ = ['register', 'namespace']

"""
Motivation

* Greater flexibility
* Hidden nodes containing meta data
* Simpler code base
* Common type-checking interface
* Python-based syntax for interpolations, transparent to the user.
* Consistent, flexible conventions, easy to remember.
* Plays nicely with ``argparse`` -- can be used to define a parser parameter, or to auto-build a parser.
* Non-intrusive - does not auto-configure logging, does not require a rigid configuration file structure or output file name location.
* Meaningful error messages clearly indicating the node with problems.
"""
