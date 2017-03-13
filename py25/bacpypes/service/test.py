#!/usr/bin/env python

"""
Test Service
"""

from ..debugging import bacpypes_debugging, ModuleLogger

# some debugging
_debug = 0
_log = ModuleLogger(globals())

def some_function(*args):
    if _debug: some_function._debug("f %r", args)

    return args[0] + 1

bacpypes_debugging(some_function)