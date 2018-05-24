#!/usr/bin/env python

from ..debugging import bacpypes_debugging, ModuleLogger

from ..primitivedata import Null, Boolean, Unsigned, Integer, Real, Double, \
    OctetString, CharacterString, BitString, Enumerated, Date, Time, \
    ObjectIdentifier
from ..constructeddata import ArrayOf
from ..basetypes import ServicesSupported

from ..errors import ExecutionError
from ..object import register_object_type, registered_object_types, \
    Property, DeviceObject

from .object import CurrentPropertyListMixIn

# some debugging
_debug = 0
_log = ModuleLogger(globals())

#
#   CurrentLocalDate
#

class CurrentLocalDate(Property):

    def __init__(self):
        Property.__init__(self, 'localDate', Date, default=(), optional=True, mutable=False)

    def ReadProperty(self, obj, arrayIndex=None):
        if arrayIndex is not None:
            raise ExecutionError(errorClass='property', errorCode='propertyIsNotAnArray')

        # get the value
        now = Date()
        now.now()
        return now.value

    def WriteProperty(self, obj, value, arrayIndex=None, priority=None, direct=False):
        raise ExecutionError(errorClass='property', errorCode='writeAccessDenied')

#
#   CurrentLocalTime
#

class CurrentLocalTime(Property):

    def __init__(self):
        Property.__init__(self, 'localTime', Time, default=(), optional=True, mutable=False)

    def ReadProperty(self, obj, arrayIndex=None):
        if arrayIndex is not None:
            raise ExecutionError(errorClass='property', errorCode='propertyIsNotAnArray')

        # get the value
        now = Time()
        now.now()
        return now.value

    def WriteProperty(self, obj, value, arrayIndex=None, priority=None, direct=False):
        raise ExecutionError(errorClass='property', errorCode='writeAccessDenied')

#
#   CurrentProtocolServicesSupported
#

@bacpypes_debugging
class CurrentProtocolServicesSupported(Property):

    def __init__(self):
        if _debug: CurrentProtocolServicesSupported._debug("__init__")
        Property.__init__(self, 'protocolServicesSupported', ServicesSupported, default=None, optional=True, mutable=False)

    def ReadProperty(self, obj, arrayIndex=None):
        if _debug: CurrentProtocolServicesSupported._debug("ReadProperty %r %r", obj, arrayIndex)

        # not an array
        if arrayIndex is not None:
            raise ExecutionError(errorClass='property', errorCode='propertyIsNotAnArray')

        # return what the application says
        return obj._app.get_services_supported()

    def WriteProperty(self, obj, value, arrayIndex=None, priority=None, direct=False):
        raise ExecutionError(errorClass='property', errorCode='writeAccessDenied')

#
#   LocalDeviceObject
#

