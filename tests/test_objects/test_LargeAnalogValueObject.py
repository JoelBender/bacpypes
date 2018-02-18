#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Nose Test Objects LargeAnalogValueObject
---------------------
"""

import unittest
from helper import TestObjectHelper

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, xtob
from bacpypes.object import LargeAnalogValueObject, WritableProperty, ReadableProperty, OptionalProperty, EventLogRecord
from bacpypes.primitivedata import BitString, Boolean, CharacterString, Date, Double, \
    Enumerated, Integer, Null, ObjectIdentifier, OctetString, Real, Time, \
    Unsigned
from bacpypes.constructeddata import AnyAtomic, Array, ArrayOf, Choice, Element, \
    Sequence, SequenceOf
from bacpypes.basetypes import AccessCredentialDisable, AccessCredentialDisableReason, \
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
from bacpypes.errors import ConfigurationError, ExecutionError
from bacpypes.apdu import EventNotificationParameters, ReadAccessSpecification, \
    ReadAccessResult

# some debugging
_debug = 1
_log = ModuleLogger(globals())

@bacpypes_debugging
class Test_LargeAnalogValueObject(unittest.TestCase, TestObjectHelper):
    """
    This test will verify that the object created has good number of properties
    Will test that each property is correct datatype
    Will test that only Writable property can be written
    Will test that all properties can be read
    """
    def setUp(self):
        if _debug: Test_LargeAnalogValueObject._debug("Test_LargeAnalogValueObject")
        self.obj = LargeAnalogValueObject()
        self.objType = 'largeAnalogValue'
        self.identifiers = self.build_list_of_identifiers(self.obj.properties)
        self.numberOfPropertiesRequired = 29
        self.writeValue = 0
        self.listOfProperties = \
        [ (ReadableProperty,'presentValue', Double)
        , (ReadableProperty,'statusFlags', StatusFlags)
        , (OptionalProperty,'eventState', EventState)
        , (OptionalProperty,'reliability', Reliability)
        , (OptionalProperty,'outOfService', Boolean)
        , (ReadableProperty,'units', EngineeringUnits)
        , (OptionalProperty,'priorityArray', PriorityArray)
        , (OptionalProperty,'relinquishDefault', Integer)
        , (OptionalProperty,'covIncrement', Unsigned)
        , (OptionalProperty,'timeDelay', Unsigned)
        , (OptionalProperty,'notificationClass', Unsigned)
        , (OptionalProperty,'highLimit', Double)
        , (OptionalProperty,'lowLimit', Double)
        , (OptionalProperty,'deadband', Double)
        , (OptionalProperty,'limitEnable', LimitEnable)
        , (OptionalProperty,'eventEnable', EventTransitionBits)
        , (OptionalProperty,'ackedTransitions', EventTransitionBits)
        , (OptionalProperty,'notifyType', NotifyType)
        , (OptionalProperty,'eventTimeStamps', ArrayOf(TimeStamp))
        , (OptionalProperty,'eventMessageTexts', ArrayOf(CharacterString))
        , (OptionalProperty,'eventMessageTextsConfig', ArrayOf(CharacterString))
        , (OptionalProperty,'eventDetectionEnable', Boolean)
        , (OptionalProperty,'eventAlgorithmInhibitRef', ObjectPropertyReference)
        , (OptionalProperty,'eventAlgorithmInhibit', Boolean)
        , (OptionalProperty,'timeDelayNormal', Unsigned)
        , (OptionalProperty,'reliabilityEvaluationInhibit', Boolean)
        , (OptionalProperty,'minPresValue', Double)
        , (OptionalProperty,'maxPresValue', Double)
        , (OptionalProperty,'resolution', Double)
        ]
        
    def test_object(self):
        self.object_type(self.obj,self.objType)
        self.object_number_of_properties(self.obj,self.numberOfPropertiesRequired)
        self.object_property_identifiers(self.obj)
        self.object_property_dataType(self.obj)
        self.object_noWritingToReadableProperty(self.obj,self.writeValue)
        self.object_can_write_to_writableProperty(self.obj,self.writeValue)
        self.object_cannot_write_wrong_property_to_writableProperty(self.obj)
        self.object_can_read_property(self.obj)
        