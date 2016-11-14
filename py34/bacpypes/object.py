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
    Unsigned
from .constructeddata import AnyAtomic, Array, ArrayOf, Choice, Element, \
    Sequence, SequenceOf
from .basetypes import AccessCredentialDisable, AccessCredentialDisableReason, \
    AccessEvent, AccessPassbackMode, AccessRule, AccessThreatLevel, \
    AccessUserType, AccessZoneOccupancyState, AccumulatorRecord, Action, \
    ActionList, AddressBinding, AssignedAccessRights, AuthenticationFactor, \
    AuthenticationFactorFormat, AuthenticationPolicy, AuthenticationStatus, \
    AuthorizationException, AuthorizationMode, BackupState, BinaryPV, \
    COVSubscription, CalendarEntry, ChannelValue, ClientCOV, \
    CredentialAuthenticationFactor, DailySchedule, DateRange, DateTime, \
    Destination, DeviceObjectPropertyReference, DeviceObjectReference, \
    DeviceStatus, DoorAlarmState, DoorSecuredStatus, DoorStatus, DoorValue, \
    EngineeringUnits, EventNotificationSubscription, EventParameter, \
    EventState, EventTransitionBits, EventType, FaultParameter, FaultType, \
    FileAccessMethod, LifeSafetyMode, LifeSafetyOperation, LifeSafetyState, \
    LightingCommand, LightingInProgress, LightingTransition, LimitEnable, \
    LockStatus, LogMultipleRecord, LogRecord, LogStatus, LoggingType, \
    Maintenance, NetworkSecurityPolicy, NodeType, NotifyType, \
    ObjectPropertyReference, ObjectTypesSupported, OptionalCharacterString, \
    Polarity, PortPermission, Prescale, PriorityArray, ProcessIdSelection, \
    ProgramError, ProgramRequest, ProgramState, PropertyAccessResult, \
    PropertyIdentifier, Recipient, Reliability, RestartReason, Scale, \
    SecurityKeySet, SecurityLevel, Segmentation, ServicesSupported, \
    SetpointReference, ShedLevel, ShedState, SilencedState, SpecialEvent, \
    StatusFlags, TimeStamp, VTClass, VTSession, WriteStatus
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
        self.datatype = datatype
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

            # if it's atomic, make sure it's valid
            if issubclass(self.datatype, Atomic):
                if _debug: Property._debug("    - property is atomic, checking value")
                if not self.datatype.is_valid(value):
                    raise InvalidParameterDatatype("%s must be of type %s" % (
                            self.identifier, self.datatype.__name__,
                            ))

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

    """The property is required to be present and readable using BACnet services."""

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
        elif isinstance(value, int):
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
class Object:

    _debug_contents = ('_app',)

    properties = \
        [ ObjectIdentifierProperty('objectIdentifier', ObjectIdentifier, optional=False)
        , ReadableProperty('objectName', CharacterString, optional=False)
        , ReadableProperty('description', CharacterString)
        , OptionalProperty('profileName', CharacterString)
        , ReadableProperty('propertyList', ArrayOf(PropertyIdentifier))
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

        # start with a clean array of property identifiers
        if 'propertyList' in initargs:
            propertyList = None
        else:
            propertyList = ArrayOf(PropertyIdentifier)()
            initargs['propertyList'] = propertyList

        # initialize the object
        for propid, prop in self._properties.items():
            if propid in initargs:
                if _debug: Object._debug("    - setting %s from initargs", propid)

                # defer to the property object for error checking
                prop.WriteProperty(self, initargs[propid], direct=True)

                # add it to the property list if we are building one
                if propertyList is not None:
                    propertyList.append(propid)

            elif prop.default is not None:
                if _debug: Object._debug("    - setting %s from default", propid)

                # default values bypass property interface
                self._values[propid] = prop.default

                # add it to the property list if we are building one
                if propertyList is not None:
                    propertyList.append(propid)

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

        # tell the object it has a new property
        if 'propertyList' in self._values:
            property_list = self.propertyList
            if prop.identifier not in property_list:
                if _debug: Object._debug("    - adding to property list")
                property_list.append(prop.identifier)

    def delete_property(self, prop):
        """Delete a property from an object.  The property is an instance of
        a Property or one of its derived classes, but only the property
        is relavent.  Deleting a property disconnects it from the collection of
        properties common to all of the objects of its class."""
        if _debug: Object._debug("delete_property %r", value)

        # make a copy of the properties dictionary
        self._properties = _copy(self._properties)

        # delete the property from the dictionary and values
        del self._properties[prop.identifier]
        if prop.identifier in self._values:
            del self._values[prop.identifier]

        # remove the property identifier from its list of know properties
        if 'propertyList' in self._values:
            property_list = self.propertyList
            if prop.identifier in property_list:
                if _debug: Object._debug("    - removing from property list")
                property_list.remove(prop.identifier)

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
        , ReadableProperty('reasonForDisable', SequenceOf(AccessCredentialDisableReason))
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
        , OptionalProperty('authorizationExemptions', SequenceOf(AuthorizationException))
        , OptionalProperty('reliabilityEvaluationInhibit', Boolean)
#       , OptionalProperty('masterExemption', Boolean)
#       , OptionalProperty('passbackExemption', Boolean)
#       , OptionalProperty('occupancyExemption', Boolean)
        ]

