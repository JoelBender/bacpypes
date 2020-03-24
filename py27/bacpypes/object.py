#!/usr/bin/python

"""
Object
"""

import sys
from copy import copy as _copy
from collections import defaultdict

from .errors import ConfigurationError, ExecutionError, \
    InvalidParameterDatatype
from .debugging import bacpypes_debugging, ModuleLogger

from .primitivedata import Atomic, BitString, Boolean, CharacterString, Date, \
    Double, Integer, ObjectIdentifier, ObjectType, OctetString, Real, Time, \
    Unsigned, Unsigned8, Unsigned16
from .constructeddata import AnyAtomic, Array, ArrayOf, List, ListOf, \
    Choice, Element, Sequence
from .basetypes import AccessCredentialDisable, AccessCredentialDisableReason, \
    AccessEvent, AccessPassbackMode, AccessRule, AccessThreatLevel, \
    AccessUserType, AccessZoneOccupancyState, AccumulatorRecord, Action, \
    ActionList, AddressBinding, AssignedAccessRights, AuthenticationFactor, \
    AuthenticationFactorFormat, AuthenticationPolicy, AuthenticationStatus, \
    AuthorizationException, AuthorizationMode, BackupState, BDTEntry, BinaryPV, \
    COVSubscription, CalendarEntry, ChannelValue, ClientCOV, \
    CredentialAuthenticationFactor, DailySchedule, DateRange, DateTime, \
    Destination, DeviceObjectPropertyReference, DeviceObjectReference, \
    DeviceStatus, DoorAlarmState, DoorSecuredStatus, DoorStatus, DoorValue, \
    EngineeringUnits, EventNotificationSubscription, EventParameter, \
    EventState, EventTransitionBits, EventType, FaultParameter, FaultType, \
    FileAccessMethod, FDTEntry, IPMode, HostNPort, LifeSafetyMode, LifeSafetyOperation, LifeSafetyState, \
    LightingCommand, LightingInProgress, LightingTransition, LimitEnable, \
    LockStatus, LogMultipleRecord, LogRecord, LogStatus, LoggingType, \
    Maintenance, NameValue, NetworkNumberQuality, NetworkPortCommand, \
    NetworkSecurityPolicy, NetworkType, NodeType, NotifyType, \
    ObjectPropertyReference, ObjectTypesSupported, OptionalCharacterString, \
    Polarity, PortPermission, Prescale, PriorityArray, ProcessIdSelection, \
    ProgramError, ProgramRequest, ProgramState, PropertyAccessResult, \
    PropertyIdentifier, ProtocolLevel, Recipient, Reliability, RestartReason, \
    RouterEntry, Scale, SecurityKeySet, SecurityLevel, Segmentation, \
    ServicesSupported, SetpointReference, ShedLevel, ShedState, SilencedState, \
    SpecialEvent, StatusFlags, TimeStamp, VTClass, VTSession, VMACEntry, \
    WriteStatus
from .apdu import EventNotificationParameters, ReadAccessSpecification, \
    ReadAccessResult

# some debugging
_debug = 0
_log = ModuleLogger(globals())

#
#   PropertyError
#

class PropertyError(AttributeError):
    pass

# a dictionary of object types and classes
registered_object_types = {}

#
#   register_object_type
#

@bacpypes_debugging
def register_object_type(cls=None, vendor_id=0):
    if _debug: register_object_type._debug("register_object_type %s vendor_id=%s", repr(cls), vendor_id)

    # if cls isn't given, return a decorator
    if not cls:
        def _register(xcls):
            if _debug: register_object_type._debug("_register %s (vendor_id=%s)", repr(cls), vendor_id)
            return register_object_type(xcls, vendor_id)
        if _debug: register_object_type._debug("    - returning decorator")

        return _register

    # make sure it's an Object derived class
    if not issubclass(cls, Object):
        raise RuntimeError("Object derived class required")

    # build a property dictionary by going through the class and all its parents
    _properties = {}
    for c in cls.__mro__:
        if _debug: register_object_type._debug("    - c: %r", c)
        for prop in getattr(c, 'properties', []):
            if prop.identifier not in _properties:
                _properties[prop.identifier] = prop

    # if the object type hasn't been provided, make an immutable one
    if 'objectType' not in _properties:
        _properties['objectType'] = ReadableProperty('objectType', ObjectType, cls.objectType, mutable=False)

    # store this in the class
    cls._properties = _properties

    # now save this in all our types
    registered_object_types[(cls.objectType, vendor_id)] = cls

    # return the class as a decorator
    return cls

#
#   get_object_class
#

@bacpypes_debugging
def get_object_class(object_type, vendor_id=0):
    """Return the class associated with an object type."""
    if _debug: get_object_class._debug("get_object_class %r vendor_id=%r", object_type, vendor_id)

    # find the klass as given
    cls = registered_object_types.get((object_type, vendor_id))
    if _debug: get_object_class._debug("    - direct lookup: %s", repr(cls))

    # if the class isn't found and the vendor id is non-zero, try the standard class for the type
    if (not cls) and vendor_id:
        cls = registered_object_types.get((object_type, 0))
        if _debug: get_object_class._debug("    - default lookup: %s", repr(cls))

    return cls

#
#   get_datatype
#

@bacpypes_debugging
def get_datatype(object_type, propid, vendor_id=0):
    """Return the datatype for the property of an object."""
    if _debug: get_datatype._debug("get_datatype %r %r vendor_id=%r", object_type, propid, vendor_id)

    # get the related class
    cls = get_object_class(object_type, vendor_id)
    if not cls:
        return None

    # get the property
    prop = cls._properties.get(propid)
    if not prop:
        return None

    # return the datatype
    return prop.datatype

#
#   Property
#

@bacpypes_debugging
class Property:

    def __init__(self, identifier, datatype, default=None, optional=True, mutable=True):
        if _debug:
            Property._debug("__init__ %s %s default=%r optional=%r mutable=%r",
                identifier, datatype, default, optional, mutable
                )

        # keep the arguments
        self.identifier = identifier

        # check the datatype
        self.datatype = datatype
        if not issubclass(datatype, (Atomic, Sequence, Choice, Array, List, AnyAtomic)):
            raise TypeError("invalid datatype for property: %s" % (identifier,))

        self.optional = optional
        self.mutable = mutable
        self.default = default

    def ReadProperty(self, obj, arrayIndex=None):
        if _debug:
            Property._debug("ReadProperty(%s) %s arrayIndex=%r",
                self.identifier, obj, arrayIndex
                )

        # get the value
        value = obj._values[self.identifier]
        if _debug: Property._debug("    - value: %r", value)

        # access an array
        if arrayIndex is not None:
            if not issubclass(self.datatype, Array):
                raise ExecutionError(errorClass='property', errorCode='propertyIsNotAnArray')

            if value is not None:
                try:
                    # dive in, the water's fine
                    value = value[arrayIndex]
                except IndexError:
                    raise ExecutionError(errorClass='property', errorCode='invalidArrayIndex')

        # all set
        return value

    def WriteProperty(self, obj, value, arrayIndex=None, priority=None, direct=False):
        if _debug:
            Property._debug("WriteProperty(%s) %s %r arrayIndex=%r priority=%r direct=%r",
                self.identifier, obj, value, arrayIndex, priority, direct
                )

        if direct:
            if _debug: Property._debug("    - direct write")
        else:
            # see if it must be provided
            if not self.optional and value is None:
                raise ValueError("%s value required" % (self.identifier,))

            # see if it can be changed
            if not self.mutable:
                raise ExecutionError(errorClass='property', errorCode='writeAccessDenied')

            # if changing the length of the array, the value is unsigned
            if arrayIndex == 0:
                if not Unsigned.is_valid(value):
                    raise InvalidParameterDatatype("length of %s must be unsigned" % (
                            self.identifier,
                            ))

            # if it's atomic, make sure it's valid
            elif issubclass(self.datatype, AnyAtomic):
                if _debug: Property._debug("    - property is any atomic, checking value")
                if not isinstance(value, Atomic):
                    raise InvalidParameterDatatype("%s must be an atomic instance" % (
                            self.identifier,
                            ))

            elif issubclass(self.datatype, Atomic):
                if _debug: Property._debug("    - property is atomic, checking value")
                if not self.datatype.is_valid(value):
                    raise InvalidParameterDatatype("%s must be of type %s" % (
                            self.identifier, self.datatype.__name__,
                            ))

            # if it's an array, make sure it's valid regarding arrayIndex provided
            elif issubclass(self.datatype, Array):
                if _debug: Property._debug("    - property is array, checking subtype and index")

                # changing a single element
                if arrayIndex is not None:
                    # if it's atomic, make sure it's valid
                    if issubclass(self.datatype.subtype, Atomic):
                        if _debug: Property._debug("    - subtype is atomic, checking value")
                        if not self.datatype.subtype.is_valid(value):
                            raise InvalidParameterDatatype("%s must be of type %s" % (
                                    self.identifier, self.datatype.__name__,
                                    ))
                    # constructed type
                    elif not isinstance(value, self.datatype.subtype):
                        raise InvalidParameterDatatype("%s must be of type %s" % (
                                self.identifier, self.datatype.subtype.__name__
                                ))

                # replacing the array
                elif isinstance(value, list):
                    # check validity regarding subtype
                    for item in value:
                        # if it's atomic, make sure it's valid
                        if issubclass(self.datatype.subtype, Atomic):
                            if _debug: Property._debug("    - subtype is atomic, checking value")
                            if not self.datatype.subtype.is_valid(item):
                                raise InvalidParameterDatatype("elements of %s must be of type %s" % (
                                        self.identifier, self.datatype.subtype.__name__,
                                        ))
                        # constructed type
                        elif not isinstance(item, self.datatype.subtype):
                            raise InvalidParameterDatatype("elements of %s must be of type %s" % (
                                    self.identifier, self.datatype.subtype.__name__
                                    ))

                    # value is mutated into a new array
                    value = self.datatype(value)

            # if it's an array, make sure it's valid regarding arrayIndex provided
            elif issubclass(self.datatype, List):
                if _debug: Property._debug("    - property is list, checking subtype")

                # changing a single element
                if arrayIndex is not None:
                    raise ExecutionError(errorClass='property', errorCode='propertyIsNotAnArray')

                # replacing the array
                if not isinstance(value, list):
                    raise InvalidParameterDatatype("elements of %s must be of type %s" % (
                            self.identifier, self.datatype.subtype.__name__
                            ))

                # check validity regarding subtype
                for item in value:
                    # if it's atomic, make sure it's valid
                    if issubclass(self.datatype.subtype, Atomic):
                        if _debug: Property._debug("    - subtype is atomic, checking value")
                        if not self.datatype.subtype.is_valid(item):
                            raise InvalidParameterDatatype("elements of %s must be of type %s" % (
                                    self.identifier, self.datatype.subtype.__name__,
                                    ))
                    # constructed type
                    elif not isinstance(item, self.datatype.subtype):
                        raise InvalidParameterDatatype("elements of %s must be of type %s" % (
                                self.identifier, self.datatype.subtype.__name__
                                ))

                # value is mutated into a new list
                value = self.datatype(value)

            # some kind of constructed data
            elif not isinstance(value, self.datatype):
                if _debug: Property._debug("    - property is not atomic and wrong type")
                raise InvalidParameterDatatype("%s must be of type %s" % (
                        self.identifier, self.datatype.__name__,
                        ))

        # local check if the property is monitored
        is_monitored = self.identifier in obj._property_monitors

        if arrayIndex is not None:
            if not issubclass(self.datatype, Array):
                raise ExecutionError(errorClass='property', errorCode='propertyIsNotAnArray')

            # check the array
            arry = obj._values[self.identifier]
            if arry is None:
                raise RuntimeError("%s uninitialized array" % (self.identifier,))

            if is_monitored:
                old_value = _copy(arry)

            # seems to be OK, let the array object take over
            if _debug: Property._debug("    - forwarding to array")
            try:
                arry[arrayIndex] = value
            except IndexError:
                raise ExecutionError(errorClass='property', errorCode='invalidArrayIndex')
            except TypeError:
                raise ExecutionError(errorClass='property', errorCode='valueOutOfRange')

            # check for monitors, call each one with the old and new value
            if is_monitored:
                for fn in obj._property_monitors[self.identifier]:
                    if _debug: Property._debug("    - monitor: %r", fn)
                    fn(old_value, arry)

        else:
            if is_monitored:
                old_value = obj._values.get(self.identifier, None)

            # seems to be OK
            obj._values[self.identifier] = value

            # check for monitors, call each one with the old and new value
            if is_monitored:
                for fn in obj._property_monitors[self.identifier]:
                    if _debug: Property._debug("    - monitor: %r", fn)
                    fn(old_value, value)

#
#   StandardProperty
#

@bacpypes_debugging
class StandardProperty(Property):

    def __init__(self, identifier, datatype, default=None, optional=True, mutable=True):
        if _debug:
            StandardProperty._debug("__init__ %s %s default=%r optional=%r mutable=%r",
                identifier, datatype, default, optional, mutable
                )

        # use one of the subclasses
        if not isinstance(self, (OptionalProperty, ReadableProperty, WritableProperty)):
            raise ConfigurationError(self.__class__.__name__ + " must derive from OptionalProperty, ReadableProperty, or WritableProperty")

        # validate the identifier to be one of the standard property enumerations
        if identifier not in PropertyIdentifier.enumerations:
            raise ConfigurationError("unknown standard property identifier: %s" % (identifier,))

        # continue with the initialization
        Property.__init__(self, identifier, datatype, default, optional, mutable)

