#!/usr/bin/python

"""
Singleton

This module defines a "super singleton" class that verifies only once instance
is actually created.  It allows the class designating itself as a singleton to
be inherited, still retains its singletoness, but makes sure that derived classes
aren't created first.

Test classes A -> B -> C where A is a singleton.  B can be created before A, and
calls for A will return the instance of B.  But if B is created, C cannot be created,
since a new C would imply a new instance of B.
"""

from . import debugging

#
#   _SingletonMetaclass
#

class _SingletonMetaclass(type):

    def __init__(cls, *args):
        # no instance created yet
        cls._singleton_instance = None

        # save the current initializer
        old_cls_init = cls.__init__

        # create an initialization trap
        def __init_trap__(self, *args, **kwargs):
            # see if one of these has been created already
            if cls._singleton_instance:
                raise RuntimeError("instance of " + cls.__name__ + " has already been created")

            # initialize as usual
            old_cls_init(self, *args, **kwargs)

            # save this as a created instance
            cls._singleton_instance = self

        # set the trap
        cls.__init__ = __init_trap__

        # continue initializing the class
        super(_SingletonMetaclass, cls).__init__(*args)

    def __call__(cls, *args, **kwargs):
        if cls._singleton_instance is None:
            cls._singleton_instance = super(_SingletonMetaclass, cls).__call__(*args, **kwargs)

        return cls._singleton_instance

#
#   Singleton
#

class Singleton(metaclass=_SingletonMetaclass):

    pass

#
#   _SingletonLoggingMetaclass
#

class _SingletonLoggingMetaclass(_SingletonMetaclass, debugging._LoggingMetaclass):

    pass

class SingletonLogging(metaclass=_SingletonLoggingMetaclass):

    pass
