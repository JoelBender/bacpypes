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
class TestObjectHelper():
    def build_list_of_identifiers(self, properties):
        identifiers = []
        for each in properties:                        
            identifiers.append(each.identifier)
        return (identifiers)
        
    def object_type(self, obj, objType):
        if _debug: self._debug('test_object_%s' % obj.objectType)
        assert str(obj.objectType) == objType
        
    def object_number_of_properties(self, obj, required):
        if _debug: self._debug("test_object_%s_number_of_properties" % obj.objectType)
        self.assertEqual(len(self.identifiers),required)

        
    def object_property_identifiers(self, obj):
        if _debug: self._debug("test_object_%s_property_identifiers" % obj.objectType)
        for each in self.listOfProperties:
            assert each[1] in self.identifiers
            
    def object_property_dataType(self, obj):
        if _debug: self._debug("test_object_%s_property_dataType" % obj.objectType)
        for each in self.listOfProperties:
            assert obj.get_datatype(each[1]) == each[2]
            
    def object_noWritingToReadableProperty(self, obj, writeValue):
        if _debug: self._debug("test_object_%s_noWritingToReadableProperty" % obj.objectType)
        with self.assertRaises(ExecutionError):
            for each in self.listOfProperties:
                if each[0] == ReadableProperty or each[0] == OptionalProperty:
                    obj.WriteProperty(each[1],writeValue)
    
    def object_can_write_to_writableProperty(self, obj, writeValue):
        if _debug: self._debug("test_object_%s_can_write_to_writableProperty" % obj.objectType)
        for each in self.listOfProperties:
            if each[0] == WritableProperty:
                obj.WriteProperty(each[1],writeValue)
        assert True
    
    def object_can_read_property(self, obj):
        if _debug: self._debug("test_object_%s_can_read_property" % obj.objectType)
        for each in self.listOfProperties:
            obj.ReadProperty(each[1])
        assert True
