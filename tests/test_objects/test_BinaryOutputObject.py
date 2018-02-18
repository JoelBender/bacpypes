#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Nose Test Objects BinaryOutputObject
---------------------
"""

import unittest
from helper import TestObjectHelper

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, xtob
from bacpypes.object import BinaryOutputObject, WritableProperty, ReadableProperty, OptionalProperty
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

# some debugging
_debug = 1
_log = ModuleLogger(globals())

@bacpypes_debugging
class Test_BinaryOutputObject(unittest.TestCase, TestObjectHelper):
    """
    This test will verify that the object created has good number of properties
    Will test that each property is correct datatype
    Will test that only Writable property can be written
    Will test that all properties can be read
    """
    def setUp(self):
        if _debug: Test_BinaryOutputObject._debug("Test_BinaryOutputObject")
        self.obj = BinaryOutputObject()
        self.objType = 'binaryOutput'
        self.identifiers = self.build_list_of_identifiers(self.obj.properties)
        self.numberOfPropertiesRequired = 32
        self.writeValue = 1234
        self.listOfProperties = \
        [ (WritableProperty,'presentValue', BinaryPV)
        , (OptionalProperty,'deviceType', CharacterString)
        , (ReadableProperty,'statusFlags', StatusFlags)
        , (ReadableProperty,'eventState', EventState)
        , (OptionalProperty,'reliability', Reliability)
        , (ReadableProperty,'outOfService', Boolean)
        , (ReadableProperty,'polarity', Polarity)
        , (OptionalProperty,'inactiveText', CharacterString)
        , (OptionalProperty,'activeText', CharacterString)
        , (OptionalProperty,'changeOfStateTime', DateTime)
        , (OptionalProperty,'changeOfStateCount', Unsigned)
        , (OptionalProperty,'timeOfStateCountReset', DateTime)
        , (OptionalProperty,'elapsedActiveTime', Unsigned)
        , (OptionalProperty,'timeOfActiveTimeReset', DateTime)
        , (OptionalProperty,'minimumOffTime', Unsigned)
        , (OptionalProperty,'minimumOnTime', Unsigned)
        , (ReadableProperty,'priorityArray', PriorityArray)
        , (ReadableProperty,'relinquishDefault', BinaryPV)
        , (OptionalProperty,'timeDelay', Unsigned)
        , (OptionalProperty,'notificationClass', Unsigned)
        , (OptionalProperty,'feedbackValue', BinaryPV)
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
        