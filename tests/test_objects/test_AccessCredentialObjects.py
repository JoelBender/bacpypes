#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Nose Test Objects AccessCredentialObjects
---------------------
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, xtob
from bacpypes.object import AccessCredentialObject, WritableProperty, ReadableProperty, OptionalProperty
from bacpypes.primitivedata import Unsigned, Integer, Boolean
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
_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
class TestHelper():
    def build_list_of_identifiers(properties):
        identifiers = []
        numberOfProperties = 0
        for each in properties:                        
            identifiers.append(each.identifier)
            numberOfProperties += 1
        return (identifiers,numberOfProperties)
            
@bacpypes_debugging
class Test_AccessCredentialObjects(unittest.TestCase):
    """
    This test will verify that the object created has good number of properties
    Will test that each property is correct datatype
    Will test that only Writable property can be written
    Will test that all properties can be read
    """
    def setUp(self):
        if _debug: Test_AccessCredentialObjects._debug("Test_AccessCredentialObjects")
        self.aco = AccessCredentialObject()
        self.identifiers, self.numOfProp = TestHelper.build_list_of_identifiers(self.aco.properties)
        self.numberOfPropertiesrequired = 25
        self.listOfProperties = \
        [ (WritableProperty,'globalIdentifier', Unsigned)
        , (ReadableProperty,'statusFlags', StatusFlags)
        , (ReadableProperty,'reliability', Reliability)
        , (ReadableProperty,'credentialStatus', BinaryPV)
        , (ReadableProperty,'reasonForDisable', SequenceOf(AccessCredentialDisableReason))
        , (ReadableProperty,'authenticationFactors', ArrayOf(CredentialAuthenticationFactor))
        , (ReadableProperty,'activationTime', DateTime)
        , (ReadableProperty,'expiryTime', DateTime)
        , (ReadableProperty,'credentialDisable', AccessCredentialDisable)
        , (OptionalProperty,'daysRemaining', Integer)
        , (OptionalProperty,'usesRemaining', Integer)
        , (OptionalProperty,'absenteeLimit', Unsigned)
        , (OptionalProperty,'belongsTo', DeviceObjectReference)
        , (ReadableProperty,'assignedAccessRights', ArrayOf(AssignedAccessRights))
        , (OptionalProperty,'lastAccessPoint', DeviceObjectReference)
        , (OptionalProperty,'lastAccessEvent', AccessEvent)
        , (OptionalProperty,'lastUseTime', DateTime)
        , (OptionalProperty,'traceFlag', Boolean)
        , (OptionalProperty,'threatAuthority', AccessThreatLevel)
        , (OptionalProperty,'extendedTimeEnable', Boolean)
        , (OptionalProperty,'authorizationExemptions', SequenceOf(AuthorizationException))
        , (OptionalProperty,'reliabilityEvaluationInhibit', Boolean)
        , (OptionalProperty,'masterExemption', Boolean)
        , (OptionalProperty,'passbackExemption', Boolean)
        , (OptionalProperty,'occupancyExemption', Boolean)]
        
    def test_object_AccessCredentialObject(self):
        if _debug: Test_AccessCredentialObjects._debug("test_object_AccessCredentialObject")
        assert str(self.aco.objectType) == 'accessCredential'
        
    def test_object_AccessCredentialObject_number_of_properties(self):
        if _debug: Test_AccessCredentialObjects._debug("test_object_AccessCredentialObject_number_of_properties")
        self.assertEqual(self.numOfProp,25)
        
    def test_object_AccessCredentialObject_property_identifiers(self):
        if _debug: Test_AccessCredentialObjects._debug("test_object_AccessCredentialObject_property_identifiers")
        for each in self.listOfProperties:
            assert each[1] in self.identifiers
            
    def test_object_AccessCredentialObject_property_dataType(self):
        if _debug: Test_AccessCredentialObjects._debug("test_object_AccessCredentialObject_property_dataType")
        for each in self.listOfProperties:
            assert self.aco.get_datatype(each[1]) == each[2]
            
    def test_object_AccessCredentialObject_noWritingToReadableProperty(self):
        if _debug: Test_AccessCredentialObjects._debug("test_object_AccessCredentialObject_noWritingToReadableProperty")
        with self.assertRaises(ExecutionError):
            for each in self.listOfProperties:
                if each[0] == ReadableProperty or each[0] == OptionalProperty:
                    self.aco.WriteProperty(each[1],0)
    
    def test_object_AccessCredentialObject_can_write_to_writableProperty(self):
        if _debug: Test_AccessCredentialObjects._debug("test_object_AccessCredentialObject_can_write_to_writableProperty")
        for each in self.listOfProperties:
            if each[0] == WritableProperty:
                self.aco.WriteProperty(each[1],0)
    
    def test_object_AccessCredentialObject_can_read_property(self):
        if _debug: Test_AccessCredentialObjects._debug("test_object_AccessCredentialObject_can_read_property")
        for each in self.listOfProperties:
            self.aco.ReadProperty(each[1])
    
                    
            
    