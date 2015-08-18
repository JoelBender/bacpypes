#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Nose Test Objects LightingOutputObject
---------------------
"""

import unittest
from helper import TestObjectHelper

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, xtob
from bacpypes.object import LightingOutputObject, WritableProperty, ReadableProperty, OptionalProperty, EventLogRecord
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
class Test_LightingOutputObject(unittest.TestCase, TestObjectHelper):
    """
    This test will verify that the object created has good number of properties
    Will test that each property is correct datatype
    Will test that only Writable property can be written
    Will test that all properties can be read
    """
    def setUp(self):
        if _debug: Test_LightingOutputObject._debug("Test_LightingOutputObject")
        self.obj = LightingOutputObject()
        self.objType = 'lightingOutput'
        self.identifiers = self.build_list_of_identifiers(self.obj.properties)
        self.numberOfPropertiesRequired = 24
        self.writeValue = 0
        self.listOfProperties = \
        [ (WritableProperty,'presentValue', Real)
        , (ReadableProperty,'trackingValue', Real)
        , (WritableProperty,'lightingCommand', LightingCommand)
        , (ReadableProperty,'inProgress', LightingInProgress)
        , (ReadableProperty,'statusFlags', StatusFlags)
        , (OptionalProperty,'reliability', Reliability)
        , (ReadableProperty,'outOfService', Boolean)
        , (ReadableProperty,'blinkWarnEnable', Boolean)
        , (ReadableProperty,'egressTime', Unsigned)
        , (ReadableProperty,'egressActive', Boolean)
        , (ReadableProperty,'defaultFadeTime', Unsigned)
        , (ReadableProperty,'defaultRampRate', Real)
        , (ReadableProperty,'defaultStepIncrement', Real)
        , (OptionalProperty,'transition', LightingTransition)
        , (OptionalProperty,'feedbackValue', Real)
        , (ReadableProperty,'priorityArray', PriorityArray)
        , (ReadableProperty,'relinquishDefault', Real)
        , (OptionalProperty,'power', Real)
        , (OptionalProperty,'instantaneousPower', Real)
        , (OptionalProperty,'minActualValue', Real)
        , (OptionalProperty,'maxActualValue', Real)
        , (ReadableProperty,'lightingCommandDefaultPriority', Unsigned)
        , (OptionalProperty,'covIncrement', Real)
        , (OptionalProperty,'reliabilityEvaluationInhibit', Boolean)
        ]
        
    def test_object(self):
        self.object_type(self.obj,self.objType)
        self.object_number_of_properties(self.obj,self.numberOfPropertiesRequired)
        self.object_property_identifiers(self.obj)
        self.object_property_dataType(self.obj)
        self.object_noWritingToReadableProperty(self.obj,self.writeValue)
        #TODO Object not completed
        #self.object_can_write_to_writableProperty(self.obj,self.writeValue)
        #self.object_cannot_write_wrong_property_to_writableProperty(self.obj)
        self.object_can_read_property(self.obj)
        