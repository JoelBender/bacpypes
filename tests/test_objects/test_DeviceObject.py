#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Nose Test Objects DeviceObject
---------------------
"""

import unittest
from helper import TestObjectHelper

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, xtob
from bacpypes.object import DeviceObject, WritableProperty, ReadableProperty, OptionalProperty
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
class Test_DeviceObject(unittest.TestCase, TestObjectHelper):
    """
    This test will verify that the object created has good number of properties
    Will test that each property is correct datatype
    Will test that only Writable property can be written
    Will test that all properties can be read
    """
    def setUp(self):
        if _debug: Test_DeviceObject._debug("Test_DeviceObject")
        self.obj = DeviceObject()
        self.objType = 'device'
        self.identifiers = self.build_list_of_identifiers(self.obj.properties)
        self.numberOfPropertiesRequired = 49
        self.writeValue = 0
        self.listOfProperties = \
        [ (ReadableProperty,'systemStatus', DeviceStatus)
        , (ReadableProperty,'vendorName', CharacterString)
        , (ReadableProperty,'vendorIdentifier', Unsigned)
        , (ReadableProperty,'modelName', CharacterString)
        , (ReadableProperty,'firmwareRevision', CharacterString)
        , (ReadableProperty,'applicationSoftwareVersion', CharacterString)
        , (OptionalProperty,'location', CharacterString)
        , (ReadableProperty,'protocolVersion', Unsigned)
        , (ReadableProperty,'protocolRevision', Unsigned)
        , (ReadableProperty,'protocolServicesSupported', ServicesSupported)
        , (ReadableProperty,'protocolObjectTypesSupported', ObjectTypesSupported)
        , (ReadableProperty,'objectList', ArrayOf(ObjectIdentifier))
        , (OptionalProperty,'structuredObjectList', ArrayOf(ObjectIdentifier))
        , (ReadableProperty,'maxApduLengthAccepted', Unsigned)
        , (ReadableProperty,'segmentationSupported', Segmentation)
        , (OptionalProperty,'vtClassesSupported', SequenceOf(VTClass))
        , (OptionalProperty,'activeVtSessions', SequenceOf(VTSession))
        , (OptionalProperty,'localTime', Time)
        , (OptionalProperty,'localDate', Date)
        , (OptionalProperty,'utcOffset', Integer)
        , (OptionalProperty,'daylightSavingsStatus', Boolean)
        , (OptionalProperty,'apduSegmentTimeout', Unsigned)
        , (ReadableProperty,'apduTimeout', Unsigned)
        , (ReadableProperty,'numberOfApduRetries', Unsigned)
        , (OptionalProperty,'timeSynchronizationRecipients', SequenceOf(Recipient))
        , (OptionalProperty,'maxMaster', Unsigned)
        , (OptionalProperty,'maxInfoFrames', Unsigned)
        , (ReadableProperty,'deviceAddressBinding', SequenceOf(AddressBinding))
        , (ReadableProperty,'databaseRevision', Unsigned)
        , (OptionalProperty,'configurationFiles', ArrayOf(ObjectIdentifier))
        , (OptionalProperty,'lastRestoreTime', TimeStamp)
        , (OptionalProperty,'backupFailureTimeout', Unsigned)
        , (OptionalProperty,'backupPreparationTime', Unsigned)
        , (OptionalProperty,'restorePreparationTime', Unsigned)
        , (OptionalProperty,'restoreCompletionTime', Unsigned)
        , (OptionalProperty,'backupAndRestoreState', BackupState)
        , (OptionalProperty,'activeCovSubscriptions', SequenceOf(COVSubscription))
        , (OptionalProperty,'maxSegmentsAccepted', Unsigned)
        , (OptionalProperty,'slaveProxyEnable', ArrayOf(Boolean))
        , (OptionalProperty,'autoSlaveDiscovery', ArrayOf(Boolean))
        , (OptionalProperty,'slaveAddressBinding', SequenceOf(AddressBinding))
        , (OptionalProperty,'manualSlaveAddressBinding', SequenceOf(AddressBinding))
        , (OptionalProperty,'lastRestartReason', RestartReason)
        , (OptionalProperty,'timeOfDeviceRestart', TimeStamp)
        , (OptionalProperty,'restartNotificationRecipients', SequenceOf(Recipient))
        , (OptionalProperty,'utcTimeSynchronizationRecipients', SequenceOf(Recipient))
        , (OptionalProperty,'timeSynchronizationInterval', Unsigned)
        , (OptionalProperty,'alignIntervals', Boolean)
        , (OptionalProperty,'intervalOffset', Unsigned)
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
        