#
#   OptionalProperty
#

@bacpypes_debugging
class OptionalProperty(StandardProperty):

    """The property is optional and need not be present."""

    def __init__(self, identifier, datatype, default=None, optional=True, mutable=False):
        if _debug:
            OptionalProperty._debug("__init__ %s %s default=%r optional=%r mutable=%r",
                identifier, datatype, default, optional, mutable
                )

        # continue with the initialization
        StandardProperty.__init__(self, identifier, datatype, default, optional, mutable)

#
#   ReadableProperty
#

@bacpypes_debugging
class ReadableProperty(StandardProperty):

    """The property is required to be present and readable using BACnet services."""

    def __init__(self, identifier, datatype, default=None, optional=False, mutable=False):
        if _debug:
            ReadableProperty._debug("__init__ %s %s default=%r optional=%r mutable=%r",
                identifier, datatype, default, optional, mutable
                )

        # continue with the initialization
        StandardProperty.__init__(self, identifier, datatype, default, optional, mutable)

#
#   WritableProperty
#

@bacpypes_debugging
class WritableProperty(StandardProperty):

    """The property is required to be present, readable, and writable using BACnet services."""

    def __init__(self, identifier, datatype, default=None, optional=False, mutable=True):
        if _debug:
            WritableProperty._debug("__init__ %s %s default=%r optional=%r mutable=%r",
                identifier, datatype, default, optional, mutable
                )

        # continue with the initialization
        StandardProperty.__init__(self, identifier, datatype, default, optional, mutable)

#
#   ObjectIdentifierProperty
#

@bacpypes_debugging
class ObjectIdentifierProperty(ReadableProperty):

    def WriteProperty(self, obj, value, arrayIndex=None, priority=None, direct=False):
        if _debug: ObjectIdentifierProperty._debug("WriteProperty %r %r arrayIndex=%r priority=%r", obj, value, arrayIndex, priority)

        # make it easy to default
        if value is None:
            pass
        elif isinstance(value, (int, long)):
            value = (obj.objectType, value)
        elif isinstance(value, tuple) and len(value) == 2:
            if value[0] != obj.objectType:
                raise ValueError("%s required" % (obj.objectType,))
        else:
            raise TypeError("object identifier")

        return Property.WriteProperty( self, obj, value, arrayIndex, priority, direct )

#
#   Object
#

@bacpypes_debugging
class Object(object):

    _debug_contents = ('_app',)
    _object_supports_cov = False

    properties = \
        [ ObjectIdentifierProperty('objectIdentifier', ObjectIdentifier, optional=False)
        , ReadableProperty('objectName', CharacterString, optional=False)
        , OptionalProperty('description', CharacterString)
        , OptionalProperty('profileName', CharacterString)
        , ReadableProperty('propertyList', ArrayOf(PropertyIdentifier))
        , OptionalProperty('tags', ArrayOf(NameValue))
        , OptionalProperty('profileLocation', CharacterString)
        , OptionalProperty('profileName', CharacterString)
        ]
    _properties = {}

    def __init__(self, **kwargs):
        """Create an object, with default property values as needed."""
        if _debug: Object._debug("__init__(%s) %r", self.__class__.__name__, kwargs)

        # map the python names into property names and make sure they
        # are appropriate for this object
        initargs = {}
        for key, value in kwargs.items():
            if key not in self._properties:
                raise PropertyError(key)
            initargs[key] = value

        # object is detached from an application until it is added
        self._app = None

        # start with a clean dict of values
        self._values = {}

        # empty list of property monitors
        self._property_monitors = defaultdict(list)

        # initialize the object
        for propid, prop in self._properties.items():
            if propid in initargs:
                if _debug: Object._debug("    - setting %s from initargs", propid)

                # defer to the property object for error checking
                prop.WriteProperty(self, initargs[propid], direct=True)

            elif prop.default is not None:
                if _debug: Object._debug("    - setting %s from default", propid)

                # default values bypass property interface
                self._values[propid] = prop.default

            else:
                if not prop.optional:
                    if _debug: Object._debug("    - %s value required", propid)

                self._values[propid] = None

        if _debug: Object._debug("    - done __init__")

    def _attr_to_property(self, attr):
        """Common routine to translate a python attribute name to a property name and
        return the appropriate property."""

        # get the property
        prop = self._properties.get(attr)
        if not prop:
            raise PropertyError(attr)

        # found it
        return prop

    def __getattr__(self, attr):
        if _debug: Object._debug("__getattr__ %r", attr)

        # do not redirect private attrs or functions
        if attr.startswith('_') or attr[0].isupper() or (attr == 'debug_contents'):
            return object.__getattribute__(self, attr)

        # defer to the property to get the value
        prop = self._attr_to_property(attr)
        if _debug: Object._debug("    - deferring to %r", prop)

        # defer to the property to get the value
        return prop.ReadProperty(self)

    def __setattr__(self, attr, value):
        if _debug: Object._debug("__setattr__ %r %r", attr, value)

        if attr.startswith('_') or attr[0].isupper() or (attr == 'debug_contents'):
            return object.__setattr__(self, attr, value)

        # defer to the property to normalize the value
        prop = self._attr_to_property(attr)
        if _debug: Object._debug("    - deferring to %r", prop)

        return prop.WriteProperty(self, value, direct=True)

    def add_property(self, prop):
        """Add a property to an object.  The property is an instance of
        a Property or one of its derived classes.  Adding a property
        disconnects it from the collection of properties common to all of the
        objects of its class."""
        if _debug: Object._debug("add_property %r", prop)

        # make a copy of the properties dictionary
        self._properties = _copy(self._properties)

        # save the property reference and default value (usually None)
        self._properties[prop.identifier] = prop
        self._values[prop.identifier] = prop.default

    def delete_property(self, prop):
        """Delete a property from an object.  The property is an instance of
        a Property or one of its derived classes, but only the property
        is relavent.  Deleting a property disconnects it from the collection of
        properties common to all of the objects of its class."""
        if _debug: Object._debug("delete_property %r", prop)

        # make a copy of the properties dictionary
        self._properties = _copy(self._properties)

        # delete the property from the dictionary and values
        del self._properties[prop.identifier]
        if prop.identifier in self._values:
            del self._values[prop.identifier]

    def ReadProperty(self, propid, arrayIndex=None):
        if _debug: Object._debug("ReadProperty %r arrayIndex=%r", propid, arrayIndex)

        # get the property
        prop = self._properties.get(propid)
        if not prop:
            raise PropertyError(propid)

        # defer to the property to get the value
        return prop.ReadProperty(self, arrayIndex)

    def WriteProperty(self, propid, value, arrayIndex=None, priority=None, direct=False):
        if _debug: Object._debug("WriteProperty %r %r arrayIndex=%r priority=%r", propid, value, arrayIndex, priority)

        # get the property
        prop = self._properties.get(propid)
        if not prop:
            raise PropertyError(propid)

        # defer to the property to set the value
        return prop.WriteProperty(self, value, arrayIndex, priority, direct)

    def get_datatype(self, propid):
        """Return the datatype for the property of an object."""
        if _debug: Object._debug("get_datatype %r", propid)

        # get the property
        prop = self._properties.get(propid)
        if not prop:
            raise PropertyError(propid)

        # return the datatype
        return prop.datatype

    def _dict_contents(self, use_dict=None, as_class=dict):
        """Return the contents of an object as a dict."""
        if _debug: Object._debug("dict_contents use_dict=%r as_class=%r", use_dict, as_class)

        # make/extend the dictionary of content
        if use_dict is None:
            use_dict = as_class()

        klasses = list(self.__class__.__mro__)
        klasses.reverse()

        # build a list of property identifiers "bottom up"
        property_names = []
        properties_seen = set()
        for c in klasses:
            for prop in getattr(c, 'properties', []):
                if prop.identifier not in properties_seen:
                    property_names.append(prop.identifier)
                    properties_seen.add(prop.identifier)

        # extract the values
        for property_name in property_names:
            # get the value
            property_value = self._properties.get(property_name).ReadProperty(self)
            if property_value is None:
                continue

            # if the value has a way to convert it to a dict, use it
            if hasattr(property_value, "dict_contents"):
                property_value = property_value.dict_contents(as_class=as_class)

            # save the value
            use_dict.__setitem__(property_name, property_value)

        # return what we built/updated
        return use_dict

    def debug_contents(self, indent=1, file=sys.stdout, _ids=None):
        """Print out interesting things about the object."""
        klasses = list(self.__class__.__mro__)
        klasses.reverse()

        # print special attributes "bottom up"
        previous_attrs = ()
        for c in klasses:
            attrs = getattr(c, '_debug_contents', ())

            # if we have seen this list already, move to the next class
            if attrs is previous_attrs:
                continue

            for attr in attrs:
                file.write("%s%s = %s\n" % ("    " * indent, attr, getattr(self, attr)))
            previous_attrs = attrs

        # build a list of property identifiers "bottom up"
        property_names = []
        properties_seen = set()
        for c in klasses:
            for prop in getattr(c, 'properties', []):
                if prop.identifier not in properties_seen:
                    property_names.append(prop.identifier)
                    properties_seen.add(prop.identifier)

        # print out the values
        for property_name in property_names:
            property_value = self._values.get(property_name, None)

            # printing out property values that are None is tedious
            if property_value is None:
                continue

            if hasattr(property_value, "debug_contents"):
                file.write("%s%s\n" % ("    " * indent, property_name))
                property_value.debug_contents(indent+1, file, _ids)
            else:
                file.write("%s%s = %r\n" % ("    " * indent, property_name, property_value))

#
#   Standard Object Types
#

@register_object_type
class AccessCredentialObject(Object):
    objectType = 'accessCredential'
    properties = \
        [ WritableProperty('globalIdentifier', Unsigned)
        , ReadableProperty('statusFlags', StatusFlags)
        , ReadableProperty('reliability', Reliability)
        , ReadableProperty('credentialStatus', BinaryPV)
        , ReadableProperty('reasonForDisable', ListOf(AccessCredentialDisableReason))
        , ReadableProperty('authenticationFactors', ArrayOf(CredentialAuthenticationFactor))
        , ReadableProperty('activationTime', DateTime)
        , ReadableProperty('expiryTime', DateTime)
        , ReadableProperty('credentialDisable', AccessCredentialDisable)
        , OptionalProperty('daysRemaining', Integer)
        , OptionalProperty('usesRemaining', Integer)
        , OptionalProperty('absenteeLimit', Unsigned)
        , OptionalProperty('belongsTo', DeviceObjectReference)
        , ReadableProperty('assignedAccessRights', ArrayOf(AssignedAccessRights))
        , OptionalProperty('lastAccessPoint', DeviceObjectReference)
        , OptionalProperty('lastAccessEvent', AccessEvent)
        , OptionalProperty('lastUseTime', DateTime)
        , OptionalProperty('traceFlag', Boolean)
        , OptionalProperty('threatAuthority', AccessThreatLevel)
        , OptionalProperty('extendedTimeEnable', Boolean)
        , OptionalProperty('authorizationExemptions', ListOf(AuthorizationException))
        , OptionalProperty('reliabilityEvaluationInhibit', Boolean)
#       , OptionalProperty('masterExemption', Boolean)
#       , OptionalProperty('passbackExemption', Boolean)
#       , OptionalProperty('occupancyExemption', Boolean)
        ]

@register_object_type
class AccessDoorObject(Object):
    objectType = 'accessDoor'
    _object_supports_cov = True

    properties = \
        [ WritableProperty('presentValue', DoorValue)
        , ReadableProperty('statusFlags', StatusFlags)
        , ReadableProperty('eventState', EventState)
        , ReadableProperty('reliability', Reliability)
        , ReadableProperty('outOfService', Boolean)
        , ReadableProperty('priorityArray', PriorityArray)
        , ReadableProperty('relinquishDefault', DoorValue)
        , OptionalProperty('doorStatus', DoorStatus)
        , OptionalProperty('lockStatus', LockStatus)
        , OptionalProperty('securedStatus', DoorSecuredStatus)
        , OptionalProperty('doorMembers', ArrayOf(DeviceObjectReference))
        , ReadableProperty('doorPulseTime', Unsigned)
        , ReadableProperty('doorExtendedPulseTime', Unsigned)
        , OptionalProperty('doorUnlockDelayTime', Unsigned)
        , ReadableProperty('doorOpenTooLongTime', Unsigned)
        , OptionalProperty('doorAlarmState', DoorAlarmState)
        , OptionalProperty('maskedAlarmValues', ListOf(DoorAlarmState))
        , OptionalProperty('maintenanceRequired', Maintenance)
        , OptionalProperty('timeDelay', Unsigned)
        , OptionalProperty('notificationClass', Unsigned)
        , OptionalProperty('alarmValues', ListOf(DoorAlarmState))
        , OptionalProperty('faultValues', ListOf(DoorAlarmState))
        , OptionalProperty('eventEnable', EventTransitionBits)
        , OptionalProperty('ackedTransitions', EventTransitionBits)
        , OptionalProperty('notifyType', NotifyType)
        , OptionalProperty('eventTimeStamps', ArrayOf(TimeStamp))
        , OptionalProperty('eventMessageTexts', ArrayOf(CharacterString))
        , OptionalProperty('eventMessageTextsConfig', ArrayOf(CharacterString))
        , OptionalProperty('eventDetectionEnable', Boolean)
        , OptionalProperty('eventAlgorithmInhibitRef', ObjectPropertyReference)
        , OptionalProperty('eventAlgorithmInhibit', Boolean)
        ]

