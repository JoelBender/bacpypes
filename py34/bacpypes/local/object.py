#!/usr/bin/env python

from ..debugging import bacpypes_debugging, ModuleLogger

from ..basetypes import PropertyIdentifier
from ..constructeddata import ArrayOf

from ..errors import ExecutionError
from ..object import Property, Object

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# handy reference
ArrayOfPropertyIdentifier = ArrayOf(PropertyIdentifier)

#
#   CurrentPropertyList
#

@bacpypes_debugging
class CurrentPropertyList(Property):

    def __init__(self):
        if _debug: CurrentPropertyList._debug("__init__")
        Property.__init__(self, 'propertyList', ArrayOfPropertyIdentifier, default=None, optional=True, mutable=False)

    def ReadProperty(self, obj, arrayIndex=None):
        if _debug: CurrentPropertyList._debug("ReadProperty %r %r", obj, arrayIndex)

        # make a list of the properties that have values
        property_list = [k for k, v in obj._values.items()
            if v is not None
                and k not in ('objectName', 'objectType', 'objectIdentifier', 'propertyList')
            ]
        if _debug: CurrentPropertyList._debug("    - property_list: %r", property_list)

        # sort the list so it's stable
        property_list.sort()

        # asking for the whole thing
        if arrayIndex is None:
            return ArrayOfPropertyIdentifier(property_list)

        # asking for the length
        if arrayIndex == 0:
            return len(property_list)

        # asking for an index
        if arrayIndex > len(property_list):
            raise ExecutionError(errorClass='property', errorCode='invalidArrayIndex')
        return property_list[arrayIndex - 1]

    def WriteProperty(self, obj, value, arrayIndex=None, priority=None, direct=False):
        raise ExecutionError(errorClass='property', errorCode='writeAccessDenied')

#
#   CurrentPropertyListMixIn
#

@bacpypes_debugging
class CurrentPropertyListMixIn(Object):

    properties = [
        CurrentPropertyList(),
        ]