@register_object_type
class AccessDoorObject(Object):
    objectType = 'accessDoor'
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
        , OptionalProperty('maskedAlarmValues', SequenceOf(DoorAlarmState))
        , OptionalProperty('maintenanceRequired', Maintenance)
        , OptionalProperty('timeDelay', Unsigned)
        , OptionalProperty('notificationClass', Unsigned)
        , OptionalProperty('alarmValues', SequenceOf(DoorAlarmState))
        , OptionalProperty('faultValues', SequenceOf(DoorAlarmState))
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
        , OptionalProperty('failedAttemptEvents', SequenceOf(AccessEvent))
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
        , OptionalProperty('accessAlarmEvents', SequenceOf(AccessEvent))
        , OptionalProperty('accessTransactionEvents', SequenceOf(AccessEvent))
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
        , OptionalProperty('members', SequenceOf(DeviceObjectReference))
        , OptionalProperty('memberOf', SequenceOf(DeviceObjectReference))
        , ReadableProperty('credentials', SequenceOf(DeviceObjectReference))
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
        , OptionalProperty('credentialsInZone', SequenceOf(DeviceObjectReference) )
        , OptionalProperty('lastCredentialAdded', DeviceObjectReference)
        , OptionalProperty('lastCredentialAddedTime', DateTime)
        , OptionalProperty('lastCredentialRemoved', DeviceObjectReference)
        , OptionalProperty('lastCredentialRemovedTime', DateTime)
        , OptionalProperty('passbackMode', AccessPassbackMode)
        , OptionalProperty('passbackTimeout', Unsigned)
        , ReadableProperty('entryPoints', SequenceOf(DeviceObjectReference))
        , ReadableProperty('exitPoints', SequenceOf(DeviceObjectReference))
        , OptionalProperty('timeDelay', Unsigned)
        , OptionalProperty('notificationClass', Unsigned)
        , OptionalProperty('alarmValues', SequenceOf(AccessZoneOccupancyState))
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
        , OptionalProperty('eventDetectionEnable', Boolean)
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
        , ReadableProperty('dateList', SequenceOf(CalendarEntry))
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
        , OptionalProperty('vtClassesSupported', SequenceOf(VTClass))
        , OptionalProperty('activeVtSessions', SequenceOf(VTSession))
        , OptionalProperty('localTime', Time)
        , OptionalProperty('localDate', Date)
        , OptionalProperty('utcOffset', Integer)
        , OptionalProperty('daylightSavingsStatus', Boolean)
        , OptionalProperty('apduSegmentTimeout', Unsigned)
        , ReadableProperty('apduTimeout', Unsigned)
        , ReadableProperty('numberOfApduRetries', Unsigned)
        , OptionalProperty('timeSynchronizationRecipients', SequenceOf(Recipient))
        , OptionalProperty('maxMaster', Unsigned)
        , OptionalProperty('maxInfoFrames', Unsigned)
        , ReadableProperty('deviceAddressBinding', SequenceOf(AddressBinding))
        , ReadableProperty('databaseRevision', Unsigned)
        , OptionalProperty('configurationFiles', ArrayOf(ObjectIdentifier))
        , OptionalProperty('lastRestoreTime', TimeStamp)
        , OptionalProperty('backupFailureTimeout', Unsigned)
        , OptionalProperty('backupPreparationTime', Unsigned)
        , OptionalProperty('restorePreparationTime', Unsigned)
        , OptionalProperty('restoreCompletionTime', Unsigned)
        , OptionalProperty('backupAndRestoreState', BackupState)
        , OptionalProperty('activeCovSubscriptions', SequenceOf(COVSubscription))
        , OptionalProperty('maxSegmentsAccepted', Unsigned)
        , OptionalProperty('slaveProxyEnable', ArrayOf(Boolean))
        , OptionalProperty('autoSlaveDiscovery', ArrayOf(Boolean))
        , OptionalProperty('slaveAddressBinding', SequenceOf(AddressBinding))
        , OptionalProperty('manualSlaveAddressBinding', SequenceOf(AddressBinding))
        , OptionalProperty('lastRestartReason', RestartReason)
        , OptionalProperty('timeOfDeviceRestart', TimeStamp)
        , OptionalProperty('restartNotificationRecipients', SequenceOf(Recipient))
        , OptionalProperty('utcTimeSynchronizationRecipients', SequenceOf(Recipient))
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
        , OptionalProperty('eventDetectionEnable', Boolean)
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
        , ReadableProperty('logBuffer', SequenceOf(EventLogRecord))
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
        , OptionalProperty('covuRecipients', SequenceOf(Recipient))
        , OptionalProperty('reliabilityEvaluationInhibit', Boolean)
        ]