@register_object_type
class AccessPointObject(Object):
    objectType = 'accessPoint'
    _object_supports_cov = True

    properties = \
        [ ReadableProperty('statusFlags', StatusFlags)
        , ReadableProperty('eventState', EventState)
        , ReadableProperty('reliability', Reliability)
        , ReadableProperty('outOfService', Boolean)
        , ReadableProperty('authenticationStatus', AuthenticationStatus)
        , ReadableProperty('activeAuthenticationPolicy', Unsigned)
        , ReadableProperty('numberOfAuthenticationPolicies', Unsigned)
        , OptionalProperty('authenticationPolicyList', ArrayOf(AuthenticationPolicy))
        , OptionalProperty('authenticationPolicyNames', ArrayOf(CharacterString))
        , ReadableProperty('authorizationMode', AuthorizationMode)
        , OptionalProperty('verificationTime', Unsigned)
        , OptionalProperty('lockout', Boolean)
        , OptionalProperty('lockoutRelinquishTime', Unsigned)
        , OptionalProperty('failedAttempts', Unsigned)
        , OptionalProperty('failedAttemptEvents', ListOf(AccessEvent))
        , OptionalProperty('maxFailedAttempts', Unsigned)
        , OptionalProperty('failedAttemptsTime', Unsigned)
        , OptionalProperty('threatLevel', AccessThreatLevel)
        , OptionalProperty('occupancyUpperLimitEnforced', Boolean)
        , OptionalProperty('occupancyLowerLimitEnforced', Boolean)
        , OptionalProperty('occupancyCountAdjust', Boolean)
        , OptionalProperty('accompanimentTime', Unsigned)
        , ReadableProperty('accessEvent', AccessEvent)
        , ReadableProperty('accessEventTag', Unsigned)
        , ReadableProperty('accessEventTime', TimeStamp)
        , ReadableProperty('accessEventCredential', DeviceObjectReference)
        , OptionalProperty('accessEventAuthenticationFactor', AuthenticationFactor)
        , ReadableProperty('accessDoors', ArrayOf(DeviceObjectReference))
        , ReadableProperty('priorityForWriting', Unsigned)
        , OptionalProperty('musterPoint', Boolean)
        , OptionalProperty('zoneTo', DeviceObjectReference)
        , OptionalProperty('zoneFrom', DeviceObjectReference)
        , OptionalProperty('notificationClass', Unsigned)
        , OptionalProperty('transactionNotificationClass', Unsigned)
        , OptionalProperty('accessAlarmEvents', ListOf(AccessEvent))
        , OptionalProperty('accessTransactionEvents', ListOf(AccessEvent))
        , OptionalProperty('eventEnable', EventTransitionBits)
        , OptionalProperty('ackedTransitions', EventTransitionBits)
        , OptionalProperty('notifyType', NotifyType)
        , OptionalProperty('eventTimeStamps', ArrayOf(TimeStamp))
        , OptionalProperty('eventMessageTexts', ArrayOf(CharacterString))
        , OptionalProperty('eventMessageTextsConfig', ArrayOf(CharacterString))
        , OptionalProperty('eventDetectionEnable', Boolean)
        , OptionalProperty('eventAlgorithmInhibitRef', ObjectPropertyReference)
        , OptionalProperty('eventAlgorithmInhibit', Boolean)
        , OptionalProperty('reliabilityEvaluationInhibit', Boolean)
        ]

@register_object_type
class AccessRightsObject(Object):
    objectType = 'accessRights'
    properties = \
        [ WritableProperty('globalIdentifier', Unsigned)
        , ReadableProperty('statusFlags', StatusFlags)
        , ReadableProperty('reliability', Reliability)
        , ReadableProperty('enable', Boolean)
        , ReadableProperty('negativeAccessRules', ArrayOf(AccessRule))
        , ReadableProperty('positiveAccessRules', ArrayOf(AccessRule))
        , OptionalProperty('accompaniment', DeviceObjectReference)
        , OptionalProperty('reliabilityEvaluationInhibit', Boolean)
        ]

@register_object_type
class AccessUserObject(Object):
    objectType = 'accessUser'
    properties = \
        [ WritableProperty('globalIdentifier', Unsigned)
        , ReadableProperty('statusFlags', StatusFlags)
        , ReadableProperty('reliability', Reliability)
        , ReadableProperty('userType', AccessUserType)
        , OptionalProperty('userName', CharacterString)
        , OptionalProperty('userExternalIdentifier', CharacterString)
        , OptionalProperty('userInformationReference', CharacterString)
        , OptionalProperty('members', ListOf(DeviceObjectReference))
        , OptionalProperty('memberOf', ListOf(DeviceObjectReference))
        , ReadableProperty('credentials', ListOf(DeviceObjectReference))
       ]

@register_object_type
class AccessZoneObject(Object):
    objectType = 'accessZone'
    properties = \
        [ WritableProperty('globalIdentifier', Unsigned)
        , ReadableProperty('occupancyState', AccessZoneOccupancyState)
        , ReadableProperty('statusFlags', StatusFlags)
        , ReadableProperty('eventState', EventState)
        , ReadableProperty('reliability', Reliability)
        , ReadableProperty('outOfService', Boolean)
        , OptionalProperty('occupancyCount', Unsigned)
        , OptionalProperty('occupancyCountEnable', Boolean)
        , OptionalProperty('adjustValue', Integer)
        , OptionalProperty('occupancyUpperLimit', Unsigned)
        , OptionalProperty('occupancyLowerLimit', Unsigned)
        , OptionalProperty('credentialsInZone', ListOf(DeviceObjectReference) )
        , OptionalProperty('lastCredentialAdded', DeviceObjectReference)
        , OptionalProperty('lastCredentialAddedTime', DateTime)
        , OptionalProperty('lastCredentialRemoved', DeviceObjectReference)
        , OptionalProperty('lastCredentialRemovedTime', DateTime)
        , OptionalProperty('passbackMode', AccessPassbackMode)
        , OptionalProperty('passbackTimeout', Unsigned)
        , ReadableProperty('entryPoints', ListOf(DeviceObjectReference))
        , ReadableProperty('exitPoints', ListOf(DeviceObjectReference))
        , OptionalProperty('timeDelay', Unsigned)
        , OptionalProperty('notificationClass', Unsigned)
        , OptionalProperty('alarmValues', ListOf(AccessZoneOccupancyState))
        , OptionalProperty('eventEnable', EventTransitionBits)
        , OptionalProperty('ackedTransitions', EventTransitionBits)
        , OptionalProperty('notifyType', NotifyType)
        , OptionalProperty('eventTimeStamps', ArrayOf(TimeStamp))
        , OptionalProperty('eventMessageTexts', ArrayOf(CharacterString))
        , OptionalProperty('eventMessageTextsConfig', ArrayOf(CharacterString))
        , OptionalProperty('eventDetectionEnable', Boolean)
        , OptionalProperty('eventAlgorithmInhibitRef', ObjectPropertyReference)
        , OptionalProperty('eventAlgorithmInhibit', Boolean)
        , OptionalProperty('timeDelayNormal', Unsigned)
        , OptionalProperty('reliabilityEvaluationInhibit', Boolean)
        ]

@register_object_type
class AccumulatorObject(Object):
    objectType = 'accumulator'
    properties = \
        [ ReadableProperty('presentValue', Unsigned)
        , OptionalProperty('deviceType', CharacterString)
        , ReadableProperty('statusFlags', StatusFlags)
        , ReadableProperty('eventState', EventState)
        , OptionalProperty('reliability', Reliability)
        , ReadableProperty('outOfService', Boolean)
        , ReadableProperty('scale', Scale)
        , ReadableProperty('units', EngineeringUnits)
        , OptionalProperty('prescale', Prescale)
        , ReadableProperty('maxPresValue', Unsigned)
        , OptionalProperty('valueChangeTime', DateTime)
        , OptionalProperty('valueBeforeChange', Unsigned)
        , OptionalProperty('valueSet', Unsigned)
        , OptionalProperty('loggingRecord', AccumulatorRecord)
        , OptionalProperty('loggingObject', ObjectIdentifier)
        , OptionalProperty('pulseRate', Unsigned)
        , OptionalProperty('highLimit', Unsigned)
        , OptionalProperty('lowLimit', Unsigned)
        , OptionalProperty('limitMonitoringInterval', Unsigned)
        , OptionalProperty('notificationClass', Unsigned)
        , OptionalProperty('timeDelay', Unsigned)
        , OptionalProperty('limitEnable', LimitEnable)
        , OptionalProperty('eventEnable', EventTransitionBits)
        , OptionalProperty('ackedTransitions', EventTransitionBits)
        , OptionalProperty('notifyType', NotifyType)
        , OptionalProperty('eventTimeStamps', ArrayOf(TimeStamp))
        , OptionalProperty('eventMessageTexts', ArrayOf(CharacterString))
        , OptionalProperty('eventMessageTextsConfig', ArrayOf(CharacterString))
        , OptionalProperty('eventDetectionEnable', Boolean)
        , OptionalProperty('eventAlgorithmInhibitRef', ObjectPropertyReference)
        , OptionalProperty('eventAlgorithmInhibit', Boolean)
        , OptionalProperty('timeDelayNormal', Unsigned)
        , OptionalProperty('reliabilityEvaluationInhibit', Boolean)
        ]

@register_object_type
class AlertEnrollmentObject(Object):
    objectType = 'alertEnrollment'
    properties = \
        [ ReadableProperty('presentValue', ObjectIdentifier)
        , ReadableProperty('eventState', EventState)
        , ReadableProperty('eventDetectionEnable', Boolean)
        , ReadableProperty('notificationClass', Unsigned)
        , OptionalProperty('eventEnable', EventTransitionBits)
        , OptionalProperty('ackedTransitions', EventTransitionBits)
        , OptionalProperty('notifyType', NotifyType)
        , OptionalProperty('eventTimeStamps', ArrayOf(TimeStamp))
        , OptionalProperty('eventMessageTexts', ArrayOf(CharacterString))
        , OptionalProperty('eventMessageTextsConfig', ArrayOf(CharacterString))
        , OptionalProperty('eventAlgorithmInhibitRef', ObjectPropertyReference)
        , OptionalProperty('eventAlgorithmInhibit', Boolean)
        ]

@register_object_type
class AnalogInputObject(Object):
    objectType = 'analogInput'
    _object_supports_cov = True

    properties = \
        [ ReadableProperty('presentValue', Real)
        , OptionalProperty('deviceType', CharacterString)
        , ReadableProperty('statusFlags', StatusFlags)
        , ReadableProperty('eventState', EventState)
        , OptionalProperty('reliability', Reliability)
        , ReadableProperty('outOfService', Boolean)
        , OptionalProperty('updateInterval', Unsigned)
        , ReadableProperty('units', EngineeringUnits)
        , OptionalProperty('minPresValue', Real)
        , OptionalProperty('maxPresValue', Real)
        , OptionalProperty('resolution', Real)
        , OptionalProperty('covIncrement', Real)
        , OptionalProperty('timeDelay', Unsigned)
        , OptionalProperty('notificationClass', Unsigned)
        , OptionalProperty('highLimit', Real)
        , OptionalProperty('lowLimit', Real)
        , OptionalProperty('deadband', Real)
        , OptionalProperty('limitEnable', LimitEnable)
        , OptionalProperty('eventEnable', EventTransitionBits)
        , OptionalProperty('ackedTransitions', EventTransitionBits)
        , OptionalProperty('notifyType', NotifyType)
        , OptionalProperty('eventTimeStamps', ArrayOf(TimeStamp))
        , OptionalProperty('eventMessageTexts', ArrayOf(CharacterString))
        , OptionalProperty('eventMessageTextsConfig', ArrayOf(CharacterString))
        , OptionalProperty('eventDetectionEnable', Boolean)
        , OptionalProperty('eventAlgorithmInhibitRef', ObjectPropertyReference)
        , OptionalProperty('eventAlgorithmInhibit', Boolean)
        , OptionalProperty('timeDelayNormal', Unsigned)
        , OptionalProperty('reliabilityEvaluationInhibit', Boolean)
        ]

@register_object_type
class AnalogOutputObject(Object):
    objectType = 'analogOutput'
    _object_supports_cov = True

    properties = \
        [ WritableProperty('presentValue', Real)
        , OptionalProperty('deviceType', CharacterString)
        , ReadableProperty('statusFlags', StatusFlags)
        , ReadableProperty('eventState', EventState)
        , OptionalProperty('reliability', Reliability)
        , ReadableProperty('outOfService', Boolean)
        , ReadableProperty('units',  EngineeringUnits)
        , OptionalProperty('minPresValue', Real)
        , OptionalProperty('maxPresValue', Real)
        , OptionalProperty('resolution', Real)
        , ReadableProperty('priorityArray', PriorityArray)
        , ReadableProperty('relinquishDefault', Real)
        , OptionalProperty('covIncrement', Real)
        , OptionalProperty('timeDelay', Unsigned)
        , OptionalProperty('notificationClass', Unsigned)
        , OptionalProperty('highLimit', Real)
        , OptionalProperty('lowLimit', Real)
        , OptionalProperty('deadband', Real)
        , OptionalProperty('limitEnable', LimitEnable)
        , OptionalProperty('eventEnable', EventTransitionBits)
        , OptionalProperty('ackedTransitions',  EventTransitionBits)
        , OptionalProperty('notifyType', NotifyType)
        , OptionalProperty('eventTimeStamps', ArrayOf(TimeStamp))
        , OptionalProperty('eventMessageTexts', ArrayOf(CharacterString))
        , OptionalProperty('eventMessageTextsConfig', ArrayOf(CharacterString))
        , OptionalProperty('eventDetectionEnable', Boolean)
        , OptionalProperty('eventAlgorithmInhibitRef', ObjectPropertyReference)
        , OptionalProperty('eventAlgorithmInhibit', Boolean)
        , OptionalProperty('timeDelayNormal', Unsigned)
        , OptionalProperty('reliabilityEvaluationInhibit', Boolean)
        ]

