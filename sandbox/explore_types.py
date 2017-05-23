#!/bin/bash python3

"""
"""

from bacpypes.primitivedata import Enumerated
from bacpypes.constructeddata import Any, Choice, Element, Sequence, SequenceOf

import bacpypes.basetypes

vendor_types = set()

# look for all of the enumerated types that have a vendor range
print('')
print("Enumerated Types with a vendor range")
print('')
for x in dir(bacpypes.basetypes):
    c = getattr(bacpypes.basetypes, x)
    if not isinstance(c, type):
        pass
    elif issubclass(c, Enumerated) and hasattr(c, 'vendor_range'):
        print(c)
        vendor_types.add(c)

# now look for sequences and choices that have an extensible enumeration
print('')
print("Sequences and Choice with an extensible enumeration")
print('')
for x in dir(bacpypes.basetypes):
    c = getattr(bacpypes.basetypes, x)
    if not isinstance(c, type):
        pass
    elif issubclass(c, Sequence):
        for e in c.sequenceElements:
            if e.klass in vendor_types:
                print(c, e.name, e.klass)
                vendor_types.add(c)
    elif issubclass(c, Choice):
        for e in c.choiceElements:
            if e.klass in vendor_types:
                print(c, e.name, e.klass)
                vendor_types.add(c)

import bacpypes.apdu

# look for all of the enumerated types that have a vendor range
print('')
print("Vendor Enumerations in APDU Module")
print('')
for x in dir(bacpypes.apdu):
    c = getattr(bacpypes.apdu, x)
    if not isinstance(c, type):
        pass
    elif issubclass(c, Enumerated) and hasattr(c, 'vendor_range'):
        print(c)
        vendor_types.add(c)

# now look for sequences and choices in APDUs that are one of these
print('')
print("Sequences and Choices with Vendor Enumerations")
print('')
for x in dir(bacpypes.apdu):
    c = getattr(bacpypes.apdu, x)
    if not isinstance(c, type):
        pass
    elif issubclass(c, Sequence):
        for e in c.sequenceElements:
            if e.klass in vendor_types:
                print(c, e.name, e.klass)
    elif issubclass(c, Choice):
        for e in c.choiceElements:
            if e.klass in vendor_types:
                print(c, e.name, e.klass)

