#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Nose Test Objects TrendLogMultipleObject
---------------------
"""

import unittest
from helper import TestObjectHelper

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, xtob
from bacpypes.object import TrendLogMultipleObject, WritableProperty, ReadableProperty, OptionalProperty, EventLogRecord
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
class Test_TrendLogMultipleObject(unittest.TestCase, TestObjectHelper):
    """
    This test will verify that the object created has good number of properties
    Will test that each property is correct datatype
    Will test that only Writable property can be written
    Will test that all properties can be read
    """
    def setUp(self):
        if _debug: Test_TrendLogMultipleObject._debug("Test_TrendLogMultipleObject")
        self.obj = TrendLogMultipleObject()
        self.objType = 'trendLogMultiple'
        self.identifiers = self.build_list_of_identifiers(self.obj.properties)
        self.numberOfPropertiesRequired = 31
        self.writeValue = 0
        self.listOfProperties = \
        [ (ReadableProperty,'statusFlags', StatusFlags)
        , (ReadableProperty,'eventState', EventState)
        , (OptionalProperty,'reliability', Reliability)
        , (WritableProperty,'enable', Boolean)
        , (OptionalProperty,'startTime', DateTime)
        , (OptionalProperty,'stopTime', DateTime)
        , (ReadableProperty,'logDeviceObjectProperty', ArrayOf(DeviceObjectPropertyReference))
        , (ReadableProperty,'loggingType', LoggingType)
        , (ReadableProperty,'logInterval', Unsigned)
        , (OptionalProperty,'alignIntervals', Boolean)
        , (OptionalProperty,'intervalOffset', Unsigned)
        , (OptionalProperty,'trigger', Boolean)
        , (ReadableProperty,'stopWhenFull', Boolean)
        , (ReadableProperty,'bufferSize', Unsigned)
        , (ReadableProperty,'logBuffer', SequenceOf(LogMultipleRecord))
        , (WritableProperty,'recordCount', Unsigned)
        , (ReadableProperty,'totalRecordCount', Unsigned)
        , (OptionalProperty,'notificationThreshold', Unsigned)
        , (OptionalProperty,'recordsSinceNotification', Unsigned)
        , (OptionalProperty,'lastNotifyRecord', Unsigned)
        , (OptionalProperty,'notificationClass', Unsigned)
        , (OptionalProperty,'eventEnable', EventTransitionBits)
        , (OptionalProperty,'ackedTransitions', EventTransitionBits)
        , (OptionalProperty,'notifyType', NotifyType)
        , (OptionalProperty,'eventTimeStamps', ArrayOf(TimeStamp))
        , (OptionalProperty,'eventMessageTexts', ArrayOf(CharacterString))
        , (OptionalProperty,'eventMessageTextsConfig', ArrayOf(CharacterString))
        , (OptionalProperty,'eventDetectionEnable', Boolean)
        , (OptionalProperty,'eventAlgorithmInhibitRef', ObjectPropertyReference)
        , (OptionalProperty,'eventAlgorithmInhibit', Boolean)
        , (OptionalProperty,'reliabilityEvaluationInhibit', Boolean)
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
        