@register_object_type
class AnalogValueObject(Object):
    objectType = 'analogValue'
    _object_supports_cov = True

    properties = \
        [ ReadableProperty('presentValue', Real)
        , ReadableProperty('statusFlags', StatusFlags)
        , ReadableProperty('eventState', EventState)
        , OptionalProperty('reliability', Reliability)
        , ReadableProperty('outOfService', Boolean)
        , ReadableProperty('units', EngineeringUnits)
        , OptionalProperty('minPresValue', Real)
        , OptionalProperty('maxPresValue', Real)
        , OptionalProperty('resolution', Real)
        , OptionalProperty('priorityArray', PriorityArray)
        , OptionalProperty('relinquishDefault', Real)
        , OptionalProperty('covIncrement', Real)
        , OptionalProperty('timeDelay', Unsigned)
        , OptionalProperty('notificationClass',  Unsigned)
        , OptionalProperty('highLimit', Real)
        , OptionalProperty('lowLimit', Real)
        , OptionalProperty('deadband', Real)
        , OptionalProperty('limitEnable', LimitEnable)
        , OptionalProperty('eventEnable', EventTransitionBits)
        , OptionalProperty('ackedTransitions', EventTransitionBits)
        , OptionalProperty('notifyType', NotifyType)
        , OptionalProperty('eventTimeStamps', ArrayOf(TimeStamp))
        , OptionalProperty('eventMessageTexts', ArrayOf(CharacterString))
        , OptionalProperty('eventMessageTextsConfig', ArrayOf(CharacterString))
        , OptionalProperty('eventDetectionEnable', Boolean)
        , OptionalProperty('eventAlgorithmInhibitRef', ObjectPropertyReference)
        , OptionalProperty('eventAlgorithmInhibit', Boolean)
        , OptionalProperty('timeDelayNormal', Unsigned)
        , OptionalProperty('reliabilityEvaluationInhibit', Boolean)
        ]

@register_object_type
class AveragingObject(Object):
    objectType = 'averaging'
    properties = \
        [ ReadableProperty('minimumValue', Real)
        , OptionalProperty('minimumValueTimestamp', DateTime)
        , ReadableProperty('averageValue', Real)
        , OptionalProperty('varianceValue', Real)
        , ReadableProperty('maximumValue', Real)
        , OptionalProperty('maximumValueTimestamp', DateTime)
        , WritableProperty('attemptedSamples', Unsigned)
        , ReadableProperty('validSamples', Unsigned)
        , ReadableProperty('objectPropertyReference', DeviceObjectPropertyReference)
        , WritableProperty('windowInterval', Unsigned)
        , WritableProperty('windowSamples', Unsigned)
        ]

@register_object_type
class BinaryInputObject(Object):
    objectType = 'binaryInput'
    _object_supports_cov = True

    properties = \
        [ ReadableProperty('presentValue', BinaryPV)
        , OptionalProperty('deviceType', CharacterString)
        , ReadableProperty('statusFlags', StatusFlags)
        , ReadableProperty('eventState', EventState)
        , OptionalProperty('reliability', Reliability)
        , ReadableProperty('outOfService', Boolean)
        , ReadableProperty('polarity', Polarity)
        , OptionalProperty('inactiveText', CharacterString)
        , OptionalProperty('activeText', CharacterString)
        , OptionalProperty('changeOfStateTime', DateTime)
        , OptionalProperty('changeOfStateCount', Unsigned)
        , OptionalProperty('timeOfStateCountReset', DateTime)
        , OptionalProperty('elapsedActiveTime', Unsigned)
        , OptionalProperty('timeOfActiveTimeReset', DateTime)
        , OptionalProperty('timeDelay', Unsigned)
        , OptionalProperty('notificationClass', Unsigned)
        , OptionalProperty('alarmValue', BinaryPV)
        , OptionalProperty('eventEnable', EventTransitionBits)
        , OptionalProperty('ackedTransitions', EventTransitionBits)
        , OptionalProperty('notifyType', NotifyType)
        , OptionalProperty('eventTimeStamps', ArrayOf(TimeStamp))
        , OptionalProperty('eventMessageTexts', ArrayOf(CharacterString))
        , OptionalProperty('eventMessageTextsConfig', ArrayOf(CharacterString))
        , OptionalProperty('eventDetectionEnable', Boolean)
        , OptionalProperty('eventAlgorithmInhibitRef', ObjectPropertyReference)
        , OptionalProperty('eventAlgorithmInhibit', Boolean)
        , OptionalProperty('timeDelayNormal', Unsigned)
        , OptionalProperty('reliabilityEvaluationInhibit', Boolean)
        ]

@register_object_type
class BinaryOutputObject(Object):
    objectType = 'binaryOutput'
    _object_supports_cov = True

    properties = \
        [ WritableProperty('presentValue', BinaryPV)
        , OptionalProperty('deviceType', CharacterString)
        , ReadableProperty('statusFlags', StatusFlags)
        , ReadableProperty('eventState', EventState)
        , OptionalProperty('reliability', Reliability)
        , ReadableProperty('outOfService', Boolean)
        , ReadableProperty('polarity', Polarity)
        , OptionalProperty('inactiveText', CharacterString)
        , OptionalProperty('activeText', CharacterString)
        , OptionalProperty('changeOfStateTime', DateTime)
        , OptionalProperty('changeOfStateCount', Unsigned)
        , OptionalProperty('timeOfStateCountReset', DateTime)
        , OptionalProperty('elapsedActiveTime', Unsigned)
        , OptionalProperty('timeOfActiveTimeReset', DateTime)
        , OptionalProperty('minimumOffTime', Unsigned)
        , OptionalProperty('minimumOnTime', Unsigned)
        , ReadableProperty('priorityArray', PriorityArray)
        , ReadableProperty('relinquishDefault', BinaryPV)
        , OptionalProperty('timeDelay', Unsigned)
        , OptionalProperty('notificationClass', Unsigned)
        , OptionalProperty('feedbackValue', BinaryPV)
        , OptionalProperty('eventEnable', EventTransitionBits)
        , OptionalProperty('ackedTransitions', EventTransitionBits)
        , OptionalProperty('notifyType', NotifyType)
        , OptionalProperty('eventTimeStamps', ArrayOf(TimeStamp))
        , OptionalProperty('eventMessageTexts', ArrayOf(CharacterString))
        , OptionalProperty('eventMessageTextsConfig', ArrayOf(CharacterString))
        , OptionalProperty('eventDetectionEnable', Boolean)
        , OptionalProperty('eventAlgorithmInhibitRef', ObjectPropertyReference)
        , OptionalProperty('eventAlgorithmInhibit', Boolean)
        , OptionalProperty('timeDelayNormal', Unsigned)
        , OptionalProperty('reliabilityEvaluationInhibit', Boolean)
        ]

@register_object_type
class BinaryValueObject(Object):
    objectType = 'binaryValue'
    _object_supports_cov = True

    properties = \
        [ WritableProperty('presentValue', BinaryPV)
        , ReadableProperty('statusFlags',StatusFlags)
        , ReadableProperty('eventState',EventState)
        , OptionalProperty('reliability',Reliability)
        , ReadableProperty('outOfService',Boolean)
        , OptionalProperty('inactiveText',CharacterString)
        , OptionalProperty('activeText',CharacterString)
        , OptionalProperty('changeOfStateTime',DateTime)
        , OptionalProperty('changeOfStateCount',Unsigned)
        , OptionalProperty('timeOfStateCountReset',DateTime)
        , OptionalProperty('elapsedActiveTime',Unsigned)
        , OptionalProperty('timeOfActiveTimeReset',DateTime)
        , OptionalProperty('minimumOffTime',Unsigned)
        , OptionalProperty('minimumOnTime',Unsigned)
        , OptionalProperty('priorityArray',PriorityArray)
        , OptionalProperty('relinquishDefault',BinaryPV)
        , OptionalProperty('timeDelay',Unsigned)
        , OptionalProperty('notificationClass',Unsigned)
        , OptionalProperty('alarmValue',BinaryPV)
        , OptionalProperty('eventEnable',EventTransitionBits)
        , OptionalProperty('ackedTransitions',EventTransitionBits)
        , OptionalProperty('notifyType',NotifyType)
        , OptionalProperty('eventTimeStamps', ArrayOf(TimeStamp))
        , OptionalProperty('eventMessageTexts', ArrayOf(CharacterString))
        , OptionalProperty('eventMessageTextsConfig', ArrayOf(CharacterString))
        , OptionalProperty('eventDetectionEnable', Boolean)
        , OptionalProperty('eventAlgorithmInhibitRef', ObjectPropertyReference)
        , OptionalProperty('eventAlgorithmInhibit', Boolean)
        , OptionalProperty('timeDelayNormal', Unsigned)
        , OptionalProperty('reliabilityEvaluationInhibit', Boolean)
        ]

@register_object_type
class BitStringValueObject(Object):
    objectType = 'bitstringValue'
    properties = \
        [ ReadableProperty('presentValue', BitString)
        , OptionalProperty('bitText', ArrayOf(CharacterString))
        , ReadableProperty('statusFlags', StatusFlags)
        , OptionalProperty('eventState', EventState)
        , OptionalProperty('reliability', Reliability)
        , OptionalProperty('outOfService', Boolean)
        , OptionalProperty('priorityArray', PriorityArray)
        , OptionalProperty('relinquishDefault', BitString)
        , OptionalProperty('timeDelay', Unsigned)
        , OptionalProperty('notificationClass', Unsigned)
        , OptionalProperty('alarmValues', ArrayOf(BitString))
        , OptionalProperty('bitMask', BitString)
        , OptionalProperty('eventEnable', EventTransitionBits)
        , OptionalProperty('ackedTransitions', EventTransitionBits)
        , OptionalProperty('notifyType', NotifyType)
        , OptionalProperty('eventTimeStamps', ArrayOf(TimeStamp))
        , OptionalProperty('eventMessageTexts', ArrayOf(CharacterString))
        , OptionalProperty('eventMessageTextsConfig', ArrayOf(CharacterString))
        , OptionalProperty('eventDetectionEnable', Boolean)
        , OptionalProperty('eventAlgorithmInhibitRef', ObjectPropertyReference)
        , OptionalProperty('eventAlgorithmInhibit', Boolean)
        , OptionalProperty('timeDelayNormal', Unsigned)
        , OptionalProperty('reliabilityEvaluationInhibit', Boolean)
        ]

@register_object_type
class CalendarObject(Object):
    objectType = 'calendar'
    properties = \
        [ ReadableProperty('presentValue', Boolean)
        , ReadableProperty('dateList', ListOf(CalendarEntry))
        ]

@register_object_type
class ChannelObject(Object):
    objectType = 'channel'
    properties = \
        [ WritableProperty('presentValue', ChannelValue)
        , ReadableProperty('lastPriority', Unsigned)
        , ReadableProperty('writeStatus', WriteStatus)
        , ReadableProperty('statusFlags', StatusFlags)
        , OptionalProperty('reliability', Reliability)
        , ReadableProperty('outOfService', Boolean)
        , WritableProperty('listOfObjectPropertyReferences', ArrayOf(DeviceObjectPropertyReference))
        , OptionalProperty('executionDelay', ArrayOf(Unsigned))
        , OptionalProperty('allowGroupDelayInhibit', Boolean)
        , WritableProperty('channelNumber', Unsigned)
        , WritableProperty('controlGroups', ArrayOf(Unsigned))
        , OptionalProperty('eventDetectionEnable', Boolean)
        , OptionalProperty('notificationClass', Unsigned)
        , OptionalProperty('eventEnable', EventTransitionBits)
        , OptionalProperty('eventState', EventState)
        , OptionalProperty('ackedTransitions', EventTransitionBits)
        , OptionalProperty('notifyType', NotifyType)
        , OptionalProperty('eventTimeStamps', ArrayOf(TimeStamp))
        , OptionalProperty('eventMessageTexts', ArrayOf(CharacterString))
        , OptionalProperty('eventMessageTextsConfig', ArrayOf(CharacterString))
        , OptionalProperty('reliabilityEvaluationInhibit', Boolean)
        ]

