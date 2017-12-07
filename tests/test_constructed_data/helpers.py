#!/usr/bin/python

"""
Helper classes for constructed data tests.
"""

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, xtob

from bacpypes.errors import MissingRequiredParameter
from bacpypes.primitivedata import Boolean, Integer, Tag, TagList
from bacpypes.constructeddata import Element, Sequence

# some debugging
_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
class SequenceEquality:

    """
    This mixin class adds an equality function for matching values for all of
    the elements, even if they are optional.  It will raise an exception for
    missing elements, even if they are missing in both objects.
    """

    def __eq__(self, other):
        if _debug: SequenceEquality._debug("__eq__ %r", other)

        # loop through this sequences elements
        for element in self.sequenceElements:
            self_value = getattr(self, element.name, None)
            other_value = getattr(other, element.name, None)

            if (not element.optional) and ((self_value is None) or (other_value is None)):
                raise MissingRequiredParameter("%s is a missing required element of %s" % (element.name, self.__class__.__name__))
            if not (self_value == other_value):
                return False

        # success
        return True


@bacpypes_debugging
class EmptySequence(Sequence, SequenceEquality):

    def __init__(self, *args, **kwargs):
        if _debug: EmptySequence._debug("__init__ %r %r", args, kwargs)
        Sequence.__init__(self, *args, **kwargs)


@bacpypes_debugging
class SimpleSequence(Sequence, SequenceEquality):

    sequenceElements = [
        Element('hydrogen', Boolean),
        ]

    def __init__(self, *args, **kwargs):
        if _debug: SimpleSequence._debug("__init__ %r %r", args, kwargs)
        Sequence.__init__(self, *args, **kwargs)


@bacpypes_debugging
class CompoundSequence1(Sequence, SequenceEquality):

    sequenceElements = [
        Element('hydrogen', Boolean),
        Element('helium', Integer),
        ]

    def __init__(self, *args, **kwargs):
        if _debug: CompoundSequence1._debug("__init__ %r %r", args, kwargs)
        Sequence.__init__(self, *args, **kwargs)


@bacpypes_debugging
class CompoundSequence2(Sequence, SequenceEquality):

    sequenceElements = [
        Element('lithium', Boolean, optional=True),
        Element('beryllium', Integer),
        ]

    def __init__(self, *args, **kwargs):
        if _debug: CompoundSequence2._debug("__init__ %r %r", args, kwargs)
        Sequence.__init__(self, *args, **kwargs)