@bacpypes_debugging
class LocalDeviceObject(CurrentPropertyListMixIn, DeviceObject):

    properties = [
        CurrentLocalTime(),
        CurrentLocalDate(),
        CurrentProtocolServicesSupported(),
        ]

    defaultProperties = \
        { 'maxApduLengthAccepted': 1024
        , 'segmentationSupported': 'segmentedBoth'
        , 'maxSegmentsAccepted': 16
        , 'apduSegmentTimeout': 5000
        , 'apduTimeout': 3000
        , 'numberOfApduRetries': 3
        }

    def __init__(self, **kwargs):
        if _debug: LocalDeviceObject._debug("__init__ %r", kwargs)

        # start with an empty dictionary of device object properties
        init_args = {}
        ini_arg = kwargs.get('ini', None)
        if _debug: LocalDeviceObject._debug("    - ini_arg: %r", dir(ini_arg))

        # check for registration as a keyword parameter or in the INI file
        if self.__class__ not in registered_object_types.values():
            if _debug: LocalDeviceObject._debug("    - unregistered")

            vendor_identifier = kwargs.get('vendorIdentifier', None)
            if _debug: LocalDeviceObject._debug("    - keyword vendor identifier: %r", vendor_identifier)

            if vendor_identifier is None:
                vendor_identifier = getattr(ini_arg, 'vendoridentifier', None)
                if _debug: LocalDeviceObject._debug("    - INI vendor identifier: %r", vendor_identifier)

            if vendor_identifier is None:
                raise RuntimeError("vendorIdentifier required to auto-register the LocalDeviceObject class")

            register_object_type(self.__class__, vendor_id=vendor_identifier)

        # look for properties, fill in values from the keyword arguments or
        # the INI parameter (converted to a proper value) if it was provided
        for propid, prop in self._properties.items():
            # special processing for object identifier
            if propid == 'objectIdentifier':
                continue

            # use keyword argument if it was provided
            if propid in kwargs:
                prop_value = kwargs[propid]
            else:
                prop_value = getattr(ini_arg, propid.lower(), None)
                if prop_value is None:
                    continue

                prop_datatype = prop.datatype

                if issubclass(prop_datatype, Null):
                    if prop_value != "Null":
                        raise ValueError("invalid null property value: %r" % (propid,))
                    prop_value = None

                elif issubclass(prop_datatype, Boolean):
                    prop_value = prop_value.lower()
                    if prop_value not in ('true', 'false', 'set', 'reset'):
                        raise ValueError("invalid boolean property value: %r" % (propid,))
                    prop_value = prop_value in ('true', 'set')

                elif issubclass(prop_datatype, (Unsigned, Integer)):
                    try:
                        prop_value = int(prop_value)
                    except ValueError:
                        raise ValueError("invalid unsigned or integer property value: %r" % (propid,))

                elif issubclass(prop_datatype, (Real, Double)):
                    try:
                        prop_value = float(prop_value)
                    except ValueError:
                        raise ValueError("invalid real or double property value: %r" % (propid,))

                elif issubclass(prop_datatype, OctetString):
                    try:
                        prop_value = xtob(prop_value)
                    except:
                        raise ValueError("invalid octet string property value: %r" % (propid,))

                elif issubclass(prop_datatype, CharacterString):
                    pass

                elif issubclass(prop_datatype, BitString):
                    try:
                        bstr, prop_value = prop_value, []
                        for b in bstr:
                            if b not in ('0', '1'):
                                raise ValueError
                            prop_value.append(int(b))
                    except:
                        raise ValueError("invalid bit string property value: %r" % (propid,))

                elif issubclass(prop_datatype, Enumerated):
                    pass

                else:
                    raise ValueError("cannot interpret %r INI paramter" % (propid,))
            if _debug: LocalDeviceObject._debug("    - property %r: %r", propid, prop_value)

            # at long last
            init_args[propid] = prop_value

        # check for object identifier as a keyword parameter or in the INI file,
        # and it might be just an int, so make it a tuple if necessary
        if 'objectIdentifier' in kwargs:
            object_identifier = kwargs['objectIdentifier']
            if isinstance(object_identifier, int):
                object_identifier = ('device', object_identifier)
        elif hasattr(ini_arg, 'objectidentifier'):
            object_identifier = ('device', int(getattr(ini_arg, 'objectidentifier')))
        else:
            raise RuntimeError("objectIdentifier is required")
        init_args['objectIdentifier'] = object_identifier
        if _debug: LocalDeviceObject._debug("    - object identifier: %r", object_identifier)

        # fill in default property values not in init_args
        for attr, value in LocalDeviceObject.defaultProperties.items():
            if attr not in init_args:
                init_args[attr] = value

        # check for properties this class implements
        if 'localDate' in kwargs:
            raise RuntimeError("localDate is provided by LocalDeviceObject and cannot be overridden")
        if 'localTime' in kwargs:
            raise RuntimeError("localTime is provided by LocalDeviceObject and cannot be overridden")
        if 'protocolServicesSupported' in kwargs:
            raise RuntimeError("protocolServicesSupported is provided by LocalDeviceObject and cannot be overridden")

        # the object list is provided
        if 'objectList' in kwargs:
            raise RuntimeError("objectList is provided by LocalDeviceObject and cannot be overridden")
        init_args['objectList'] = ArrayOf(ObjectIdentifier)([object_identifier])

        # check for a minimum value
        if init_args['maxApduLengthAccepted'] < 50:
            raise ValueError("invalid max APDU length accepted")

        # dump the updated attributes
        if _debug: LocalDeviceObject._debug("    - init_args: %r", init_args)

        # proceed as usual
        super(LocalDeviceObject, self).__init__(**init_args)

        # pass along special property values that are not BACnet properties
        for key, value in kwargs.items():
            if key.startswith("_"):
                setattr(self, key, value)