@register_object_type
class CharacterStringValueObject(Object):
    objectType = 'characterstringValue'
    _object_supports_cov = True

    properties = \
        [ ReadableProperty('presentValue', CharacterString)
        , ReadableProperty('statusFlags', StatusFlags)
        , OptionalProperty('eventState', EventState)
        , OptionalProperty('reliability', Reliability)
        , OptionalProperty('outOfService', Boolean)
        , OptionalProperty('priorityArray', PriorityArray)
        , OptionalProperty('relinquishDefault', CharacterString)
        , OptionalProperty('timeDelay', Unsigned)
        , OptionalProperty('notificationClass', Unsigned)
        , OptionalProperty('alarmValues', ArrayOf(OptionalCharacterString))
        , OptionalProperty('faultValues', ArrayOf(OptionalCharacterString))
        , OptionalProperty('eventEnable', EventTransitionBits)
        , OptionalProperty('ackedTransitions', EventTransitionBits)
        , OptionalProperty('notifyType', NotifyType)
        , OptionalProperty('eventTimeStamps', ArrayOf(TimeStamp))
        , OptionalProperty('eventMessageTexts', ArrayOf(CharacterString))
        , OptionalProperty('eventMessageTextsConfig', ArrayOf(CharacterString))
        , OptionalProperty('eventDetectionEnable', Boolean)
        , OptionalProperty('eventAlgorithmInhibitRef', ObjectPropertyReference)
        , OptionalProperty('eventAlgorithmInhibit', Boolean)
        , OptionalProperty('timeDelayNormal', Unsigned)
        , OptionalProperty('reliabilityEvaluationInhibit', Boolean)
        ]

@register_object_type
class CommandObject(Object):
    objectType = 'command'
    properties = \
        [ WritableProperty('presentValue', Unsigned)
        , ReadableProperty('inProcess', Boolean)
        , ReadableProperty('allWritesSuccessful', Boolean)
        , ReadableProperty('action', ArrayOf(ActionList))
        , OptionalProperty('actionText', ArrayOf(CharacterString))
        ]

@register_object_type
class CredentialDataInputObject(Object):
    objectType = 'credentialDataInput'
    _object_supports_cov = True

    properties = \
        [ ReadableProperty('presentValue', AuthenticationFactor)
        , ReadableProperty('statusFlags', StatusFlags)
        , OptionalProperty('reliability', Reliability)
        , ReadableProperty('outOfService', Boolean)
        , ReadableProperty('supportedFormats', ArrayOf(AuthenticationFactorFormat))
        , OptionalProperty('supportedFormatClasses', ArrayOf(Unsigned))
        , ReadableProperty('updateTime', TimeStamp)
        , OptionalProperty('eventDetectionEnable', Boolean)
        , OptionalProperty('notificationClass', Unsigned)
        , OptionalProperty('eventEnable', EventTransitionBits)
        , OptionalProperty('ackedTransitions', EventTransitionBits)
        , OptionalProperty('notifyType', NotifyType)
        , OptionalProperty('eventTimeStamps', ArrayOf(TimeStamp))
        , OptionalProperty('eventMessageTexts', ArrayOf(CharacterString))
        , OptionalProperty('eventMessageTextsConfig', ArrayOf(CharacterString))
        , OptionalProperty('reliabilityEvaluationInhibit', Boolean)
        ]

@register_object_type
class DatePatternValueObject(Object):
    objectType = 'datePatternValue'
    _object_supports_cov = True

    properties = \
        [ ReadableProperty('presentValue', Date)
        , ReadableProperty('statusFlags', StatusFlags)
        , OptionalProperty('eventState', EventState)
        , OptionalProperty('reliability', Reliability)
        , OptionalProperty('outOfService', Boolean)
        , OptionalProperty('priorityArray', PriorityArray)
        , OptionalProperty('relinquishDefault', Date)
        ]

@register_object_type
class DateValueObject(Object):
    objectType = 'dateValue'
    _object_supports_cov = True

    properties = \
        [ ReadableProperty('presentValue', Date)
        , ReadableProperty('statusFlags', StatusFlags)
        , OptionalProperty('eventState', EventState)
        , OptionalProperty('reliability', Reliability)
        , OptionalProperty('outOfService', Boolean)
        , OptionalProperty('priorityArray', PriorityArray)
        , OptionalProperty('relinquishDefault', Date)
        ]

@register_object_type
class DateTimePatternValueObject(Object):
    objectType = 'datetimePatternValue'
    _object_supports_cov = True

    properties = \
        [ ReadableProperty('presentValue', DateTime)
        , ReadableProperty('statusFlags', StatusFlags)
        , OptionalProperty('eventState', EventState)
        , OptionalProperty('reliability', Reliability)
        , OptionalProperty('outOfService', Boolean)
        , OptionalProperty('priorityArray', PriorityArray)
        , OptionalProperty('relinquishDefault', DateTime)
        , OptionalProperty('isUtc', Boolean)
        ]

@register_object_type
class DateTimeValueObject(Object):
    objectType = 'datetimeValue'
    _object_supports_cov = True

    properties = \
        [ ReadableProperty('presentValue', DateTime)
        , ReadableProperty('statusFlags', StatusFlags)
        , OptionalProperty('eventState', EventState)
        , OptionalProperty('reliability', Reliability)
        , OptionalProperty('outOfService', Boolean)
        , OptionalProperty('priorityArray', PriorityArray)
        , OptionalProperty('relinquishDefault', DateTime)
        , OptionalProperty('isUtc', Boolean)
        ]

@register_object_type
class DeviceObject(Object):
    objectType = 'device'
    properties = \
        [ ReadableProperty('systemStatus', DeviceStatus)
        , ReadableProperty('vendorName', CharacterString)
        , ReadableProperty('vendorIdentifier', Unsigned)
        , ReadableProperty('modelName', CharacterString)
        , ReadableProperty('firmwareRevision', CharacterString)
        , ReadableProperty('applicationSoftwareVersion', CharacterString)
        , OptionalProperty('location', CharacterString)
        , ReadableProperty('protocolVersion', Unsigned)
        , ReadableProperty('protocolRevision', Unsigned)
        , ReadableProperty('protocolServicesSupported', ServicesSupported)
        , ReadableProperty('protocolObjectTypesSupported', ObjectTypesSupported)
        , ReadableProperty('objectList', ArrayOf(ObjectIdentifier))
        , OptionalProperty('structuredObjectList', ArrayOf(ObjectIdentifier))
        , ReadableProperty('maxApduLengthAccepted', Unsigned)
        , ReadableProperty('segmentationSupported', Segmentation)
        , OptionalProperty('vtClassesSupported', ListOf(VTClass))
        , OptionalProperty('activeVtSessions', ListOf(VTSession))
        , OptionalProperty('localTime', Time)
        , OptionalProperty('localDate', Date)
        , OptionalProperty('utcOffset', Integer)
        , OptionalProperty('daylightSavingsStatus', Boolean)
        , OptionalProperty('apduSegmentTimeout', Unsigned)
        , ReadableProperty('apduTimeout', Unsigned)
        , ReadableProperty('numberOfApduRetries', Unsigned)
        , OptionalProperty('timeSynchronizationRecipients', ListOf(Recipient))
        , OptionalProperty('maxMaster', Unsigned)
        , OptionalProperty('maxInfoFrames', Unsigned)
        , ReadableProperty('deviceAddressBinding', ListOf(AddressBinding))
        , ReadableProperty('databaseRevision', Unsigned)
        , OptionalProperty('configurationFiles', ArrayOf(ObjectIdentifier))
        , OptionalProperty('lastRestoreTime', TimeStamp)
        , OptionalProperty('backupFailureTimeout', Unsigned)
        , OptionalProperty('backupPreparationTime', Unsigned)
        , OptionalProperty('restorePreparationTime', Unsigned)
        , OptionalProperty('restoreCompletionTime', Unsigned)
        , OptionalProperty('backupAndRestoreState', BackupState)
        , OptionalProperty('activeCovSubscriptions', ListOf(COVSubscription))
        , OptionalProperty('maxSegmentsAccepted', Unsigned)
        , OptionalProperty('slaveProxyEnable', ArrayOf(Boolean))
        , OptionalProperty('autoSlaveDiscovery', ArrayOf(Boolean))
        , OptionalProperty('slaveAddressBinding', ListOf(AddressBinding))
        , OptionalProperty('manualSlaveAddressBinding', ListOf(AddressBinding))
        , OptionalProperty('lastRestartReason', RestartReason)
        , OptionalProperty('timeOfDeviceRestart', TimeStamp)
        , OptionalProperty('restartNotificationRecipients', ListOf(Recipient))
        , OptionalProperty('utcTimeSynchronizationRecipients', ListOf(Recipient))
        , OptionalProperty('timeSynchronizationInterval', Unsigned)
        , OptionalProperty('alignIntervals', Boolean)
        , OptionalProperty('intervalOffset', Unsigned)
        , OptionalProperty('serialNumber', CharacterString)
        ]

@register_object_type
class EventEnrollmentObject(Object):
    objectType = 'eventEnrollment'
    properties = \
        [ ReadableProperty('eventType', EventType)
        , ReadableProperty('notifyType', NotifyType)
        , ReadableProperty('eventParameters', EventParameter)
        , ReadableProperty('objectPropertyReference', DeviceObjectPropertyReference)
        , ReadableProperty('eventState', EventState)
        , ReadableProperty('eventEnable', EventTransitionBits)
        , ReadableProperty('ackedTransitions', EventTransitionBits)
        , ReadableProperty('notificationClass', Unsigned)
        , ReadableProperty('eventTimeStamps', ArrayOf(TimeStamp))
        , OptionalProperty('eventMessageTexts', ArrayOf(CharacterString))
        , OptionalProperty('eventMessageTextsConfig', ArrayOf(CharacterString))
        , ReadableProperty('eventDetectionEnable', Boolean)
        , OptionalProperty('eventAlgorithmInhibitRef', ObjectPropertyReference)
        , OptionalProperty('eventAlgorithmInhibit', Boolean)
        , OptionalProperty('timeDelayNormal', Unsigned)
        , ReadableProperty('statusFlags', StatusFlags)
        , ReadableProperty('reliability', Reliability)
        , OptionalProperty('faultType', FaultType)
        , OptionalProperty('faultParameters', FaultParameter)
        , OptionalProperty('reliabilityEvaluationInhibit', Boolean)
        ]

#-----

class EventLogRecordLogDatum(Choice):
    choiceElements = \
        [ Element('logStatus', LogStatus, 0)
        , Element('notification', EventNotificationParameters, 1)
        , Element('timeChange', Real, 2)
        ]

class EventLogRecord(Sequence):
    sequenceElements = \
        [ Element('timestamp', DateTime, 0)
        , Element('logDatum', EventLogRecordLogDatum, 1)
        ]

@register_object_type
class EventLogObject(Object):
    objectType = 'eventLog'
    properties = \
        [ ReadableProperty('statusFlags', StatusFlags)
        , ReadableProperty('eventState', EventState)
        , OptionalProperty('reliability', Reliability)
        , WritableProperty('enable', Boolean)
        , OptionalProperty('startTime', DateTime)
        , OptionalProperty('stopTime', DateTime)
        , ReadableProperty('stopWhenFull', Boolean)
        , ReadableProperty('bufferSize', Unsigned)
        , ReadableProperty('logBuffer', ListOf(EventLogRecord))
        , WritableProperty('recordCount', Unsigned)
        , ReadableProperty('totalRecordCount', Unsigned)
        , OptionalProperty('notificationThreshold', Unsigned)
        , OptionalProperty('recordsSinceNotification', Unsigned)
        , OptionalProperty('lastNotifyRecord', Unsigned)
        , OptionalProperty('notificationClass', Unsigned)
        , OptionalProperty('eventEnable', EventTransitionBits)
        , OptionalProperty('ackedTransitions', EventTransitionBits)
        , OptionalProperty('notifyType', NotifyType)
        , OptionalProperty('eventTimeStamps', ArrayOf(TimeStamp))
        , OptionalProperty('eventMessageTexts', ArrayOf(CharacterString))
        , OptionalProperty('eventMessageTextsConfig', ArrayOf(CharacterString))
        , OptionalProperty('eventDetectionEnable', Boolean)
        , OptionalProperty('eventAlgorithmInhibitRef', ObjectPropertyReference)
        , OptionalProperty('eventAlgorithmInhibit', Boolean)
        ]

#-----

@register_object_type
class FileObject(Object):
    objectType = 'file'
    properties = \
        [ ReadableProperty('fileType', CharacterString)
        , ReadableProperty('fileSize', Unsigned)
        , ReadableProperty('modificationDate', DateTime)
        , WritableProperty('archive', Boolean)
        , ReadableProperty('readOnly', Boolean)
        , ReadableProperty('fileAccessMethod', FileAccessMethod)
        , OptionalProperty('recordCount', Unsigned)
        ]

#-----

@register_object_type
class GlobalGroupObject(Object):
    objectType = 'globalGroup'
    properties = \
        [ ReadableProperty('groupMembers', ArrayOf(DeviceObjectPropertyReference))
        , OptionalProperty('groupMemberNames', ArrayOf(CharacterString))
        , ReadableProperty('presentValue', ArrayOf(PropertyAccessResult))
        , ReadableProperty('statusFlags', StatusFlags)
        , ReadableProperty('eventState', EventState)
        , ReadableProperty('memberStatusFlags', StatusFlags)
        , OptionalProperty('reliability', Reliability)
        , ReadableProperty('outOfService', Boolean)
        , OptionalProperty('updateInterval', Unsigned)
        , OptionalProperty('requestedUpdateInterval', Unsigned)
        , OptionalProperty('covResubscriptionInterval', Unsigned)
        , OptionalProperty('clientCovIncrement', ClientCOV)
        , OptionalProperty('timeDelay', Unsigned)
        , OptionalProperty('notificationClass', Unsigned)
        , OptionalProperty('eventEnable', EventTransitionBits)
        , OptionalProperty('ackedTransitions', EventTransitionBits)
        , OptionalProperty('notifyType', NotifyType)
        , OptionalProperty('eventTimeStamps', ArrayOf(TimeStamp))
        , OptionalProperty('eventMessageTexts', ArrayOf(CharacterString))
        , OptionalProperty('eventMessageTextsConfig', ArrayOf(CharacterString))
        , OptionalProperty('eventDetectionEnable', Boolean)
        , OptionalProperty('eventAlgorithmInhibitRef', ObjectPropertyReference)
        , OptionalProperty('eventAlgorithmInhibit', Boolean)
        , OptionalProperty('timeDelayNormal', Unsigned)
        , OptionalProperty('covuPeriod', Unsigned)
        , OptionalProperty('covuRecipients', ListOf(Recipient))
        , OptionalProperty('reliabilityEvaluationInhibit', Boolean)
        ]

