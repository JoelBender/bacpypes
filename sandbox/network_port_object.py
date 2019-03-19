
from bacpypes.object import Object, ReadableProperty, OptionalProperty

from bacpypes.primitivedata import Atomic, BitString, Boolean, CharacterString, Date, \
    Double, Integer, ObjectIdentifier, ObjectType, OctetString, Real, Time, \
    Unsigned, Tag, Enumerated, Null

from bacpypes.constructeddata import AnyAtomic, Array, ArrayOf, List, ListOf, \
    Choice, Element, Sequence

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


#
#   NEW PRIMITIVES
#

class Unsigned8(Unsigned):

    _app_tag = Tag.unsignedAppTag

    def __init__(self,arg = None):
        Unsigned.__init__(self, arg)
        self.value = 0

        if arg is None:
            pass
        elif isinstance(arg, Tag):
            self.decode(arg)
        elif isinstance(arg, int):
            if not self.is_valid(arg):
                raise ValueError("unsigned integer less than 256 required")
            self.value = arg
        elif isinstance(arg, Unsigned8):
            self.value = arg.value
        else:
            raise TypeError("invalid constructor datatype")


    @classmethod
    def is_valid(cls, arg):
        """Return True if arg is valid value for the class."""
        return Unsigned.is_valid(arg) and (0 <= arg <= 255)

    def __str__(self):
        return "%s(%s)" % (self.__class__.__name__, self.value)


class Unsigned16(Unsigned):

    _app_tag = Tag.unsignedAppTag

    def __init__(self,arg = None):
        Unsigned.__init__(self, arg)
        self.value = 0

        if arg is None:
            pass
        elif isinstance(arg, Tag):
            self.decode(arg)
        elif isinstance(arg, int):
            if not self.is_valid(arg):
                raise ValueError("unsigned integer less than 65536 required")
            self.value = arg
        elif isinstance(arg, Unsigned16):
            self.value = arg.value
        else:
            raise TypeError("invalid constructor datatype")


    @classmethod
    def is_valid(cls, arg):
        """Return True if arg is valid value for the class."""
        return Unsigned.is_valid(arg) and (0 <= arg <= 65535)

    def __str__(self):
        return "%s(%s)" % (self.__class__.__name__, self.value)

#
#   NEW BASETYPES
#

# Enumerations

class NetworkType(Enumerated):
    enumerations = \
        { 'ethernet':0
        , 'arcnet':1
        , 'mstp':2
        , 'ptp':3
        , 'lontalk':4
        , 'ipv4':5
        , 'zigbee':6
        , 'virtual': 7
        # , 'non-bacnet': 8  Removed in Version 1, Revision 18
        , 'ipv6':9
        , 'serial':10
        }

class ProtocolLevel(Enumerated):
    enumerations = \
        { 'physical':0
        , 'protocol':1
        , 'bacnetApplication':2
        , 'nonBacnetApplication':3
        }

class NetworkNumberQuality(Enumerated):
    enumerations = \
        { 'unknown':0
        , 'learned':1
        , 'learnedConfigured':2
        , 'configured':3
        }

class NetworkPortCommand(Enumerated):
    enumerations = \
        { 'idle':0
        , 'discardChanges':1
        , 'renewFdDRegistration':2
        , 'restartSlaveDiscovery':3
        , 'renewDHCP':4
        , 'restartAutonegotiation':5
        , 'disconnect':6
        , 'restartPort':7
        }

class IPMode(Enumerated):
    enumerations = \
        { 'normal':0
        , 'foreign':1
        , 'bbmd':2
        }

class RouterEntryStatus(Enumerated):
    # This was defined directly in the RouterEntry Sequence in the standard, but I moved it up here because
    # I didn't see anywhere else you defined something that way.
    enumerations = \
        { 'available':0
        , 'busy':1
        , 'disconnected':2
        }

# Choices

class HostAddress(Choice):
    choiceElements = \
        [ Element('none', Null)
        , Element('ipAddress', OctetString)  # 4 octets for B/IP or 16 octets for B/IPv6
        , Element('name', CharacterString)  # Internet host name (see RFC 1123)
        ]

# Sequences

class HostNPort(Sequence):
    sequenceElements = \
        [ Element('host', HostAddress)
        , Element('port', Unsigned16)
        ]

class BDTEntry(Sequence):
    sequenceElements = \
        [ Element('bbmdAddress', HostNPort)
        , Element('broadcastMask', OctetString)  # shall be present if BACnet/IP, and absent for BACnet/IPv6
        ]

class FDTEntry(Sequence):
    sequenceElements = \
        [ Element('bacnetIPAddress', OctetString)  # the 6-octet B/IP or 18-octet B/IPv6 address of the registrant
        , Element('timeToLive', Unsigned16)  # time to live in seconds at the time of registration
        , Element('remainingTimeToLive', Unsigned16)  # remaining time to live in seconds, incl. grace period
        ]

class VMACEntry(Sequence):
    sequenceElements = \
        [ Element('virtualMACAddress', OctetString)  # maximum size 6 octets
        , Element('nativeMACAddress', OctetString)
        ]

class RouterEntry(Sequence):
    sequenceElements = \
        [ Element('networkNumber', Unsigned16)
        , Element('macAddress', OctetString)
        , Element('status', RouterEntryStatus)  # Defined Above
        ]