@register_object_type
class GroupObject(Object):
    objectType = 'group'
    properties = \
        [ ReadableProperty('listOfGroupMembers', SequenceOf(ReadAccessSpecification))
        , ReadableProperty('presentValue', SequenceOf(ReadAccessResult))
        ]

@register_object_type
class IntegerValueObject(Object):
    objectType = 'integerValue'
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
    properties = \
        [ ReadableProperty('presentValue', LifeSafetyState)
        , ReadableProperty('trackingValue', LifeSafetyState)
        , OptionalProperty('deviceType', CharacterString)
        , ReadableProperty('statusFlags', StatusFlags)
        , ReadableProperty('eventState', EventState)
        , ReadableProperty('reliability', Reliability)
        , ReadableProperty('outOfService', Boolean)
        , WritableProperty('mode', LifeSafetyMode)
        , ReadableProperty('acceptedModes', SequenceOf(LifeSafetyMode))
        , OptionalProperty('timeDelay', Unsigned)
        , OptionalProperty('notificationClass', Unsigned)
        , OptionalProperty('lifeSafetyAlarmValues', SequenceOf(LifeSafetyState))
        , OptionalProperty('alarmValues', SequenceOf(LifeSafetyState))
        , OptionalProperty('faultValues', SequenceOf(LifeSafetyState))
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
        , OptionalProperty('memberOf', SequenceOf(DeviceObjectReference))
        ]

@register_object_type
class LifeSafetyZoneObject(Object):
    objectType = 'lifeSafetyZone'
    properties = \
        [ ReadableProperty('presentValue', LifeSafetyState)
        , ReadableProperty('trackingValue', LifeSafetyState)
        , OptionalProperty('deviceType', CharacterString)
        , ReadableProperty('statusFlags', StatusFlags)
        , ReadableProperty('eventState', EventState)
        , ReadableProperty('reliability', Reliability)
        , ReadableProperty('outOfService', Boolean)
        , WritableProperty('mode', LifeSafetyMode)
        , ReadableProperty('acceptedModes', SequenceOf(LifeSafetyMode))
        , OptionalProperty('timeDelay', Unsigned)
        , OptionalProperty('notificationClass', Unsigned)
        , OptionalProperty('lifeSafetyAlarmValues', SequenceOf(LifeSafetyState))
        , OptionalProperty('alarmValues', SequenceOf(LifeSafetyState))
        , OptionalProperty('faultValues', SequenceOf(LifeSafetyState))
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
        , ReadableProperty('zoneMembers', SequenceOf(DeviceObjectReference))
        , OptionalProperty('memberOf', SequenceOf(DeviceObjectReference))
        ]

@register_object_type
class LightingOutputObject(Object):
    objectType = 'lightingOutput'
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
        , OptionalProperty('alarmValues', SequenceOf(Unsigned))
        , OptionalProperty('faultValues', SequenceOf(Unsigned))
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
        , OptionalProperty('alarmValues', SequenceOf(Unsigned))
        , OptionalProperty('faultValues', SequenceOf(Unsigned))
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
        , ReadableProperty('supportedSecurityAlgorithms', SequenceOf(Unsigned))
        , WritableProperty('doNotHide', Boolean)
        ]

@register_object_type
class NotificationClassObject(Object):
    objectType = 'notificationClass'
    properties = \
        [ ReadableProperty('notificationClass', Unsigned)
        , ReadableProperty('priority', ArrayOf(Unsigned))
        , ReadableProperty('ackRequired', EventTransitionBits)
        , ReadableProperty('recipientList', SequenceOf(Destination))
        ]

@register_object_type
class NotificationForwarderObject(Object):
    objectType = 'notificationForwarder'
    properties = \
        [ ReadableProperty('statusFlags', StatusFlags)
        , ReadableProperty('reliability', Reliability)
        , ReadableProperty('outOfService', Boolean)
        , ReadableProperty('recipientList', SequenceOf(Destination))
        , WritableProperty('subscribedRecipients', SequenceOf(EventNotificationSubscription))
        , ReadableProperty('processIdentifierFilter', ProcessIdSelection)
        , OptionalProperty('portFilter', ArrayOf(PortPermission))
        , ReadableProperty('localForwardingOnly', Boolean)
        , OptionalProperty('reliabilityEvaluationInhibit', Boolean)
        ]

@register_object_type
class OctetStringValueObject(Object):
    objectType = 'octetstringValue'
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
        , OptionalProperty('weeklySchedule', ArrayOf(DailySchedule))
        , OptionalProperty('exceptionSchedule', ArrayOf(SpecialEvent))
        , ReadableProperty('scheduleDefault', AnyAtomic)
        , ReadableProperty('listOfObjectPropertyReferences', SequenceOf(DeviceObjectPropertyReference))
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
        , ReadableProperty('logBuffer', SequenceOf(LogRecord))
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
        , ReadableProperty('logBuffer', SequenceOf(LogMultipleRecord))
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