@register_object_type
class GroupObject(Object):
    objectType = 'group'
    properties = \
        [ ReadableProperty('listOfGroupMembers', ListOf(ReadAccessSpecification))
        , ReadableProperty('presentValue', ListOf(ReadAccessResult))
        ]

@register_object_type
class IntegerValueObject(Object):
    objectType = 'integerValue'
    _object_supports_cov = True

    properties = \
        [ ReadableProperty('presentValue', Integer)
        , ReadableProperty('statusFlags', StatusFlags)
        , OptionalProperty('eventState', EventState)
        , OptionalProperty('reliability', Reliability)
        , OptionalProperty('outOfService', Boolean)
        , ReadableProperty('units', EngineeringUnits)
        , OptionalProperty('priorityArray', PriorityArray)
        , OptionalProperty('relinquishDefault', Integer)
        , OptionalProperty('covIncrement', Unsigned)
        , OptionalProperty('timeDelay', Unsigned)
        , OptionalProperty('notificationClass', Unsigned)
        , OptionalProperty('highLimit', Integer)
        , OptionalProperty('lowLimit', Integer)
        , OptionalProperty('deadband', Unsigned)
        , OptionalProperty('limitEnable', LimitEnable)
        , OptionalProperty('eventEnable', EventTransitionBits)
        , OptionalProperty('ackedTransitions', EventTransitionBits)
        , OptionalProperty('notifyType', NotifyType)
        , OptionalProperty('eventTimeStamps', ArrayOf(TimeStamp))
        , OptionalProperty('eventMessageTexts', ArrayOf(CharacterString))
        , OptionalProperty('eventMessageTextsConfig', ArrayOf(CharacterString))
        , OptionalProperty('eventDetectionEnable', Boolean)
        , OptionalProperty('eventAlgorithmInhibitRef', ObjectPropertyReference)
        , OptionalProperty('eventAlgorithmInhibit', Boolean)
        , OptionalProperty('timeDelayNormal', Unsigned)
        , OptionalProperty('reliabilityEvaluationInhibit', Boolean)
        , OptionalProperty('minPresValue', Integer)
        , OptionalProperty('maxPresValue', Integer)
        , OptionalProperty('resolution', Integer)
        ]

@register_object_type
class LargeAnalogValueObject(Object):
    objectType = 'largeAnalogValue'
    _object_supports_cov = True

    properties = \
        [ ReadableProperty('presentValue', Double)
        , ReadableProperty('statusFlags', StatusFlags)
        , OptionalProperty('eventState', EventState)
        , OptionalProperty('reliability', Reliability)
        , OptionalProperty('outOfService', Boolean)
        , ReadableProperty('units', EngineeringUnits)
        , OptionalProperty('priorityArray', PriorityArray)
        , OptionalProperty('relinquishDefault', Integer)
        , OptionalProperty('covIncrement', Unsigned)
        , OptionalProperty('timeDelay', Unsigned)
        , OptionalProperty('notificationClass', Unsigned)
        , OptionalProperty('highLimit', Double)
        , OptionalProperty('lowLimit', Double)
        , OptionalProperty('deadband', Double)
        , OptionalProperty('limitEnable', LimitEnable)
        , OptionalProperty('eventEnable', EventTransitionBits)
        , OptionalProperty('ackedTransitions', EventTransitionBits)
        , OptionalProperty('notifyType', NotifyType)
        , OptionalProperty('eventTimeStamps', ArrayOf(TimeStamp))
        , OptionalProperty('eventMessageTexts', ArrayOf(CharacterString))
        , OptionalProperty('eventMessageTextsConfig', ArrayOf(CharacterString))
        , OptionalProperty('eventDetectionEnable', Boolean)
        , OptionalProperty('eventAlgorithmInhibitRef', ObjectPropertyReference)
        , OptionalProperty('eventAlgorithmInhibit', Boolean)
        , OptionalProperty('timeDelayNormal', Unsigned)
        , OptionalProperty('reliabilityEvaluationInhibit', Boolean)
        , OptionalProperty('minPresValue', Double)
        , OptionalProperty('maxPresValue', Double)
        , OptionalProperty('resolution', Double)
        ]

@register_object_type
class LifeSafetyPointObject(Object):
    objectType = 'lifeSafetyPoint'
    _object_supports_cov = True

    properties = \
        [ ReadableProperty('presentValue', LifeSafetyState)
        , ReadableProperty('trackingValue', LifeSafetyState)
        , OptionalProperty('deviceType', CharacterString)
        , ReadableProperty('statusFlags', StatusFlags)
        , ReadableProperty('eventState', EventState)
        , ReadableProperty('reliability', Reliability)
        , ReadableProperty('outOfService', Boolean)
        , WritableProperty('mode', LifeSafetyMode)
        , ReadableProperty('acceptedModes', ListOf(LifeSafetyMode))
        , OptionalProperty('timeDelay', Unsigned)
        , OptionalProperty('notificationClass', Unsigned)
        , OptionalProperty('lifeSafetyAlarmValues', ListOf(LifeSafetyState))
        , OptionalProperty('alarmValues', ListOf(LifeSafetyState))
        , OptionalProperty('faultValues', ListOf(LifeSafetyState))
        , OptionalProperty('eventEnable', EventTransitionBits)
        , OptionalProperty('ackedTransitions', EventTransitionBits)
        , OptionalProperty('notifyType', NotifyType)
        , OptionalProperty('eventTimeStamps', ArrayOf(TimeStamp))
        , OptionalProperty('eventMessageTexts', ArrayOf(CharacterString))
        , OptionalProperty('eventMessageTextsConfig', ArrayOf(CharacterString))
        , OptionalProperty('eventDetectionEnable', Boolean)
        , OptionalProperty('eventAlgorithmInhibitRef', ObjectPropertyReference)
        , OptionalProperty('eventAlgorithmInhibit', Boolean)
        , OptionalProperty('timeDelayNormal', Unsigned)
        , OptionalProperty('reliabilityEvaluationInhibit', Boolean)
        , ReadableProperty('silenced', SilencedState)
        , ReadableProperty('operationExpected', LifeSafetyOperation)
        , OptionalProperty('maintenanceRequired', Maintenance)
        , OptionalProperty('setting', Unsigned)
        , OptionalProperty('directReading', Real)
        , OptionalProperty('units', EngineeringUnits)
        , OptionalProperty('memberOf', ListOf(DeviceObjectReference))
        ]

@register_object_type
class LifeSafetyZoneObject(Object):
    objectType = 'lifeSafetyZone'
    _object_supports_cov = True

    properties = \
        [ ReadableProperty('presentValue', LifeSafetyState)
        , ReadableProperty('trackingValue', LifeSafetyState)
        , OptionalProperty('deviceType', CharacterString)
        , ReadableProperty('statusFlags', StatusFlags)
        , ReadableProperty('eventState', EventState)
        , ReadableProperty('reliability', Reliability)
        , ReadableProperty('outOfService', Boolean)
        , WritableProperty('mode', LifeSafetyMode)
        , ReadableProperty('acceptedModes', ListOf(LifeSafetyMode))
        , OptionalProperty('timeDelay', Unsigned)
        , OptionalProperty('notificationClass', Unsigned)
        , OptionalProperty('lifeSafetyAlarmValues', ListOf(LifeSafetyState))
        , OptionalProperty('alarmValues', ListOf(LifeSafetyState))
        , OptionalProperty('faultValues', ListOf(LifeSafetyState))
        , OptionalProperty('eventEnable', EventTransitionBits)
        , OptionalProperty('ackedTransitions', EventTransitionBits)
        , OptionalProperty('notifyType', NotifyType)
        , OptionalProperty('eventTimeStamps', ArrayOf(TimeStamp))
        , OptionalProperty('eventMessageTexts', ArrayOf(CharacterString))
        , OptionalProperty('eventMessageTextsConfig', ArrayOf(CharacterString))
        , OptionalProperty('eventDetectionEnable', Boolean)
        , OptionalProperty('eventAlgorithmInhibitRef', ObjectPropertyReference)
        , OptionalProperty('eventAlgorithmInhibit', Boolean)
        , OptionalProperty('timeDelayNormal', Unsigned)
        , OptionalProperty('reliabilityEvaluationInhibit', Boolean)
        , ReadableProperty('silenced', SilencedState)
        , ReadableProperty('operationExpected', LifeSafetyOperation)
        , OptionalProperty('maintenanceRequired', Boolean)
        , ReadableProperty('zoneMembers', ListOf(DeviceObjectReference))
        , OptionalProperty('memberOf', ListOf(DeviceObjectReference))
        ]

@register_object_type
class LightingOutputObject(Object):
    objectType = 'lightingOutput'
    _object_supports_cov = True

    properties = \
        [ WritableProperty('presentValue', Real)
        , ReadableProperty('trackingValue', Real)
        , WritableProperty('lightingCommand', LightingCommand)
        , ReadableProperty('inProgress', LightingInProgress)
        , ReadableProperty('statusFlags', StatusFlags)
        , OptionalProperty('reliability', Reliability)
        , ReadableProperty('outOfService', Boolean)
        , ReadableProperty('blinkWarnEnable', Boolean)
        , ReadableProperty('egressTime', Unsigned)
        , ReadableProperty('egressActive', Boolean)
        , ReadableProperty('defaultFadeTime', Unsigned)
        , ReadableProperty('defaultRampRate', Real)
        , ReadableProperty('defaultStepIncrement', Real)
        , OptionalProperty('transition', LightingTransition)
        , OptionalProperty('feedbackValue', Real)
        , ReadableProperty('priorityArray', PriorityArray)
        , ReadableProperty('relinquishDefault', Real)
        , OptionalProperty('power', Real)
        , OptionalProperty('instantaneousPower', Real)
        , OptionalProperty('minActualValue', Real)
        , OptionalProperty('maxActualValue', Real)
        , ReadableProperty('lightingCommandDefaultPriority', Unsigned)
        , OptionalProperty('covIncrement', Real)
        , OptionalProperty('reliabilityEvaluationInhibit', Boolean)
        ]

@register_object_type
class LoadControlObject(Object):
    objectType = 'loadControl'
    _object_supports_cov = True

    properties = \
        [ ReadableProperty('presentValue', ShedState)
        , OptionalProperty('stateDescription', CharacterString)
        , ReadableProperty('statusFlags', StatusFlags)
        , ReadableProperty('eventState', EventState)
        , OptionalProperty('reliability', Reliability)
        , WritableProperty('requestedShedLevel', ShedLevel)
        , WritableProperty('startTime', DateTime)
        , WritableProperty('shedDuration', Unsigned)
        , WritableProperty('dutyWindow', Unsigned)
        , WritableProperty('enable', Boolean)
        , OptionalProperty('fullDutyBaseline', Real)
        , ReadableProperty('expectedShedLevel', ShedLevel)
        , ReadableProperty('actualShedLevel', ShedLevel)
        , WritableProperty('shedLevels', ArrayOf(Unsigned))
        , ReadableProperty('shedLevelDescriptions', ArrayOf(CharacterString))
        , OptionalProperty('notificationClass', Unsigned)
        , OptionalProperty('timeDelay', Unsigned)
        , OptionalProperty('eventEnable', EventTransitionBits)
        , OptionalProperty('ackedTransitions', EventTransitionBits)
        , OptionalProperty('notifyType', NotifyType)
        , OptionalProperty('eventTimeStamps', ArrayOf(TimeStamp))
        , OptionalProperty('eventMessageTexts', ArrayOf(CharacterString))
        , OptionalProperty('eventMessageTextsConfig', ArrayOf(CharacterString))
        , OptionalProperty('eventDetectionEnable', Boolean)
        , OptionalProperty('eventAlgorithmInhibitRef', ObjectPropertyReference)
        , OptionalProperty('eventAlgorithmInhibit', Boolean)
        , OptionalProperty('timeDelayNormal', Unsigned)
        , OptionalProperty('reliabilityEvaluationInhibit', Boolean)
        ]