class NameValue(Sequence):
    sequenceElements = \
        [ Element('name', CharacterString)
        , Element('value', Atomic)  # IS ATOMIC CORRECT HERE? value is limited to primitive datatypes and BACnetDateTime
        ]

#
#   NEW OBJECT
#

class NetworkPortObject(Object):
    objectType = 'NetworkPort'
    properties = \
        [ ReadableProperty('statusFlags', StatusFlags)
        , ReadableProperty('reliability', Reliability)
        , ReadableProperty('outOfService', Boolean)
        , ReadableProperty('networkType', NetworkType)
        , ReadableProperty('protocolLevel', ProtocolLevel)
        , OptionalProperty('referencePort', Unsigned)
        , ReadableProperty('networkNumber', Unsigned16)
        , ReadableProperty('networkNumberQuality', NetworkNumberQuality)
        , ReadableProperty('changesPending', Boolean)
        , OptionalProperty('command', NetworkPortCommand)
        , OptionalProperty('macAddress', OctetString)
        , ReadableProperty('apduLength', Unsigned)
        , ReadableProperty('linkSpeed', Real)
        , OptionalProperty('linkSpeeds', ArrayOf(Real))
        , OptionalProperty('eventTimeStamps', ArrayOf(TimeStamp))
        , OptionalProperty('linkSpeedAutonegotiate', Boolean)
        , OptionalProperty('networkInterfaceName', CharacterString)
        , OptionalProperty('ipMode', IPMode)
        , OptionalProperty('ipAddress', OctetString)
        , OptionalProperty('ipUDPPort', Unsigned16)
        , OptionalProperty('ipSubnetMask', OctetString)
        , OptionalProperty('ipDefaultGateway', OctetString)
        , OptionalProperty('ipMulticastAddress', OctetString)
        , OptionalProperty('ipDNSServer', ArrayOf(OctetString))
        , OptionalProperty('ipDHCPEnable', Boolean)
        , OptionalProperty('ipDHCPLeaseTime', Unsigned)
        , OptionalProperty('ipDHCPLeaseTimeRemaining', Unsigned)
        , OptionalProperty('ipDHCPServer', OctetString)
        , OptionalProperty('ipNATTraversal', Boolean)
        , OptionalProperty('ipGlobalAddress', HostNPort)
        , OptionalProperty('broadcastDistributionTable', ListOf(BDTEntry))
        , OptionalProperty('acceptFDRegistrations', Boolean)
        , OptionalProperty('foreignDeviceTable', ListOf(FDTEntry))
        , OptionalProperty('fdBBMDAddress', HostNPort)
        , OptionalProperty('fdSubscriptionLifetime', Unsigned16)
        , OptionalProperty('ipv6Mode', IPMode)
        , OptionalProperty('ipv6Address', OctetString)
        , OptionalProperty('ipv6PrefixLength', Unsigned8)
        , OptionalProperty('ipv6UDPPort', Unsigned16)
        , OptionalProperty('ipv6DefaultGateway', OctetString)
        , OptionalProperty('ipv6MulticastAddress', OctetString)
        , OptionalProperty('ipv6DNSServer', OctetString)
        , OptionalProperty('ipv6AutoAddressingEnabled', Boolean)
        , OptionalProperty('ipv6DHCPLeaseTime', Unsigned)
        , OptionalProperty('ipv6DHCPLeaseTimeRemaining', Unsigned)
        , OptionalProperty('ipv6DHCPServer', OctetString)
        , OptionalProperty('ipv6ZoneIndex', CharacterString)
        , OptionalProperty('maxMasters', Unsigned8) # range 0-127
        , OptionalProperty('maxInfoFrames', Unsigned8)
        , OptionalProperty('slaveProxyEnable', Boolean)
        , OptionalProperty('manualSlaveAddressBinding', ListOf(AddressBinding))
        , OptionalProperty('autoSlaveDiscovery', Boolean)
        , OptionalProperty('slaveAddressBinding', ListOf(AddressBinding))
        , OptionalProperty('virtualMACAddressTable', ListOf(VMACEntry))
        , OptionalProperty('routingTable', ListOf(RouterEntry))
        , OptionalProperty('eventDetectionEnabled', Boolean)
        , OptionalProperty('notificationClass', Unsigned)
        , OptionalProperty('eventEnable', EventTransitionBits)
        , OptionalProperty('ackedTransitions', EventTransitionBits)
        , OptionalProperty('notifyType', NotifyType)
        , OptionalProperty('eventTimeStamps', ArrayOf(TimeStamp, 3))
        , OptionalProperty('eventMessageTexts', ArrayOf(CharacterString, 3))
        , OptionalProperty('eventMessageTextsConfig', ArrayOf(CharacterString, 3))
        , OptionalProperty('eventState', EventState)
        , ReadableProperty('reliabilityEvaluationInhibit', Boolean)
        , OptionalProperty('propertyList', ArrayOf(PropertyIdentifier))
        , OptionalProperty('tags', ArrayOf(NameValue))
        , OptionalProperty('profileLocation', CharacterString)
        , OptionalProperty('profileName', CharacterString)
        ]