@register_object_type
class LoopObject(Object):
    objectType = 'loop'
    _object_supports_cov = True

    properties = \
        [ ReadableProperty('presentValue', Real)
        , ReadableProperty('statusFlags', StatusFlags)
        , ReadableProperty('eventState', EventState)
        , OptionalProperty('reliability', Reliability)
        , ReadableProperty('outOfService', Boolean)
        , ReadableProperty('updateInterval', Unsigned)
        , ReadableProperty('outputUnits', EngineeringUnits)
        , ReadableProperty('manipulatedVariableReference', ObjectPropertyReference)
        , ReadableProperty('controlledVariableReference', ObjectPropertyReference)
        , ReadableProperty('controlledVariableValue', Real)
        , ReadableProperty('controlledVariableUnits', EngineeringUnits)
        , ReadableProperty('setpointReference', SetpointReference)
        , ReadableProperty('setpoint', Real)
        , ReadableProperty('action', Action)
        , OptionalProperty('proportionalConstant', Real)
        , OptionalProperty('proportionalConstantUnits', EngineeringUnits)
        , OptionalProperty('integralConstant', Real)
        , OptionalProperty('integralConstantUnits', EngineeringUnits)
        , OptionalProperty('derivativeConstant', Real)
        , OptionalProperty('derivativeConstantUnits', EngineeringUnits)
        , OptionalProperty('bias', Real)
        , OptionalProperty('maximumOutput', Real)
        , OptionalProperty('minimumOutput', Real)
        , ReadableProperty('priorityForWriting', Unsigned)
        , OptionalProperty('covIncrement', Real)
        , OptionalProperty('timeDelay', Unsigned)
        , OptionalProperty('notificationClass', Unsigned)
        , OptionalProperty('errorLimit', Real)
        , OptionalProperty('deadband', Real)
        , OptionalProperty('eventEnable', EventTransitionBits)
        , OptionalProperty('ackedTransitions', EventTransitionBits)
        , OptionalProperty('notifyType', NotifyType)
        , OptionalProperty('eventTimeStamps', ArrayOf(TimeStamp))
        , OptionalProperty('eventMessageTexts', ArrayOf(CharacterString))
        , OptionalProperty('eventMessageTextsConfig', ArrayOf(CharacterString))
        , OptionalProperty('eventDetectionEnable', Boolean)
        , OptionalProperty('eventAlgorithmInhibitRef', ObjectPropertyReference)
        , OptionalProperty('eventAlgorithmInhibit', Boolean)
        , OptionalProperty('timeDelayNormal', Unsigned)
        , OptionalProperty('reliabilityEvaluationInhibit', Boolean)
        ]

@register_object_type
class MultiStateInputObject(Object):
    objectType = 'multiStateInput'
    _object_supports_cov = True

    properties = \
        [ ReadableProperty('presentValue', Unsigned)
        , OptionalProperty('deviceType', CharacterString)
        , ReadableProperty('statusFlags', StatusFlags)
        , ReadableProperty('eventState', EventState)
        , OptionalProperty('reliability', Reliability)
        , ReadableProperty('outOfService', Boolean)
        , ReadableProperty('numberOfStates', Unsigned)
        , OptionalProperty('stateText', ArrayOf(CharacterString))
        , OptionalProperty('timeDelay', Unsigned)
        , OptionalProperty('notificationClass', Unsigned)
        , OptionalProperty('alarmValues', ListOf(Unsigned))
        , OptionalProperty('faultValues', ListOf(Unsigned))
        , OptionalProperty('eventEnable', EventTransitionBits)
        , OptionalProperty('ackedTransitions', EventTransitionBits)
        , OptionalProperty('notifyType', NotifyType)
        , OptionalProperty('eventTimeStamps', ArrayOf(TimeStamp))
        , OptionalProperty('eventMessageTexts', ArrayOf(CharacterString))
        , OptionalProperty('eventMessageTextsConfig', ArrayOf(CharacterString))
        , OptionalProperty('eventDetectionEnable', Boolean)
        , OptionalProperty('eventAlgorithmInhibitRef', ObjectPropertyReference)
        , OptionalProperty('eventAlgorithmInhibit', Boolean)
        , OptionalProperty('timeDelayNormal', Unsigned)
        , OptionalProperty('reliabilityEvaluationInhibit', Boolean)
        ]

@register_object_type
class MultiStateOutputObject(Object):
    objectType = 'multiStateOutput'
    _object_supports_cov = True

    properties = \
        [ WritableProperty('presentValue', Unsigned)
        , OptionalProperty('deviceType', CharacterString)
        , ReadableProperty('statusFlags', StatusFlags)
        , ReadableProperty('eventState', EventState)
        , OptionalProperty('reliability', Reliability)
        , ReadableProperty('outOfService', Boolean)
        , ReadableProperty('numberOfStates', Unsigned)
        , OptionalProperty('stateText', ArrayOf(CharacterString))
        , ReadableProperty('priorityArray', PriorityArray)
        , OptionalProperty('relinquishDefault', Unsigned)
        , OptionalProperty('timeDelay', Unsigned)
        , OptionalProperty('notificationClass', Unsigned)
        , OptionalProperty('feedbackValue', Unsigned)
        , OptionalProperty('eventEnable', EventTransitionBits)
        , OptionalProperty('ackedTransitions', EventTransitionBits)
        , OptionalProperty('notifyType', NotifyType)
        , OptionalProperty('eventTimeStamps', ArrayOf(TimeStamp))
        , OptionalProperty('eventMessageTexts', ArrayOf(CharacterString))
        , OptionalProperty('eventMessageTextsConfig', ArrayOf(CharacterString))
        , OptionalProperty('eventDetectionEnable', Boolean)
        , OptionalProperty('eventAlgorithmInhibitRef', ObjectPropertyReference)
        , OptionalProperty('eventAlgorithmInhibit', Boolean)
        , OptionalProperty('timeDelayNormal', Unsigned)
        , OptionalProperty('reliabilityEvaluationInhibit', Boolean)
        ]

@register_object_type
class MultiStateValueObject(Object):
    objectType = 'multiStateValue'
    _object_supports_cov = True

    properties = \
        [ ReadableProperty('presentValue', Unsigned)
        , ReadableProperty('statusFlags', StatusFlags)
        , ReadableProperty('eventState', EventState)
        , OptionalProperty('reliability', Reliability)
        , ReadableProperty('outOfService', Boolean)
        , ReadableProperty('numberOfStates', Unsigned)
        , OptionalProperty('stateText', ArrayOf(CharacterString))
        , OptionalProperty('priorityArray', PriorityArray)
        , OptionalProperty('relinquishDefault', Unsigned)
        , OptionalProperty('timeDelay', Unsigned)
        , OptionalProperty('notificationClass', Unsigned)
        , OptionalProperty('alarmValues', ListOf(Unsigned))
        , OptionalProperty('faultValues', ListOf(Unsigned))
        , OptionalProperty('eventEnable', EventTransitionBits)
        , OptionalProperty('ackedTransitions', EventTransitionBits)
        , OptionalProperty('notifyType', NotifyType)
        , OptionalProperty('eventTimeStamps', ArrayOf(TimeStamp))
        , OptionalProperty('eventMessageTexts', ArrayOf(CharacterString))
        , OptionalProperty('eventMessageTextsConfig', ArrayOf(CharacterString))
        , OptionalProperty('eventDetectionEnable', Boolean)
        , OptionalProperty('eventAlgorithmInhibitRef', ObjectPropertyReference)
        , OptionalProperty('eventAlgorithmInhibit', Boolean)
        , OptionalProperty('timeDelayNormal', Unsigned)
        , OptionalProperty('reliabilityEvaluationInhibit', Boolean)
        ]

@register_object_type
class NetworkPortObject(Object):
    objectType = 'networkPort'  #56
    properties = \
        [ ReadableProperty('statusFlags', StatusFlags)  #111
        , ReadableProperty('reliability', Reliability)  #103
        , ReadableProperty('outOfService', Boolean)  #81
        , ReadableProperty('networkType', NetworkType)  #427
        , ReadableProperty('protocolLevel', ProtocolLevel)  #482
        , OptionalProperty('referencePort', Unsigned)  #483
        , ReadableProperty('networkNumber', Unsigned16)  #425
        , ReadableProperty('networkNumberQuality', NetworkNumberQuality)  #427
        , ReadableProperty('changesPending', Boolean)  #416
        , OptionalProperty('command', NetworkPortCommand)   #417
        , OptionalProperty('macAddress', OctetString)   #423
        , ReadableProperty('apduLength', Unsigned)  #388
        , ReadableProperty('linkSpeed', Real)  #420
        , OptionalProperty('linkSpeeds', ArrayOf(Real))  #421
        , OptionalProperty('eventTimeStamps', ArrayOf(TimeStamp))  #130
        , OptionalProperty('linkSpeedAutonegotiate', Boolean)  #422
        , OptionalProperty('networkInterfaceName', CharacterString)  #424
        , OptionalProperty('bacnetIPMode', IPMode)  #408
        , OptionalProperty('ipAddress', OctetString)  #400
        , OptionalProperty('bacnetIPUDPPort', Unsigned16)  #412
        , OptionalProperty('ipSubnetMask', OctetString)  #411
        , OptionalProperty('ipDefaultGateway', OctetString)  #401
        , OptionalProperty('bacnetIPMulticastAddress', OctetString)  #409
        , OptionalProperty('ipDNSServer', ArrayOf(OctetString))  #406
        , OptionalProperty('ipDHCPEnable', Boolean)  #402
        , OptionalProperty('ipDHCPLeaseTime', Unsigned)  #403
        , OptionalProperty('ipDHCPLeaseTimeRemaining', Unsigned)  #404
        , OptionalProperty('ipDHCPServer', OctetString)  #405
        , OptionalProperty('bacnetIPNATTraversal', Boolean)  #410
        , OptionalProperty('bacnetIPGlobalAddress', HostNPort)  #407
        , OptionalProperty('bbmdBroadcastDistributionTable', ListOf(BDTEntry))  #414
        , OptionalProperty('bbmdAcceptFDRegistrations', Boolean)  #413
        , OptionalProperty('bbmdForeignDeviceTable', ListOf(FDTEntry))  #415
        , OptionalProperty('fdBBMDAddress', HostNPort)  #418
        , OptionalProperty('fdSubscriptionLifetime', Unsigned16)  #419
        , OptionalProperty('bacnetIPv6Mode', IPMode)  #435
        , OptionalProperty('ipv6Address', OctetString)  #436
        , OptionalProperty('ipv6PrefixLength', Unsigned8)  #437
        , OptionalProperty('bacnetIPv6UDPPort', Unsigned16)  #438
        , OptionalProperty('ipv6DefaultGateway', OctetString)  #439
        , OptionalProperty('bacnetIPv6MulticastAddress', OctetString)  #440
        , OptionalProperty('ipv6DNSServer', OctetString)  #441
        , OptionalProperty('ipv6AutoAddressingEnabled', Boolean)  #442
        , OptionalProperty('ipv6DHCPLeaseTime', Unsigned)  #443
        , OptionalProperty('ipv6DHCPLeaseTimeRemaining', Unsigned)  #444
        , OptionalProperty('ipv6DHCPServer', OctetString)  #445
        , OptionalProperty('ipv6ZoneIndex', CharacterString)  #446
        , OptionalProperty('maxMaster', Unsigned8)  #64
        , OptionalProperty('maxInfoFrames', Unsigned8)  #63
        , OptionalProperty('slaveProxyEnable', Boolean)  #172
        , OptionalProperty('manualSlaveAddressBinding', ListOf(AddressBinding))  #170
        , OptionalProperty('autoSlaveDiscovery', Boolean)  #169
        , OptionalProperty('slaveAddressBinding', ListOf(AddressBinding))  #171
        , OptionalProperty('virtualMACAddressTable', ListOf(VMACEntry))  #429
        , OptionalProperty('routingTable', ListOf(RouterEntry))  #428
        , OptionalProperty('eventDetectionEnabled', Boolean)  #353
        , OptionalProperty('notificationClass', Unsigned)  #17
        , OptionalProperty('eventEnable', EventTransitionBits)  #35
        , OptionalProperty('ackedTransitions', EventTransitionBits)  #0
        , OptionalProperty('notifyType', NotifyType)  #72
        , OptionalProperty('eventTimeStamps', ArrayOf(TimeStamp, 3))  #130
        , OptionalProperty('eventMessageTexts', ArrayOf(CharacterString, 3))  #351
        , OptionalProperty('eventMessageTextsConfig', ArrayOf(CharacterString, 3))  #352
        , OptionalProperty('eventState', EventState)  #36
        , ReadableProperty('reliabilityEvaluationInhibit', Boolean) #357
        ]

@register_object_type
class NetworkSecurityObject(Object):
    objectType = 'networkSecurity'
    properties = \
        [ WritableProperty('baseDeviceSecurityPolicy', SecurityLevel)
        , WritableProperty('networkAccessSecurityPolicies', ArrayOf(NetworkSecurityPolicy))
        , WritableProperty('securityTimeWindow', Unsigned)
        , WritableProperty('packetReorderTime', Unsigned)
        , ReadableProperty('distributionKeyRevision', Unsigned)
        , ReadableProperty('keySets', ArrayOf(SecurityKeySet))
        , WritableProperty('lastKeyServer', AddressBinding)
        , WritableProperty('securityPDUTimeout', Unsigned)
        , ReadableProperty('updateKeySetTimeout', Unsigned)
        , ReadableProperty('supportedSecurityAlgorithms', ListOf(Unsigned))
        , WritableProperty('doNotHide', Boolean)
        ]

@register_object_type
class NotificationClassObject(Object):
    objectType = 'notificationClass'
    properties = \
        [ ReadableProperty('notificationClass', Unsigned)
        , ReadableProperty('priority', ArrayOf(Unsigned))
        , ReadableProperty('ackRequired', EventTransitionBits)
        , ReadableProperty('recipientList', ListOf(Destination))
        ]

@register_object_type
class NotificationForwarderObject(Object):
    objectType = 'notificationForwarder'
    properties = \
        [ ReadableProperty('statusFlags', StatusFlags)
        , ReadableProperty('reliability', Reliability)
        , ReadableProperty('outOfService', Boolean)
        , ReadableProperty('recipientList', ListOf(Destination))
        , WritableProperty('subscribedRecipients', ListOf(EventNotificationSubscription))
        , ReadableProperty('processIdentifierFilter', ProcessIdSelection)
        , OptionalProperty('portFilter', ArrayOf(PortPermission))
        , ReadableProperty('localForwardingOnly', Boolean)
        , OptionalProperty('reliabilityEvaluationInhibit', Boolean)
        ]

@register_object_type
class OctetStringValueObject(Object):
    objectType = 'octetstringValue'
    _object_supports_cov = True

    properties = \
        [ ReadableProperty('presentValue', CharacterString)
        , ReadableProperty('statusFlags', StatusFlags)
        , OptionalProperty('eventState', EventState)
        , OptionalProperty('reliability', Reliability)
        , OptionalProperty('outOfService', Boolean)
        , OptionalProperty('priorityArray', PriorityArray)
        , OptionalProperty('relinquishDefault', OctetString)
        ]

@register_object_type
class PositiveIntegerValueObject(Object):
    objectType = 'positiveIntegerValue'
    _object_supports_cov = True

    properties = \
        [ ReadableProperty('presentValue', Unsigned)
        , ReadableProperty('statusFlags', StatusFlags)
        , OptionalProperty('eventState', EventState)
        , OptionalProperty('reliability', Reliability)
        , OptionalProperty('outOfService', Boolean)
        , ReadableProperty('units', EngineeringUnits)
        , OptionalProperty('priorityArray', PriorityArray)
        , OptionalProperty('relinquishDefault', Unsigned)
        , OptionalProperty('covIncrement', Unsigned)
        , OptionalProperty('timeDelay', Unsigned)
        , OptionalProperty('notificationClass', Unsigned)
        , OptionalProperty('highLimit', Unsigned)
        , OptionalProperty('lowLimit', Unsigned)
        , OptionalProperty('deadband', Unsigned)
        , OptionalProperty('limitEnable', LimitEnable)
        , OptionalProperty('eventEnable', EventTransitionBits)
        , OptionalProperty('ackedTransitions', EventTransitionBits)
        , OptionalProperty('notifyType', NotifyType)
        , OptionalProperty('eventTimeStamps', ArrayOf(TimeStamp))
        , OptionalProperty('eventMessageTexts', ArrayOf(CharacterString))
        , OptionalProperty('eventMessageTextsConfig', ArrayOf(CharacterString))
        , OptionalProperty('eventDetectionEnable', Boolean)
        , OptionalProperty('eventAlgorithmInhibitRef', ObjectPropertyReference)
        , OptionalProperty('eventAlgorithmInhibit', Boolean)
        , OptionalProperty('timeDelayNormal', Unsigned)
        , OptionalProperty('reliabilityEvaluationInhibit', Boolean)
        , OptionalProperty('minPresValue', Unsigned)
        , OptionalProperty('maxPresValue', Unsigned)
        , OptionalProperty('resolution', Unsigned)
        ]

@register_object_type
class ProgramObject(Object):
    objectType = 'program'
    properties = \
        [ ReadableProperty('programState', ProgramState)
        , WritableProperty('programChange', ProgramRequest)
        , OptionalProperty('reasonForHalt', ProgramError)
        , OptionalProperty('descriptionOfHalt', CharacterString)
        , OptionalProperty('programLocation', CharacterString)
        , OptionalProperty('instanceOf', CharacterString)
        , ReadableProperty('statusFlags', StatusFlags)
        , OptionalProperty('reliability', Reliability)
        , ReadableProperty('outOfService', Boolean)
        , OptionalProperty('eventDetectionEnable', Boolean)
        , OptionalProperty('notificationClass', Unsigned)
        , OptionalProperty('eventEnable', EventTransitionBits)
        , OptionalProperty('ackedTransitions', EventTransitionBits)
        , OptionalProperty('notifyType', NotifyType)
        , OptionalProperty('eventTimeStamps', ArrayOf(TimeStamp))
        , OptionalProperty('eventMessageTexts', ArrayOf(CharacterString))
        , OptionalProperty('eventMessageTextsConfig', ArrayOf(CharacterString))
        , OptionalProperty('reliabilityEvaluationInhibit', Boolean)
        ]

@register_object_type
class PulseConverterObject(Object):
    objectType = 'pulseConverter'
    _object_supports_cov = True

    properties = \
        [ ReadableProperty('presentValue', Real)
        , OptionalProperty('inputReference', ObjectPropertyReference)
        , ReadableProperty('statusFlags', StatusFlags)
        , ReadableProperty('eventState', EventState)
        , OptionalProperty('reliability', Reliability)
        , ReadableProperty('outOfService', Boolean)
        , ReadableProperty('units', EngineeringUnits)
        , ReadableProperty('scaleFactor', Real)
        , WritableProperty('adjustValue', Real)
        , ReadableProperty('count', Unsigned)
        , ReadableProperty('updateTime', DateTime)
        , ReadableProperty('countChangeTime', DateTime)
        , ReadableProperty('countBeforeChange', Unsigned)
        , OptionalProperty('covIncrement', Real)
        , OptionalProperty('covPeriod', Unsigned)
        , OptionalProperty('notificationClass', Unsigned)
        , OptionalProperty('timeDelay', Unsigned)
        , OptionalProperty('highLimit', Real)
        , OptionalProperty('lowLimit', Real)
        , OptionalProperty('deadband', Real)
        , OptionalProperty('limitEnable', LimitEnable)
        , OptionalProperty('eventEnable', EventTransitionBits)
        , OptionalProperty('ackedTransitions', EventTransitionBits)
        , OptionalProperty('notifyType', NotifyType)
        , OptionalProperty('eventTimeStamps', ArrayOf(TimeStamp))
        , OptionalProperty('eventMessageTexts', ArrayOf(CharacterString))
        , OptionalProperty('eventMessageTextsConfig', ArrayOf(CharacterString))
        , OptionalProperty('eventDetectionEnable', Boolean)
        , OptionalProperty('eventAlgorithmInhibitRef', ObjectPropertyReference)
        , OptionalProperty('eventAlgorithmInhibit', Boolean)
        , OptionalProperty('timeDelayNormal', Unsigned)
        , OptionalProperty('reliabilityEvaluationInhibit', Boolean)
        ]

@register_object_type
class ScheduleObject(Object):
    objectType = 'schedule'
    properties = \
        [ ReadableProperty('presentValue', AnyAtomic)
        , ReadableProperty('effectivePeriod', DateRange)
        , OptionalProperty('weeklySchedule', ArrayOf(DailySchedule, 7))
        , OptionalProperty('exceptionSchedule', ArrayOf(SpecialEvent))
        , ReadableProperty('scheduleDefault', AnyAtomic)
        , ReadableProperty('listOfObjectPropertyReferences', ListOf(DeviceObjectPropertyReference))
        , ReadableProperty('priorityForWriting', Unsigned)
        , ReadableProperty('statusFlags', StatusFlags)
        , ReadableProperty('reliability', Reliability)
        , ReadableProperty('outOfService', Boolean)
        , OptionalProperty('eventDetectionEnable', Boolean)
        , OptionalProperty('notificationClass', Unsigned)
        , OptionalProperty('eventEnable', EventTransitionBits)
        , ReadableProperty('eventState', EventState)
        , OptionalProperty('ackedTransitions', EventTransitionBits)
        , OptionalProperty('notifyType', NotifyType)
        , OptionalProperty('eventTimeStamps', ArrayOf(TimeStamp))
        , OptionalProperty('eventMessageTexts', ArrayOf(CharacterString))
        , OptionalProperty('eventMessageTextsConfig', ArrayOf(CharacterString))
        , OptionalProperty('reliabilityEvaluationInhibit', Boolean)
        ]

@register_object_type
class StructuredViewObject(Object):
    objectType = 'structuredView'
    properties = \
        [ ReadableProperty('nodeType', NodeType)
        , OptionalProperty('nodeSubtype', CharacterString)
        , ReadableProperty('subordinateList', ArrayOf(DeviceObjectReference))
        , OptionalProperty('subordinateAnnotations', ArrayOf(CharacterString))
        ]

@register_object_type
class TimePatternValueObject(Object):
    objectType = 'timePatternValue'
    _object_supports_cov = True

    properties = \
        [ ReadableProperty('presentValue', Time)
        , ReadableProperty('statusFlags', StatusFlags)
        , OptionalProperty('eventState', EventState)
        , OptionalProperty('reliability', Reliability)
        , OptionalProperty('outOfService', Boolean)
        , OptionalProperty('priorityArray', PriorityArray)
        , OptionalProperty('relinquishDefault', Time)
        ]

@register_object_type
class TimeValueObject(Object):
    objectType = 'timeValue'
    _object_supports_cov = True

    properties = \
        [ ReadableProperty('presentValue', Time)
        , ReadableProperty('statusFlags', StatusFlags)
        , OptionalProperty('eventState', EventState)
        , OptionalProperty('reliability', Reliability)
        , OptionalProperty('outOfService', Boolean)
        , OptionalProperty('priorityArray', PriorityArray)
        , OptionalProperty('relinquishDefault', Time)
        ]

@register_object_type
class TrendLogObject(Object):
    objectType = 'trendLog'
    properties = \
        [ ReadableProperty('statusFlags', StatusFlags)
        , ReadableProperty('eventState', EventState)
        , OptionalProperty('reliability', Reliability)
        , WritableProperty('enable', Boolean)
        , OptionalProperty('startTime', DateTime)
        , OptionalProperty('stopTime', DateTime)
        , OptionalProperty('logDeviceObjectProperty', DeviceObjectPropertyReference)
        , OptionalProperty('logInterval', Unsigned)
        , OptionalProperty('covResubscriptionInterval', Unsigned)
        , OptionalProperty('clientCovIncrement', ClientCOV)
        , ReadableProperty('stopWhenFull', Boolean)
        , ReadableProperty('bufferSize', Unsigned)
        , ReadableProperty('logBuffer', ListOf(LogRecord))
        , WritableProperty('recordCount', Unsigned)
        , ReadableProperty('totalRecordCount', Unsigned)
        , ReadableProperty('loggingType', LoggingType)
        , OptionalProperty('alignIntervals', Boolean)
        , OptionalProperty('intervalOffset', Unsigned)
        , OptionalProperty('trigger', Boolean)
        , ReadableProperty('statusFlags', StatusFlags)
        , OptionalProperty('reliability', Reliability)
        , OptionalProperty('notificationThreshold', Unsigned)
        , OptionalProperty('recordsSinceNotification', Unsigned)
        , OptionalProperty('lastNotifyRecord', Unsigned)
        , ReadableProperty('eventState', EventState)
        , OptionalProperty('notificationClass', Unsigned)
        , OptionalProperty('eventEnable', EventTransitionBits)
        , OptionalProperty('ackedTransitions', EventTransitionBits)
        , OptionalProperty('notifyType', NotifyType)
        , OptionalProperty('eventTimeStamps', ArrayOf(TimeStamp))
        , OptionalProperty('eventMessageTexts', ArrayOf(CharacterString))
        , OptionalProperty('eventMessageTextsConfig', ArrayOf(CharacterString))
        , OptionalProperty('eventDetectionEnable', Boolean)
        , OptionalProperty('eventAlgorithmInhibitRef', ObjectPropertyReference)
        , OptionalProperty('eventAlgorithmInhibit', Boolean)
        , OptionalProperty('reliabilityEvaluationInhibit', Boolean)
        ]

@register_object_type
class TrendLogMultipleObject(Object):
    objectType = 'trendLogMultiple'
    properties = \
        [ ReadableProperty('statusFlags', StatusFlags)
        , ReadableProperty('eventState', EventState)
        , OptionalProperty('reliability', Reliability)
        , WritableProperty('enable', Boolean)
        , OptionalProperty('startTime', DateTime)
        , OptionalProperty('stopTime', DateTime)
        , ReadableProperty('logDeviceObjectProperty', ArrayOf(DeviceObjectPropertyReference))
        , ReadableProperty('loggingType', LoggingType)
        , ReadableProperty('logInterval', Unsigned)
        , OptionalProperty('alignIntervals', Boolean)
        , OptionalProperty('intervalOffset', Unsigned)
        , OptionalProperty('trigger', Boolean)
        , ReadableProperty('stopWhenFull', Boolean)
        , ReadableProperty('bufferSize', Unsigned)
        , ReadableProperty('logBuffer', ListOf(LogMultipleRecord))
        , WritableProperty('recordCount', Unsigned)
        , ReadableProperty('totalRecordCount', Unsigned)
        , OptionalProperty('notificationThreshold', Unsigned)
        , OptionalProperty('recordsSinceNotification', Unsigned)
        , OptionalProperty('lastNotifyRecord', Unsigned)
        , OptionalProperty('notificationClass', Unsigned)
        , OptionalProperty('eventEnable', EventTransitionBits)
        , OptionalProperty('ackedTransitions', EventTransitionBits)
        , OptionalProperty('notifyType', NotifyType)
        , OptionalProperty('eventTimeStamps', ArrayOf(TimeStamp))
        , OptionalProperty('eventMessageTexts', ArrayOf(CharacterString))
        , OptionalProperty('eventMessageTextsConfig', ArrayOf(CharacterString))
        , OptionalProperty('eventDetectionEnable', Boolean)
        , OptionalProperty('eventAlgorithmInhibitRef', ObjectPropertyReference)
        , OptionalProperty('eventAlgorithmInhibit', Boolean)
        , OptionalProperty('reliabilityEvaluationInhibit', Boolean)
        ]
