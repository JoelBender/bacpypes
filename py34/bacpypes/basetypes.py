#!/usr/bin/python

"""
Base Types
"""

from .debugging import bacpypes_debugging, ModuleLogger
from .errors import MissingRequiredParameter

from .primitivedata import Atomic, BitString, Boolean, CharacterString, Date, Double, \
    Enumerated, Integer, Null, ObjectType, ObjectIdentifier, OctetString, Real, Time, \
    Unsigned, Unsigned8, Unsigned16, Tag
from .constructeddata import Any, AnyAtomic, ArrayOf, Choice, Element, \
    Sequence, SequenceOf

# some debugging
_debug = 0
_log = ModuleLogger(globals())

#
#   Bit Strings
#

class AuditOperationFlags(BitString):
    vendor_range = (32, 63)
    bitNames = \
        { 'read':0
        , 'write':1
        , 'create':2
        , 'delete':3
        , 'lifeSafety':4
        , 'acknowledgeAlarm':5
        , 'deviceDisableComm':6
        , 'deviceEnableComm':7
        , 'deviceReset':8
        , 'deviceBackup':9
        , 'deviceRestore':10
        , 'subscription':11
        , 'notification':12
        , 'auditingFailure':13
        , 'networkChanges':14
        , 'general':15
        }
    bitLen = 16

class DaysOfWeek(BitString):
    bitNames = \
        { 'monday':0
        , 'tuesday':1
        , 'wednesday':2
        , 'thursday':3
        , 'friday':4
        , 'saturday':5
        , 'sunday':6
        }
    bitLen = 7

class EventTransitionBits(BitString):
    bitNames = \
        { 'toOffnormal':0
        , 'toFault':1
        , 'toNormal':2
        }
    bitLen = 3

class LimitEnable(BitString):
    bitNames = \
        { 'lowLimitEnable':0
        , 'highLimitEnable':1
        }
    bitLen = 2

class LogStatus(BitString):
    bitNames = \
        { 'logDisabled':0
        , 'bufferPurged':1
        , 'logInterrupted':2
        }
    bitLen = 3

class ObjectTypesSupported(BitString):
    bitNames = \
        { 'analogInput':0
        , 'analogOutput':1
        , 'analogValue':2
        , 'binaryInput':3
        , 'binaryOutput':4
        , 'binaryValue':5
        , 'calendar':6
        , 'command':7
        , 'device':8
        , 'eventEnrollment':9
        , 'file':10
        , 'group':11
        , 'loop':12
        , 'multiStateInput':13
        , 'multiStateOutput':14
        , 'notificationClass':15
        , 'program':16
        , 'schedule':17
        , 'averaging':18
        , 'multiStateValue':19
        , 'trendLog':20
        , 'lifeSafetyPoint':21
        , 'lifeSafetyZone':22
        , 'accumulator':23
        , 'pulseConverter':24
        , 'eventLog':25
        , 'globalGroup':26
        , 'trendLogMultiple':27
        , 'loadControl':28
        , 'structuredView':29
        , 'accessDoor':30
        , 'accessCredential':32
        , 'accessPoint':33
        , 'accessRights':34
        , 'accessUser':35
        , 'accessZone':36
        , 'credentialDataInput':37
        , 'networkSecurity':38 # removed revision 22
        , 'bitstringValue':39
        , 'characterstringValue':40
        , 'datePatternValue':41
        , 'dateValue':42
        , 'datetimePatternValue':43
        , 'datetimeValue':44
        , 'integerValue':45
        , 'largeAnalogValue':46
        , 'octetstringValue':47
        , 'positiveIntegerValue':48
        , 'timePatternValue':49
        , 'timeValue':50
        , 'notificationForwarder':51
        , 'alertEnrollment':52
        , 'channel':53
        , 'lightingOutput':54
        , 'binaryLightingOutput':55
        , 'networkPort':56
        , 'elevatorGroup':57
        , 'escalator':58
        , 'lift':59
        , 'staging':60
        , 'auditLog':61
        , 'auditReporter':62
        }
    bitLen = 63

class PriorityFilter(BitString):
    bitNames = \
        { 'manualLifeSafety':0
        , 'automaticLifeSafety':1
        , 'priority3':2
        , 'priority4':3
        , 'criticalEquipmentControls':4
        , 'minimumOnOff':5
        , 'priority7':6
        , 'manualOperator':7
        , 'priority9':8
        , 'priority10':9
        , 'priority11':10
        , 'priority12':11
        , 'priority13':12
        , 'priority14':13
        , 'priority15':14
        , 'priority16':15
        }
    bitLen = 16

class ResultFlags(BitString):
    bitNames = \
        { 'firstItem':0
        , 'lastItem':1
        , 'moreItems':2
        }
    bitLen = 3

class ServicesSupported(BitString):
    bitNames = \
        { 'acknowledgeAlarm':0
        , 'confirmedCOVNotification':1
        , 'confirmedEventNotification':2
        , 'getAlarmSummary':3
        , 'getEnrollmentSummary':4
        , 'subscribeCOV':5
        , 'atomicReadFile':6
        , 'atomicWriteFile':7
        , 'addListElement':8
        , 'removeListElement':9
        , 'createObject':10
        , 'deleteObject':11
        , 'readProperty':12
      # , 'readPropertyConditional':13      # removed in version 1 revision 12
        , 'readPropertyMultiple':14
        , 'writeProperty':15
        , 'writePropertyMultiple':16
        , 'deviceCommunicationControl':17
        , 'confirmedPrivateTransfer':18
        , 'confirmedTextMessage':19
        , 'reinitializeDevice':20
        , 'vtOpen':21
        , 'vtClose':22
        , 'vtData':23
      # , 'authenticate':24                 # removed in version 1 revision 11
      # , 'requestKey':25                   # removed in version 1 revision 11
        , 'iAm':26
        , 'iHave':27
        , 'unconfirmedCOVNotification':28
        , 'unconfirmedEventNotification':29
        , 'unconfirmedPrivateTransfer':30
        , 'unconfirmedTextMessage':31
        , 'timeSynchronization':32
        , 'whoHas':33
        , 'whoIs':34
        , 'readRange':35
        , 'utcTimeSynchronization':36
        , 'lifeSafetyOperation':37
        , 'subscribeCOVProperty':38
        , 'getEventInformation':39
        , 'writeGroup':40
        , 'subscribeCOVPropertyMultiple':41
        , 'confirmedCOVNotificationMultiple':42
        , 'unconfirmedCOVNotificationMultiple':43
        , 'confirmedAuditNotification':44
        , 'auditLogQuery':45
        , 'unconfirmedAuditNotification':46
        , 'whoAmI':47
        , 'youAre':48
        }
    bitLen = 49

class StatusFlags(BitString):
    bitNames = \
        { 'inAlarm':0
        , 'fault':1
        , 'overridden':2
        , 'outOfService':3
        }
    bitLen = 4

#
#   Enumerations
#

class AccessAuthenticationFactorDisable(Enumerated):
    vendor_range = (64, 65535)
    enumerations = \
        { 'none':0
        , 'disabled':1
        , 'disabledLost':2
        , 'disabledStolen':3
        , 'disabledDamaged':4
        , 'disabledDestroyed':5
        }

class AccessCredentialDisable(Enumerated):
    vendor_range = (64, 65535)
    enumerations = \
        { 'none':0
        , 'disable':1
        , 'disableManual':2
        , 'disableLockout':3
        }

class AccessCredentialDisableReason(Enumerated):
    enumerations = \
        { 'disabled':0
        , 'disabledNeedsProvisioning':1
        , 'disabledUnassigned':2
        , 'disabledNotYetActive':3
        , 'disabledExpired':4
        , 'disabledLockout':5
        , 'disabledMaxDays':6
        , 'disabledMaxUses':7
        , 'disabledInactivity':8
        , 'disabledManual':9
        }

class AccessEvent(Enumerated):
    vendor_range = (512, 65535)
    enumerations = \
        { 'none':0
        , 'granted':1
        , 'muster':2
        , 'passbackDetected':3
        , 'duress':4
        , 'trace':5
        , 'lockoutMaxAttempts':6
        , 'lockoutOther':7
        , 'lockoutRelinquished':8
        , 'lockedByHigherPriority':9
        , 'outOfService':10
        , 'outOfServiceRelinquished':11
        , 'accompanimentBy':12
        , 'authenticationFactorRead':13
        , 'authorizationDelayed':14
        , 'verificationRequired':15
        , 'deniedDenyAll':128
        , 'deniedUnknownCredential':129
        , 'deniedAuthenticationUnavailable':130
        , 'deniedAuthenticationFactorTimeout':131
        , 'deniedIncorrectAuthenticationFactor':132
        , 'deniedZoneNoAccessRights':133
        , 'deniedPointNoAccessRights':134
        , 'deniedNoAccessRights':135
        , 'deniedOutOfTimeRange':136
        , 'deniedThreatLevel':137
        , 'deniedPassback':138
        , 'deniedUnexpectedLocationUsage':139
        , 'deniedMaxAttempts':140
        , 'deniedLowerOccupancyLimit':141
        , 'deniedUpperOccupancyLimit':142
        , 'deniedAuthenticationFactorLost':143
        , 'deniedAuthenticationFactorStolen':144
        , 'deniedAuthenticationFactorDamaged':145
        , 'deniedAuthenticationFactorDestroyed':146
        , 'deniedAuthenticationFactorDisabled':147
        , 'deniedAuthenticationFactorError':148
        , 'deniedCredentialUnassigned':149
        , 'deniedCredentialNotProvisioned':150
        , 'deniedCredentialNotYetActive':151
        , 'deniedCredentialExpired':152
        , 'deniedCredentialManualDisable':153
        , 'deniedCredentialLockout':154
        , 'deniedCredentialMaxDays':155
        , 'deniedCredentialMaxUses':156
        , 'deniedCredentialInactivity':157
        , 'deniedCredentialDisabled':158
        , 'deniedNoAccompaniment':159
        , 'deniedIncorrectAccompaniment':160
        , 'deniedLockout':161
        , 'deniedVerificationFailed':162
        , 'deniedVerificationTimeout':163
        , 'deniedOther':164
        }

class AccessPassbackMode(Enumerated):
    enumerations = \
        { 'passbackOff':0
        , 'hardPassback':1
        , 'softPassback':2
        }

class AccessRuleTimeRangeSpecifier(Enumerated):
    enumerations = \
        { 'specified':0
        , 'always':1
        }

class AccessRuleLocationSpecifier(Enumerated):
    enumerations = \
        { 'specified':0
        , 'all':1
        }

class AccessUserType(Enumerated):
    vendor_range = (64, 65535)
    enumerations = \
        { 'asset':0
        , 'group':1
        , 'person':2
        }

class AccessZoneOccupancyState(Enumerated):
    vendor_range = (64, 65535)
    enumerations = \
        { 'normal':0
        , 'belowLowerLimit':1
        , 'atLowerLimit':2
        , 'atUpperLimit':3
        , 'aboveUpperLimit':4
        , 'disabled':5
        , 'notSupported':6
        }

class AccumulatorRecordAccumulatorStatus(Enumerated):
    enumerations = \
        { 'normal':0
        , 'starting':1
        , 'recovered':2
        , 'abnormal':3
        , 'failed':4
        }

class Action(Enumerated):
    enumerations = \
        { 'direct':0
        , 'reverse':1
        }

class AuditLevel(Enumerated):
    vendor_range = (128, 255)
    enumerations = \
        { 'none':0
        , 'auditAll':1
        , 'auditConfig':2
        , 'default':3
        }

class AuditOperation(Enumerated):
    vendor_range = (32, 63)
    enumerations = \
        { 'read':0
        , 'write':1
        , 'create':2
        , 'delete':3
        , 'lifeSafety':4
        , 'acknowledgeAlarm':5
        , 'deviceDisableComm':6
        , 'deviceEnableComm':7
        , 'deviceReset':8
        , 'deviceBackup':9
        , 'deviceRestore':10
        , 'subscription':11
        , 'notification':12
        , 'auditingFailure':13
        , 'networkChanges':14
        , 'general':15
        }

class AuthenticationFactorType(Enumerated):
    enumerations = \
        { 'undefined':0
        , 'error':1
        , 'custom':2
        , 'simpleNumber16':3
        , 'simpleNumber32':4
        , 'simpleNumber56':5
        , 'simpleAlphaNumeric':6
        , 'abaTrack2':7
        , 'wiegand26':8
        , 'wiegand37':9
        , 'wiegand37facility':10
        , 'facility16card32':11
        , 'facility32card32':12
        , 'fascN':13
        , 'fascNbcd':14
        , 'fascNlarge':15
        , 'fascNlargeBcd':16
        , 'gsa75':17
        , 'chuid':18
        , 'chuidFull':19
        , 'guid':20
        , 'cbeffA':21
        , 'cbeffB':22
        , 'cbeffC':23
        , 'userPassword':24
        }

class AuthenticationStatus(Enumerated):
    enumerations = \
        { 'notReady':0
        , 'ready':1
        , 'disabled':2
        , 'waitingForAuthenticationFactor':3
        , 'waitingForAccompaniment':4
        , 'waitingForVerification':5
        , 'inProgress':6
        }

class AuthorizationException(Enumerated):
    vendor_range = (64, 255)
    enumerations = \
        { 'passback':0
        , 'occupancyCheck':1
        , 'accessRights':2
        , 'lockout':3
        , 'deny':4
        , 'verification':5
        , 'authorizationDelay':6
        }

class AuthorizationMode(Enumerated):
    vendor_range = (64, 65536)
    enumerations = \
        { 'authorize':0
        , 'grantActive':1
        , 'denyAll':2
        , 'verificationRequired':3
        , 'authorizationDelayed':4
        , 'none':5
        }

class BackupState(Enumerated):
    enumerations = \
        { 'idle':0
        , 'preparingForBackup':1
        , 'preparingForRestore':2
        , 'performingABackup':3
        , 'performingARestore':4
        , 'backupFailure':5
        , 'restoreFailure':6
        }

class BinaryLightingPV(Enumerated):
    vendor_range = (64, 255)
    enumerations = \
        { 'off':0
        , 'on':1
        , 'warn':2
        , 'warnOff':3
        , 'warnRelinquish':4
        , 'stop':5
        }

class BinaryPV(Enumerated):
    enumerations = \
        { 'inactive':0
        , 'active':1
        }

class DeviceStatus(Enumerated):
    vendor_range = (64, 65535)
    enumerations = \
        { 'operational':0
        , 'operationalReadOnly':1
        , 'downloadRequired':2
        , 'downloadInProgress':3
        , 'nonOperational':4
        , 'backupInProgress':5
        }

class DoorAlarmState(Enumerated):
    vendor_range = (256, 65535)
    enumerations = \
        { 'normal':0
        , 'alarm':1
        , 'doorOpenTooLong':2
        , 'forcedOpen':3
        , 'tamper':4
        , 'doorFault':5
        , 'lockDown':6
        , 'freeAccess':7
        , 'egressOpen':8
        }

class DoorSecuredStatus(Enumerated):
    enumerations = \
        { 'secured':0
        , 'unsecured':1
        , 'unknown':2
        }

class DoorStatus(Enumerated):
    enumerations = \
        { 'closed':0
        , 'opened':1
        , 'unknown':2
        }

class DoorValue(Enumerated):
    enumerations = \
        { 'lock':0
        , 'unlock':1
        , 'pulseUnlock':2
        , 'extendedPulseUnlock':3
        }

class EngineeringUnits(Enumerated):
    vendor_range = (256, 65535)
    enumerations = \
        {
        #Acceleration
          'metersPerSecondPerSecond':166
        , 'squareMeters':0
        , 'squareCentimeters':116
        , 'squareFeet':1
        , 'squareInches':115
        #Currency
        , 'currency1':105
        , 'currency2':106
        , 'currency3':107
        , 'currency4':108
        , 'currency5':109
        , 'currency6':110
        , 'currency7':111
        , 'currency8':112
        , 'currency9':113
        , 'currency10':114
        #Electrical
        , 'milliamperes':2
        , 'amperes':3
        , 'amperesPerMeter':167
        , 'amperesPerSquareMeter':168
        , 'ampereSquareMeters':169
        , 'decibels':199
        , 'decibelsMillivolt':200
        , 'decibelsVolt':201
        , 'farads':170
        , 'henrys':171
        , 'ohms':4
        , 'ohmMeters':172
        , 'ohmMeterPerSquareMeter':237
        , 'milliohms':145
        , 'kilohms':122
        , 'megohms':123
        , 'microSiemens':190
        , 'millisiemens':202
        , 'siemens':173
        , 'siemensPerMeter':174
        , 'teslas':175
        , 'volts':5
        , 'millivolts':124
        , 'kilovolts':6
        , 'megavolts':7
        , 'voltAmperes':8
        , 'kilovoltAmperes':9
        , 'megavoltAmperes':10
        , 'ampereSeconds':238
        , 'ampereSquareHours':246
        , 'voltAmpereHours':239 #VAh
        , 'kilovoltAmpereHours':240 #kVAh
        , 'megavoltAmpereHours':241 #MVAh
        , 'voltAmperesReactive':11
        , 'kilovoltAmperesReactive':12
        , 'megavoltAmperesReactive':13
        , 'voltAmpereHoursReactive':242 #varh
        , 'kilovoltAmpereHoursReactive':243 #kvarh
        , 'megavoltAmpereHoursReactive':244 #Mvarh
        , 'voltsPerDegreeKelvin':176
        , 'voltsPerMeter':177
        , 'voltsSquareHours':245
        , 'degreesPhase':14
        , 'powerFactor':15
        , 'webers':178
        # Energy
        , 'joules':16
        , 'kilojoules':17
        , 'kilojoulesPerKilogram':125
        , 'megajoules':126
        , 'joulesPerHours':247
        , 'wattHours':18
        , 'kilowattHours':19
        , 'megawattHours':146
        , 'wattHoursReactive':203
        , 'kilowattHoursReactive':204
        , 'megawattHoursReactive':205
        , 'btus':20
        , 'kiloBtus':147
        , 'megaBtus':148
        , 'therms':21
        , 'tonHours':22
        # Enthalpy
        , 'joulesPerKilogramDryAir':23
        , 'kilojoulesPerKilogramDryAir':149
        , 'megajoulesPerKilogramDryAir':150
        , 'btusPerPoundDryAir':24
        , 'btusPerPound':117
        , 'joulesPerDegreeKelvin':127
        # Entropy
        , 'kilojoulesPerDegreeKelvin':151
        , 'megajoulesPerDegreeKelvin':152
        , 'joulesPerKilogramDegreeKelvin':128
        # Force
        , 'newton':153
        # Frequency
        , 'cyclesPerHour':25
        , 'cyclesPerMinute':26
        , 'hertz':27
        , 'kilohertz':129
        , 'megahertz':130
        , 'perHour':131
        , 'gramsOfWaterPerKilogramDryAir':28
        , 'percentRelativeHumidity':29
        , 'micrometers':194
        , 'millimeters':30
        , 'centimeters':118
        , 'kilometers':193
        , 'meters':31
        , 'inches':32
        , 'feet':33
        , 'candelas':179
        , 'candelasPerSquareMeter':180
        , 'wattsPerSquareFoot':34
        , 'wattsPerSquareMeter':35
        , 'lumens':36
        , 'luxes':37
        , 'footCandles':38
        , 'milligrams':196
        , 'grams':195
        , 'kilograms':39
        , 'poundsMass':40
        , 'tons':41
        , 'gramsPerSecond':154
        , 'gramsPerMinute':155
        , 'kilogramsPerSecond':42
        , 'kilogramsPerMinute':43
        , 'kilogramsPerHour':44
        , 'poundsMassPerSecond':119
        , 'poundsMassPerMinute':45
        , 'poundsMassPerHour':46
        , 'tonsPerHour':156
        , 'milliwatts':132
        , 'watts':47
        , 'kilowatts':48
        , 'megawatts':49
        , 'btusPerHour':50
        , 'kiloBtusPerHour':157
        , 'horsepower':51
        , 'tonsRefrigeration':52
        , 'pascals':53
        , 'hectopascals':133
        , 'kilopascals':54
        , 'pascalSeconds':253
        , 'millibars':134
        , 'bars':55
        , 'poundsForcePerSquareInch':56
        , 'millimetersOfWater':206
        , 'centimetersOfWater':57
        , 'inchesOfWater':58
        , 'millimetersOfMercury':59
        , 'centimetersOfMercury':60
        , 'inchesOfMercury':61
        , 'degreesCelsius':62
        , 'degreesKelvin':63
        , 'degreesKelvinPerHour':181
        , 'degreesKelvinPerMinute':182
        , 'degreesFahrenheit':64
        , 'degreeDaysCelsius':65
        , 'degreeDaysFahrenheit':66
        , 'deltaDegreesFahrenheit':120
        , 'deltaDegreesKelvin':121
        , 'years':67
        , 'months':68
        , 'weeks':69
        , 'days':70
        , 'hours':71
        , 'minutes':72
        , 'seconds':73
        , 'hundredthsSeconds':158
        , 'milliseconds':159
        , 'newtonMeters':160
        , 'millimetersPerSecond':161
        , 'millimetersPerMinute':162
        , 'metersPerSecond':74
        , 'metersPerMinute':163
        , 'metersPerHour':164
        , 'kilometersPerHour':75
        , 'feetPerSecond':76
        , 'feetPerMinute':77
        , 'milesPerHour':78
        , 'cubicFeet':79
        , 'cubicFeetPerDay':248
        , 'cubicMeters':80
        , 'cubicMetersPerDay':249
        , 'imperialGallons':81
        , 'milliliters':197
        , 'liters':82
        , 'usGallons':83
        , 'cubicFeetPerSecond':142
        , 'cubicFeetPerMinute':84
        , 'cubicFeetPerHour':191
        , 'cubicMetersPerSecond':85
        , 'cubicMetersPerMinute':165
        , 'cubicMetersPerHour':135
        , 'imperialGallonsPerMinute':86
        , 'millilitersPerSecond':198
        , 'litersPerSecond':87
        , 'litersPerMinute':88
        , 'litersPerHour':136
        , 'usGallonsPerMinute':89
        , 'usGallonsPerHour':192
        , 'degreesAngular':90
        , 'degreesCelsiusPerHour':91
        , 'degreesCelsiusPerMinute':92
        , 'degreesFahrenheitPerHour':93
        , 'degreesFahrenheitPerMinute':94
        , 'jouleSeconds':183
        , 'kilogramsPerCubicMeter':186
        , 'kilowattHoursPerSquareMeter':137
        , 'kilowattHoursPerSquareFoot':138
        , 'megajoulesPerSquareMeter':139
        , 'megajoulesPerSquareFoot':140
        , 'noUnits':95
        , 'newtonSeconds':187
        , 'newtonsPerMeter':188
        , 'partsPerMillion':96
        , 'partsPerBillion':97
        , 'percent':98
        , 'percentObscurationPerFoot':143
        , 'percentObscurationPerMeter':144
        , 'percentPerSecond':99
        , 'perMinute':100
        , 'perSecond':101
        , 'psiPerDegreeFahrenheit':102
        , 'radians':103
        , 'radiansPerSecond':184
        , 'revolutionsPerMinute':104
        , 'squareMetersPerNewton':185
        , 'wattsPerMeterPerDegreeKelvin':189
        , 'wattsPerSquareMeterDegreeKelvin':141
        , 'perMille':207
        , 'gramsPerGram':208
        , 'kilogramsPerKilogram':209
        , 'gramsPerKilogram':210
        , 'milligramsPerGram':211
        , 'milligramsPerKilogram':212
        , 'gramsPerMilliliter':213
        , 'gramsPerLiter':214
        , 'milligramsPerLiter':215
        , 'microgramsPerLiter':216
        , 'gramsPerCubicMeter':217
        , 'milligramsPerCubicMeter':218
        , 'microgramsPerCubicMeter':219
        , 'nanogramsPerCubicMeter':220
        , 'gramsPerCubicCentimeter':221
        , 'wattHoursPerCubicMeter':250
        , 'joulesPerCubicMeter':251
        , 'becquerels':222
        , 'kilobecquerels':223
        , 'megabecquerels':224
        , 'gray':225
        , 'milligray':226
        , 'microgray':227
        , 'sieverts':228
        , 'millisieverts':229
        , 'microsieverts':230
        , 'microsievertsPerHour':231
        , 'decibelsA':232
        , 'nephelometricTurbidityUnit':233
        , 'pH':234
        , 'gramsPerSquareMeter':235
        , 'minutesPerDegreeKelvin':236
        }

class ErrorClass(Enumerated):
    enumerations = \
        { 'device':0
        , 'object':1
        , 'property':2
        , 'resources':3
        , 'security':4
        , 'services':5
        , 'vt':6
        , 'communication':7
        }

class ErrorCode(Enumerated):
    enumerations = \
        { 'abortApduTooLong':123
        , 'abortApplicationExceededReplyTime':124
        , 'abortBufferOverflow':51
        , 'abortInsufficientSecurity':135
        , 'abortInvalidApduInThisState':52
        , 'abortOther':56
        , 'abortOutOfResources':125
        , 'abortPreemptedByHigherPriorityTask':53
        , 'abortProprietary':55
        , 'abortSecurityError':136
        , 'abortSegmentationNotSupported':54
        , 'abortProprietary':55
        , 'abortOther':56
        , 'abortTsmTimeout':126
        , 'abortWindowSizeOutOfRange':127
        , 'accessDenied':85
        , 'addressingError':115
        , 'badDestinationAddress':86
        , 'badDestinationDeviceId':87
        , 'badSignature':88
        , 'badSourceAddress':89
        , 'badTimestamp':90 #Removed revision 22
        , 'busy':82
        , 'bvlcFunctionUnknown':143
        , 'bvlcProprietaryFunctionUnknown':144
        , 'cannotUseKey':91 #Removed revision 22
        , 'cannotVerifyMessageId':92 #Removed revision 22
        , 'characterSetNotSupported':41
        , 'communicationDisabled':83
        , 'configurationInProgress':2
        , 'correctKeyRevision':93 #Removed revision 22
        , 'covSubscriptionFailed':43
        , 'datatypeNotSupported':47
        , 'deleteFdtEntryFailed':120
        , 'deviceBusy':3
        , 'destinationDeviceIdRequired':94 #Removed revision 22
        , 'distributeBroadcastFailed':121
        , 'dnsError':192
        , 'dnsNameResolutionFailed':190
        , 'dnsResolverFailure':191
        , 'dnsUnavailable':189
        , 'duplicateEntry': 137
        , 'duplicateMessage':95
        , 'duplicateName':48
        , 'duplicateObjectId':49
        , 'dynamicCreationNotSupported':4
        , 'encryptionNotConfigured':96
        , 'encryptionRequired':97
        , 'fileAccessDenied':5
        , 'fileFull':128
        , 'headerEncodingError':145
        , 'headerNotUnderstood':146
        , 'httpError':165
        , 'httpNoUpgrade':153
        , 'httpNotAServer':164
        , 'httpResourceNotLocal':154
        , 'httpProxyAuthenticationFailed':155
        , 'httpResponseTimeout':156
        , 'httpResponseSyntaxError':157
        , 'httpResponseValueError':158
        , 'httpResponseMissingHeader':159
        , 'httpTemporaryUnavailable':163
        , 'httpUnexpectedResponseCode':152
        , 'httpUpgradeRequired':161
        , 'httpUpgradeError':162
        , 'httpWebsocketHeaderError':160
        , 'inconsistentConfiguration':129
        , 'inconsistentObjectType':130
        , 'inconsistentParameters':7
        , 'inconsistentSelectionCriterion':8
        , 'incorrectKey':98 #Removed revision 22
        , 'internalError':131
        , 'invalidArrayIndex':42
        , 'invalidConfigurationData':46
        , 'invalidDataEncoding':142
        , 'invalidDataType':9
        , 'invalidEventState':73
        , 'invalidFileAccessMethod':10
        , 'invalidFileStartPosition':11
        , 'invalidKeyData':99 #Removed revision 22
        , 'invalidParameterDataType':13
        , 'invalidTag':57
        , 'invalidTimeStamp':14
        , 'invalidValueInThisState':138
        , 'ipAddressNotReachable':198
        , 'ipError':199
        , 'keyUpdateInProgress':100 #Removed revision 22
        , 'listElementNotFound':81
        , 'listItemNotNumbered':140
        , 'listItemNotTimestamped': 141
        , 'logBufferFull':75
        , 'loggedValuePurged':76
        , 'malformedMessage':101
        , 'messageTooLong':113
        , 'messageIncomplete':147
        , 'missingRequiredParameter':16
        , 'networkDown':58
        , 'noAlarmConfigured':74
        , 'noObjectsOfSpecifiedType':17
        , 'noPropertySpecified':77
        , 'noSpaceForObject':18
        , 'noSpaceToAddListElement':19
        , 'noSpaceToWriteProperty':20
        , 'noVtSessionsAvailable':21
        , 'nodeDuplicateVmac':151
        , 'notABacnetScHub':148
        , 'notConfigured':132
        , 'notConfiguredForTriggeredLogging':78
        , 'notCovProperty':44
        , 'notKeyServer':102 #Removed revision 22
        , 'notRouterToDnet':110
        , 'objectDeletionNotPermitted':23
        , 'objectIdentifierAlreadyExists':24
        , 'other':0
        , 'operationalProblem':25
        , 'optionalFunctionalityNotSupported':45
        , 'outOfMemory':133
        , 'parameterOutOfRange':80
        , 'passwordFailure':26
        , 'payloadExpected':149
        , 'propertyIsNotAList':22
        , 'propertyIsNotAnArray':50
        , 'readAccessDenied':27
        , 'readBdtFailed':117
        , 'readFdtFailed':119
        , 'registerForeignDeviceFailed':118
        , 'rejectBufferOverflow':59
        , 'rejectInconsistentParameters':60
        , 'rejectInvalidParameterDataType':61
        , 'rejectInvalidTag':62
        , 'rejectMissingRequiredParameter':63
        , 'rejectParameterOutOfRange':64
        , 'rejectTooManyArguments':65
        , 'rejectUndefinedEnumeration':66
        , 'rejectUnrecognizedService':67
        , 'rejectProprietary':68
        , 'rejectOther':69
        , 'routerBusy':111
        , 'securityError':114
        , 'securityNotConfigured':103
        , 'serviceRequestDenied':29
        , 'sourceSecurityRequired':104
        , 'success':84
        , 'tcpClosedByLocal':195
        , 'tcpClosedOther':196
        , 'tcpConnectTimeout':193
        , 'tcpConnectionRefused':194
        , 'tcpError':197
        , 'timeout':30
        , 'tlsClientAuthenticationFailed':182
        , 'tlsClientCertificateError':180
        , 'tlsClientCertificateExpired':184
        , 'tlsClientCertificateRevoked':186
        , 'tleError':188
        , 'tlsServerAuthenticationFailed':183
        , 'tlsServerCertificateError':181
        , 'tlsServerCertificateExpired':185
        , 'tlsServerCertificateRevoked':187
        , 'tooManyKeys':105 #Removed revision 22
        , 'unexpectedData':150
        , 'unknownAuthenticationType':106
        , 'unknownDevice':70
        , 'unknownFileSize':122
        , 'unknownKey':107 #Removed revision 22
        , 'unknownKeyRevision':108 #Removed revision 22
        , 'unknownNetworkMessage':112
        , 'unknownObject':31
        , 'unknownProperty':32
        , 'unknownSubscription':79
        , 'umknownRoute':71
        , 'unknownSourceMessage':109 #Removed revision 22
        , 'unknownVtClass':34
        , 'unknownVtSession':35
        , 'unsupportedObjectType':36
        , 'valueNotInitialized':72
        , 'valueOutOfRange':37
        , 'valueTooLong':134
        , 'vtSessionAlreadyClosed':38
        , 'vtSessionTerminationFailure':39
        , 'websocket-close-error':168
        , 'websocket-closed-abnormally':173
        , 'websocket-closed-by-peer':169
        , 'websocket-data-against-policy':175
        , 'websocket-data-inconsistent':174
        , 'websocket-data-not-accepted':172
        , 'websocket-endpoint-leaves':170
        , 'websocket-error':179
        , 'websocket-extension-missing':177
        , 'websocket-frame-too-long':176
        , 'websocket-protocol-error':171
        , 'websocket-request-unavailable':178
        , 'websocket-scheme-not-supported':166
        , 'websocket-unknown-control-message':167
        , 'writeAccessDenied':40
        , 'writeBdtFailed':116
        }

class EscalatorMode(Enumerated):
    vendor_range = (1024, 65535)
    enumerations = \
        { 'unknown':0
        , 'stop':1
        , 'up':2
        , 'down':3
        , 'inspection':4
        , 'outOfService':5
        }

class EscalatorOperationDirection(Enumerated):
    vendor_range = (1024, 65535)
    enumerations = \
        { 'unknown':0
        , 'stopped':1
        , 'upRatedSpeed':2
        , 'upReducedSpeed':3
        , 'downRatedSpeed':4
        , 'downReducedSpeed':5
        }

class EventState(Enumerated):
    vendor_range = (64, 65535)
    enumerations = \
        { 'normal':0
        , 'fault':1
        , 'offnormal':2
        , 'highLimit':3
        , 'lowLimit':4
        , 'lifeSafetyAlarm':5
        }

class EventType(Enumerated):
    vendor_range = (64, 65535)
    enumerations = \
        { 'changeOfBitstring':0
        , 'changeOfState':1
        , 'changeOfValue':2
        , 'commandFailure':3
        , 'floatingLimit':4
        , 'outOfRange':5
        # -- context tag 7 is deprecated
        , 'changeOfLifeSafety':8
        , 'extended':9
        , 'bufferReady':10
        , 'unsignedRange':11
        # -- enumeration value 12 is reserved for future addenda
        , 'accessEvent':13
        , 'doubleOutOfRange':14
        , 'signedOutOfRange':15
        , 'unsignedOutOfRange':16
        , 'changeOfCharacterstring':17
        , 'changeOfStatusFlags':18
        , 'changeOfReliability':19
        }

class FaultType(Enumerated):
    enumerations = \
        { 'none':0
        , 'faultCharacterstring':1
        , 'faultExtended':2
        , 'faultLifeSafety':3
        , 'faultState':4
        , 'faultStatusFlags':5
        }

class FileAccessMethod(Enumerated):
    enumerations = \
        { 'recordAccess':0
        , 'streamAccess':1
        }

class LiftCarDirection(Enumerated):
    vendor_range = (1024, 65535)
    enumerations = \
        { 'unknown':0
        , 'none':1
        , 'stopped':2
        , 'up':3
        , 'down':4
        , 'upAndDown':5
        }

class LiftCarDoorCommand(Enumerated):
    enumerations = \
        { 'none':0
        , 'open':1
        , 'close':2
        }

class LiftCarDriveStatus(Enumerated):
    vendor_range = (1024, 65535)
    enumerations = \
        { 'unknown':0
        , 'stationary':1
        , 'braking':2
        , 'accelerate':3
        , 'decelerate':4
        , 'ratedSpeed':5
        , 'singleFloorJump':6
        , 'twoFloorJump':7
        , 'threeFloorJump':8
        , 'multiFloorJump':9
        }

class LiftCarMode(Enumerated):
    vendor_range = (1024, 65535)
    enumerations = \
        { 'unknown':0
        , 'normal':1
        , 'vip':2
        , 'homing':3
        , 'parking':4
        , 'attendantControl':5
        , 'firefighterControl':6
        , 'emergencyPower':7
        , 'inspection':8
        , 'cabinetRecall':9
        , 'earthquakeOperation':10
        , 'fireOperation':11
        , 'outOfService':12
        , 'occupantEvacuation':13
        }

class LiftFault(Enumerated):
    vendor_range = (1024, 65535)
    enumerations = \
        { 'controllerFault':0
        , 'driveAndMotorFault':1
        , 'governorAndSafetyGearFault':2
        , 'liftShaftDeviceFault':3
        , 'powerSupplyFault':4
        , 'safetyInterlockFault':5
        , 'doorClosingFault':6
        , 'doorOpeningFault':7
        , 'carStoppedOutsideLandingZone':8
        , 'callButtonStuck':9
        , 'startFailure':10
        , 'controllerSupplyFault':11
        , 'selfTestFailure':12
        , 'runtimeLimitExceeded':13
        , 'positionLost':14
        , 'driveTemperatureExceeded':15
        , 'loadMeasurementFault':16
        }

class LiftGroupMode(Enumerated):
    enumerations = \
        { 'unknown':0
        , 'normal':1
        , 'downPeak':2
        , 'twoWay':3
        , 'fourWay':4
        , 'emergencyPower':5
        , 'upPeak':6
        }

class LifeSafetyMode(Enumerated):
    enumerations = \
        { 'off':0
        , 'on':1
        , 'test':2
        , 'manned':3
        , 'unmanned':4
        , 'armed':5
        , 'disarmed':6
        , 'prearmed':7
        , 'slow':8
        , 'fast':9
        , 'disconnected':10
        , 'enabled':11
        , 'disabled':12
        , 'automaticReleaseDisabled':13
        , 'default':14
        }

class LifeSafetyOperation(Enumerated):
    vendor_range = (64, 65535)
    enumerations = \
        { 'none':0
        , 'silence':1
        , 'silenceAudible':2
        , 'silenceVisual':3
        , 'reset':4
        , 'resetAlarm':5
        , 'resetFault':6
        , 'unsilence':7
        , 'unsilenceAudible':8
        , 'unsilenceVisual':9
        }

class LifeSafetyState(Enumerated):
    enumerations = \
        { 'quiet':0
        , 'preAlarm':1
        , 'alarm':2
        , 'fault':3
        , 'faultPreAlarm':4
        , 'faultAlarm':5
        , 'notReady':6
        , 'active':7
        , 'tamper':8
        , 'testAlarm':9
        , 'testActive':10
        , 'testFault':11
        , 'testFaultAlarm':12
        , 'holdup':13
        , 'duress':14
        , 'tamperAlarm':15
        , 'abnormal':16
        , 'emergencyPower':17
        , 'delayed':18
        , 'blocked':19
        , 'localAlarm':20
        , 'generalAlarm':21
        , 'supervisory':22
        , 'testSupervisory':23
        }

class LightingInProgress(Enumerated):
    enumerations = \
        { 'idle':0
        , 'fadeActive':1
        , 'rampActive':2
        , 'notControlled':3
        , 'other':4
        }

class LightingOperation(Enumerated):
    vendor_range = (256, 65535)
    enumerations = \
        { 'none':0
        , 'fadeTo':1
        , 'rampTo':2
        , 'stepUp':3
        , 'stepDown':4
        , 'stepOn':5
        , 'stepOff':6
        , 'warn':7
        , 'warnOff':8
        , 'warnRelinquish':9
        , 'stop':10
        }

class LightingTransition(Enumerated):
    vendor_range = (64, 255)
    enumerations = \
        { 'none':0
        , 'fade':1
        , 'ramp':2
        }

class LockStatus(Enumerated):
    enumerations = \
        { 'locked':0
        , 'unlocked':1
        , 'fault':2
        , 'unknown':3
        }

class LoggingType(Enumerated):
    vendor_range = (64, 255)
    enumerations = \
        { 'polled':0
        , 'cov':1
        , 'triggered':2
        }

class Maintenance(Enumerated):
    vendor_range = (256, 65535)
    enumerations = \
        { 'none':0
        , 'periodicTest':1
        , 'needServiceOperational':2
        , 'needServiceInoperative':3
        }

class NodeType(Enumerated):
    enumerations = \
        { 'unknown':0
        , 'system':1
        , 'network':2
        , 'device':3
        , 'organizational':4
        , 'area':5
        , 'equipment':6
        , 'point':7
        , 'collection':8
        , 'property':9
        , 'functional':10
        , 'other':11
        }

class NotifyType(Enumerated):
    enumerations = \
        { 'alarm':0
        , 'event':1
        , 'ackNotification':2
        }

class Polarity(Enumerated):
    enumerations = \
        { 'normal':0
        , 'reverse':1
        }

class ProgramError(Enumerated):
    vendor_range = (64, 65535)
    enumerations = \
        { 'normal':0
        , 'loadFailed':1
        , 'internal':2
        , 'program':3
        , 'other':4
        }

class ProgramRequest(Enumerated):
    enumerations = \
        { 'ready':0
        , 'load':1
        , 'run':2
        , 'halt':3
        , 'restart':4
        , 'unload':5
        }

class ProgramState(Enumerated):
    enumerations = \
        { 'idle':0
        , 'loading':1
        , 'running':2
        , 'waiting':3
        , 'halted':4
        , 'unloading':5
        }

class PropertyIdentifier(Enumerated):
    vendor_range = (512, 4194303)
    enumerations = \
        { 'absenteeLimit':244
        , 'acceptedModes':175
        , 'accessAlarmEvents':245
        , 'accessDoors':246
        , 'accessEvent':247
        , 'accessEventAuthenticationFactor':248
        , 'accessEventCredential':249
        , 'accessEventTag':322
        , 'accessEventTime':250
        , 'accessTransactionEvents':251
        , 'accompaniment':252
        , 'accompanimentTime':253
        , 'ackedTransitions':0
        , 'ackRequired':1
        , 'action':2
        , 'actionText':3
        , 'activationTime':254
        , 'activeAuthenticationPolicy':255
        , 'activeCovMultipleSubscriptions':481
        , 'activeCovSubscriptions':152
        , 'activeText':4
        , 'activeVtSessions':5
        , 'actualShedLevel':212
        , 'adjustValue':176
        , 'alarmValue':6
        , 'alarmValues':7
        , 'alignIntervals':193
        , 'all':8
        , 'allowGroupDelayInhibit':365
        , 'allWritesSuccessful':9
        , 'apduLength':399
        , 'apduSegmentTimeout':10
        , 'apduTimeout':11
        , 'applicationSoftwareVersion':12
        , 'archive':13
        , 'assignedAccessRights':256
        , 'assignedLandingCalls':447
        , 'attemptedSamples':124
        , 'auditableOperations':501
        , 'auditablePriorityFilter':500
        , 'auditLevel':498
        , 'auditNotificationRecipient':499
        , 'auditSourceReporter':497
        , 'authenticationFactors':257
        , 'authenticationPolicyList':258
        , 'authenticationPolicyNames':259
        , 'authenticationStatus':260
        , 'authorizationExemptions':364
        , 'authorizationMode':261
        , 'autoSlaveDiscovery':169
        , 'averageValue':125
        , 'backupAndRestoreState':338
        , 'backupFailureTimeout':153
        , 'backupPreparationTime':339
        , 'bacnetIPGlobalAddress':407
        , 'bacnetIPMode':408
        , 'bacnetIPMulticastAddress':409
        , 'bacnetIPNATTraversal':410
        , 'bacnetIPUDPPort':412
        , 'bacnetIPv6Mode':435
        , 'bacnetIPv6MulticastAddress':440
        , 'bacnetIPv6UDPPort':438
        , 'baseDeviceSecurityPolicy':327
        , 'bbmdAcceptFDRegistrations':413
        , 'bbmdBroadcastDistributionTable':414
        , 'bbmdForeignDeviceTable':415
        , 'belongsTo':262
        , 'bias':14
        , 'bitMask':342
        , 'bitText':343
        , 'blinkWarnEnable':373
        , 'bufferSize':126
        , 'carAssignedDirection':448
        , 'carDoorCommand':449
        , 'carDoorStatus':450
        , 'carDoorText':451
        , 'carDoorZone':452
        , 'carDriveStatus':453
        , 'carLoad':454
        , 'carLoadUnits':455
        , 'carMode':456
        , 'carMovingDirection':457
        , 'carPosition':458
        , 'changeOfStateCount':15
        , 'changeOfStateTime':16
        , 'changesPending':416
        , 'channelNumber':366
        , 'clientCovIncrement':127
        , 'command':417
        , 'commandTimeArray':430
        , 'configurationFiles':154
        , 'controlGroups':367
        , 'controlledVariableReference':19
        , 'controlledVariableUnits':20
        , 'controlledVariableValue':21
        , 'count':177
        , 'countBeforeChange':178
        , 'countChangeTime':179
        , 'covIncrement':22
        , 'covPeriod':180
        , 'covResubscriptionInterval':128
        , 'covuPeriod':349
        , 'covuRecipients':350
        , 'credentialDisable':263
        , 'credentials':265
        , 'credentialsInZone':266
        , 'credentialStatus':264
        , 'currentCommandPriority':431
        , 'databaseRevision':155
        , 'dateList':23
        , 'daylightSavingsStatus':24
        , 'daysRemaining':267
        , 'deadband':25
        , 'defaultFadeTime':374
        , 'defaultPresentValue':492
        , 'defaultRampRate':375
        , 'defaultStepIncrement':376
        , 'defaultSubordinateRelationship':490
        , 'defaultTimeout':393
        , 'deleteOnForward':502
        , 'deployedProfileLocation':484
        , 'derivativeConstant':26
        , 'derivativeConstantUnits':27
        , 'description':28
        , 'descriptionOfHalt':29
        , 'deviceAddressBinding':30
        , 'deviceType':31
        , 'deviceUUID':507
        , 'directReading':156
        , 'distributionKeyRevision':328
        , 'doNotHide':329
        , 'doorAlarmState':226
        , 'doorExtendedPulseTime':227
        , 'doorMembers':228
        , 'doorOpenTooLongTime':229
        , 'doorPulseTime':230
        , 'doorStatus':231
        , 'doorUnlockDelayTime':232
        , 'dutyWindow':213
        , 'effectivePeriod':32
        , 'egressActive':386
        , 'egressTime':377
        , 'elapsedActiveTime':33
        , 'elevatorGroup':459
        , 'enable':133
        , 'energyMeter':460
        , 'energyMeterRef':461
        , 'entryPoints':268
        , 'errorLimit':34
        , 'escalatorMode':462
        , 'eventAlgorithmInhibit':354
        , 'eventAlgorithmInhibitRef':355
        , 'eventDetectionEnable':353
        , 'eventEnable':35
        , 'eventMessageTexts':351
        , 'eventMessageTextsConfig':352
        , 'eventParameters':83
        , 'eventState':36
        , 'eventTimeStamps':130
        , 'eventType':37
        , 'exceptionSchedule':38
        , 'executionDelay':368
        , 'exitPoints':269
        , 'expectedShedLevel':214
        , 'expirationTime':270
        , 'extendedTimeEnable':271
        , 'failedAttemptEvents':272
        , 'failedAttempts':273
        , 'failedAttemptsTime':274
        , 'faultHighLimit':388
        , 'faultLowLimit':389
        , 'faultParameters':358
        , 'faultSignals':463
        , 'faultType':359
        , 'faultValues':39
        , 'fdBBMDAddress':418
        , 'fdSubscriptionLifetime':419
        , 'feedbackValue':40
        , 'fileAccessMethod':41
        , 'fileSize':42
        , 'fileType':43
        , 'firmwareRevision':44
        , 'floorNumber':506
        , 'floorText':464
        , 'fullDutyBaseline':215
        , 'globalIdentifier':323
        , 'groupID':465
        , 'groupMemberNames':346
        , 'groupMembers':345
        , 'groupMode':467
        , 'higherDeck':468
        , 'highLimit':45
        , 'inactiveText':46
        , 'initialTimeout':394
        , 'inProcess':47
        , 'inProgress':378
        , 'inputReference':181
        , 'installationID':469
        , 'instanceOf':48
        , 'instantaneousPower':379
        , 'integralConstant':49
        , 'integralConstantUnits':50
        , 'interfaceValue':387
        , 'intervalOffset':195
        , 'ipAddress':400
        , 'ipDefaultGateway':401
        , 'ipDHCPEnable':402
        , 'ipDHCPLeaseTime':403
        , 'ipDHCPLeaseTimeRemaining':404
        , 'ipDHCPServer':405
        , 'ipDNSServer':406
        , 'ipSubnetMask':411
        , 'ipv6Address':436
        , 'ipv6AutoAddressingEnable':442
        , 'ipv6DefaultGateway':439
        , 'ipv6DHCPLeaseTime':443
        , 'ipv6DHCPLeaseTimeRemaining':444
        , 'ipv6DHCPServer':445
        , 'ipv6DNSServer':441
        , 'ipv6PrefixLength':437
        , 'ipv6ZoneIndex':446
        , 'issueConfirmedNotifications':51
        , 'isUTC':344
        , 'keySets':330
        , 'landingCallControl':471
        , 'landingCalls': 470
        , 'landingDoorStatus':472
        , 'lastAccessEvent':275
        , 'lastAccessPoint':276
        , 'lastCommandTime':432
        , 'lastCredentialAdded':277
        , 'lastCredentialAddedTime':278
        , 'lastCredentialRemoved':279
        , 'lastCredentialRemovedTime':280
        , 'lastKeyServer':331
        , 'lastNotifyRecord':173
        , 'lastPriority':369
        , 'lastRestartReason':196
        , 'lastRestoreTime':157
        , 'lastStateChange':395
        , 'lastUseTime':281
        , 'lifeSafetyAlarmValues':166
        , 'lightingCommand':380
        , 'lightingCommandDefaultPriority':381
        , 'limitEnable':52
        , 'limitMonitoringInterval':182
        , 'linkSpeed':420
        , 'linkSpeedAutonegotiate':422
        , 'linkSpeeds':421
        , 'listOfGroupMembers':53
        , 'listOfObjectPropertyReferences':54
        , 'listOfSessionKeys':55
        , 'localDate':56
        , 'localForwardingOnly':360
        , 'localTime':57
        , 'location':58
        , 'lockout':282
        , 'lockoutRelinquishTime':283
        , 'lockStatus':233
        , 'logBuffer':131
        , 'logDeviceObjectProperty':132
        , 'loggingObject':183
        , 'loggingRecord':184
        , 'loggingType':197
        , 'logInterval':134
        , 'lowDiffLimit':390
        , 'lowerDeck':473
        , 'lowLimit':59
        , 'macAddress':423
        , 'machineRoomID':474
        , 'maintenanceRequired':158
        , 'makingCarCall':475
        , 'manipulatedVariableReference':60
        , 'manualSlaveAddressBinding':170
        , 'maskedAlarmValues':234
        , 'masterExemption':284
        , 'maxActualValue':382
        , 'maxApduLengthAccepted':62
        , 'maxFailedAttempts':285
        , 'maximumOutput':61
        , 'maximumSendDelay':503
        , 'maximumValue':135
        , 'maximumValueTimestamp':149
        , 'maxInfoFrames':63
        , 'maxMaster':64
        , 'maxPresValue':65
        , 'maxSegmentsAccepted':167
        , 'memberOf':159
        , 'members':286
        , 'memberStatusFlags':347
        , 'minActualValue':383
        , 'minimumOffTime':66
        , 'minimumOnTime':67
        , 'minimumOutput':68
        , 'minimumValue':136
        , 'minimumValueTimestamp':150
        , 'minPresValue':69
        , 'mode':160
        , 'modelName':70
        , 'modificationDate':71
        , 'monitoredObjects':504
        , 'musterPoint':287
        , 'negativeAccessRules':288
        , 'networkAccessSecurityPolicies':332
        , 'networkInterfaceName':424
        , 'networkNumber':425
        , 'networkNumberQuality':426
        , 'networkType': 427
        , 'nextStoppingFloor':476
        , 'nodeSubtype':207
        , 'nodeType':208
        , 'notificationClass':17
        , 'notificationThreshold':137
        , 'notifyType':72
        , 'numberOfApduRetries':73
        , 'numberOfAuthenticationPolicies':289
        , 'numberOfStates':74
        , 'objectIdentifier':75
        , 'objectList':76
        , 'objectName':77
        , 'objectPropertyReference':78
        , 'objectType':79
        , 'occupancyCount':290
        , 'occupancyCountAdjust':291
        , 'occupancyCountEnable':292
        , 'occupancyExemption':293
        , 'occupancyLowerLimit':294
        , 'occupancyLowerLimitEnforced':295
        , 'occupancyState':296
        , 'occupancyUpperLimit':297
        , 'occupancyUpperLimitEnforced':298
        , 'operationDirection':477
        , 'operationExpected':161
        , 'optional':80
        , 'outOfService':81
        , 'outputUnits':82
        , 'packetReorderTime':333
        , 'passbackExemption':299
        , 'passbackMode':300
        , 'passbackTimeout':301
        , 'passengerAlarm':478
        , 'polarity':84
        , 'portFilter':363
        , 'positiveAccessRules':302
        , 'power':384
        , 'powerMode':479
        , 'prescale':185
        , 'presentStage':493
        , 'presentValue':85
        , 'priority':86
        , 'priorityArray':87
        , 'priorityForWriting':88
        , 'processIdentifier':89
        , 'processIdentifierFilter':361
        , 'profileLocation':485
        , 'profileName':168
        , 'programChange':90
        , 'programLocation':91
        , 'programState':92
        , 'propertyList':371
        , 'proportionalConstant':93
        , 'proportionalConstantUnits':94
        , 'protocolLevel':482
        , 'protocolObjectTypesSupported':96
        , 'protocolRevision':139
        , 'protocolServicesSupported':97
        , 'protocolVersion':98
        , 'pulseRate':186
        , 'readOnly':99
        , 'reasonForDisable':303
        , 'reasonForHalt':100
        , 'recipientList':102
        , 'recordCount':141
        , 'recordsSinceNotification':140
        , 'referencePort':483
        , 'registeredCarCall':480
        , 'reliability':103
        , 'reliabilityEvaluationInhibit':357
        , 'relinquishDefault':104
        , 'represents':491
        , 'requestedShedLevel':218
        , 'requestedUpdateInterval':348
        , 'required':105
        , 'resolution':106
        , 'restartNotificationRecipients':202
        , 'restoreCompletionTime':340
        , 'restorePreparationTime':341
        , 'routingTable':428
        , 'scale':187
        , 'scaleFactor':188
        , 'scheduleDefault':174
        , 'securedStatus':235
        , 'securityPDUTimeout':334
        , 'securityTimeWindow':335
        , 'segmentationSupported':107
        , 'sendNow':505
        , 'serialNumber':372
        , 'setpoint':108
        , 'setpointReference':109
        , 'setting':162
        , 'shedDuration':219
        , 'shedLevelDescriptions':220
        , 'shedLevels':221
        , 'silenced':163
        , 'slaveAddressBinding':171
        , 'slaveProxyEnable':172
        , 'stageNames':495
        , 'stages':494
        , 'startTime':142
        , 'stateChangeValues':396
        , 'stateDescription':222
        , 'stateText':110
        , 'statusFlags':111
        , 'stopTime':143
        , 'stopWhenFull':144
        , 'strikeCount':391
        , 'structuredObjectList':209
        , 'subordinateAnnotations':210
        , 'subordinateList':211
        , 'subordinateNodeTypes':487
        , 'subordinateRelationships':489
        , 'subordinateTags':488
        , 'subscribedRecipients':362
        , 'supportedFormatClasses':305
        , 'supportedFormats':304
        , 'supportedSecurityAlgorithms':336
        , 'systemStatus':112
        , 'tags':486
        , 'targetReferences':496
        , 'threatAuthority':306
        , 'threatLevel':307
        , 'timeDelay':113
        , 'timeDelayNormal':356
        , 'timeOfActiveTimeReset':114
        , 'timeOfDeviceRestart':203
        , 'timeOfStateCountReset':115
        , 'timeOfStrikeCountReset':392
        , 'timerRunning':397
        , 'timerState':398
        , 'timeSynchronizationInterval':204
        , 'timeSynchronizationRecipients':116
        , 'totalRecordCount':145
        , 'traceFlag':308
        , 'trackingValue':164
        , 'transactionNotificationClass':309
        , 'transition':385
        , 'trigger':205
        , 'units':117
        , 'updateInterval':118
        , 'updateKeySetTimeout':337
        , 'updateTime':189
        , 'userExternalIdentifier':310
        , 'userInformationReference':311
        , 'userName':317
        , 'userType':318
        , 'usesRemaining':319
        , 'utcOffset':119
        , 'utcTimeSynchronizationRecipients':206
        , 'validSamples':146
        , 'valueBeforeChange':190
        , 'valueChangeTime':192
        , 'valueSet':191
        , 'valueSource':433
        , 'valueSourceArray':434
        , 'varianceValue':151
        , 'vendorIdentifier':120
        , 'vendorName':121
        , 'verificationTime':326
        , 'virtualMACAddressTable':429
        , 'vtClassesSupported':122
        , 'weeklySchedule':123
        , 'windowInterval':147
        , 'windowSamples':148
        , 'writeStatus':370
        , 'zoneFrom':320
        , 'zoneMembers':165
        , 'zoneTo':321
        }

class Relationship(Enumerated):
    vendor_range = (1024, 65535)
    enumerations = \
        { 'unknown':0
        , 'default':1
        , 'contains':2
        , 'containedBy':3
        , 'uses':4
        , 'usedBy':5
        , 'commands':6
        , 'commandedBy':7
        , 'adjusts':8
        , 'adjustedBy':9
        , 'ingress':10
        , 'egress':11
        , 'suppliesAir':12
        , 'receivesAir':13
        , 'suppliesHotAir':14
        , 'receivesHotAir':15
        , 'suppliesCoolAir':16
        , 'receivesCoolAir':17
        , 'suppliesPower':18
        , 'receivesPower':19
        , 'suppliesGas':20
        , 'receivesGas':21
        , 'suppliesWater':22
        , 'receivesWater':23
        , 'suppliesHotWater':24
        , 'receivesHotWater':25
        , 'suppliesCoolWater':26
        , 'receivesCoolWater':27
        , 'suppliesSteam':28
        , 'receivesSteam':29
        }

class Reliability(Enumerated):
    vendor_range = (64, 65535)
    enumerations = \
        { 'noFaultDetected':0
        , 'noSensor':1
        , 'overRange':2
        , 'underRange':3
        , 'openLoop':4
        , 'shortedLoop':5
        , 'noOutput':6
        , 'unreliableOther':7
        , 'processError':8
        , 'multiStateFault':9
        , 'configurationError':10
        , 'communicationFailure':12
        , 'memberFault': 13
        , 'monitoredObjectFault': 14
        , 'tripped': 15
        , 'lampFailure': 16
        , 'activationFailure': 17
        , 'renewDHCPFailure': 18
        , 'renewFDRegistrationFailure': 19
        , 'restartAutoNegotiationFailure': 20
        , 'restartFailure': 21
        , 'proprietaryCommandFailure': 22
        , 'faultsListed': 23
        , 'referencedObjectFault': 24
        , 'multiStateOutOfRange':25
        }

class RestartReason(Enumerated):
    vendor_range = (64, 255)
    enumerations = \
        { 'unknown':0
        , 'coldstart':1
        , 'warmstart':2
        , 'detectedPowerLost':3
        , 'detectedPoweredOff':4
        , 'hardwareWatchdog':5
        , 'softwareWatchdog':6
        , 'suspended':7
        , 'activateChanges':8
        }

class SecurityLevel(Enumerated):
    enumerations = \
        { 'incapable':0
        , 'plain':1
        , 'signed':2
        , 'encrypted':3
        , 'signedEndToEnd':4
        , 'encryptedEndToEnd':4
        }

class SecurityPolicy(Enumerated):
    enumerations = \
        { 'plainNonTrusted':0
        , 'plainTrusted':1
        , 'signedTrusted':2
        , 'encryptedTrusted':3
        }

class ShedState(Enumerated):
    enumerations = \
        { 'shedInactive':0
        , 'shedRequestPending':1
        , 'shedCompliant':2
        , 'shedNonCompliant':3
        }

class Segmentation(Enumerated):
    enumerations = \
        { 'segmentedBoth':0
        , 'segmentedTransmit':1
        , 'segmentedReceive':2
        , 'noSegmentation':3
        }

class SilencedState(Enumerated):
    vendor_range = (64, 65535)
    enumerations = \
        { 'unsilenced':0
        , 'audibleSilenced':1
        , 'visibleSilenced':2
        , 'allSilenced':3
        }

class TimerState(Enumerated):
    enumerations = \
        { 'idle':0
        , 'running':1
        , 'expired':2
        }

class TimerTransition(Enumerated):
    enumerations = \
        { 'none':0
        , 'idleToRunning':1
        , 'runningToIdle':2
        , 'runningToRunning':3
        , 'runningToExpired':4
        , 'forcedToExpired':5
        , 'expiredToIdle':6
        , 'expiredToRunning':7
        }

class VTClass(Enumerated):
    vendor_range = (64, 65535)
    enumerations = \
        { 'defaultTerminal':0
        , 'ansiX364':1
        , 'decVt52':2
        , 'decVt100':3
        , 'decVt220':4
        , 'hp70094':5
        , 'ibm3130':6
        }

class WriteStatus(Enumerated):
    enumerations = \
        { 'idle':0
        , 'inProgress':1
        , 'successful':2
        , 'failed':3
        }

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
    enumerations = \
        { 'available':0
        , 'busy':1
        , 'disconnected':2
        }

#
#   Forward Sequences
#

class HostAddress(Choice):
    choiceElements = \
        [ Element('none', Null, 0)
        , Element('ipAddress', OctetString, 1)  # 4 octets for B/IP or 16 octets for B/IPv6
        , Element('name', CharacterString, 2)  # Internet host name (see RFC 1123)
        ]

class HostNPort(Sequence):
    sequenceElements = \
        [ Element('host', HostAddress, 0)
        , Element('port', Unsigned16, 1)
        ]

class BDTEntry(Sequence):
    sequenceElements = \
        [ Element('bbmdAddress', HostNPort, 0)
        , Element('broadcastMask', OctetString, 1)  # shall be present if BACnet/IP, and absent for BACnet/IPv6
        ]

class FDTEntry(Sequence):
    sequenceElements = \
        [ Element('bacnetIPAddress', OctetString, 0)  # the 6-octet B/IP or 18-octet B/IPv6 address of the registrant
        , Element('timeToLive', Unsigned16, 1)  # time to live in seconds at the time of registration
        , Element('remainingTimeToLive', Unsigned16, 2)  # remaining time to live in seconds, incl. grace period
        ]

class VMACEntry(Sequence):
    sequenceElements = \
        [ Element('virtualMACAddress', OctetString, 0)  # maximum size 6 octets
        , Element('nativeMACAddress', OctetString, 1)
        ]

class PropertyReference(Sequence):
    sequenceElements = \
        [ Element('propertyIdentifier', PropertyIdentifier, 0)
        , Element('propertyArrayIndex', Unsigned, 1, True)
        ]

class RouterEntry(Sequence):
    sequenceElements = \
        [ Element('networkNumber', Unsigned16, 0)
        , Element('macAddress', OctetString, 1)
        , Element('status', RouterEntryStatus, 2)  # Defined Above
        , Element('performanceIndex', Unsigned8, 3, True)
        ]

@bacpypes_debugging
class NameValue(Sequence):
    sequenceElements = \
        [ Element('name', CharacterString)
        , Element('value', AnyAtomic, None, True)
        ]

    def __init__(self, name=None, value=None):
        if _debug: NameValue._debug("__init__ name=%r value=%r", name, value)

        # default to no value
        self.name = name
        self.value = None

        if value is None:
            pass
        elif isinstance(value, (Atomic, DateTime)):
            self.value = value
        elif isinstance(value, Tag):
            self.value = value.app_to_object()
        else:
            raise TypeError("invalid constructor datatype")

    def encode(self, taglist):
        if _debug: NameValue._debug("(%r)encode %r", self.__class__.__name__, taglist)

        # build a tag and encode the name into it
        tag = Tag()
        CharacterString(self.name).encode(tag)
        taglist.append(tag.app_to_context(0))

        # the value is optional
        if self.value is not None:
            if isinstance(self.value, DateTime):
                # has its own encoder
                self.value.encode(taglist)
            else:
                # atomic values encode into a tag
                tag = Tag()
                self.value.encode(tag)
                taglist.append(tag)

    def decode(self, taglist):
        if _debug: NameValue._debug("(%r)decode %r", self.__class__.__name__, taglist)

        # no contents yet
        self.name = None
        self.value = None

        # look for the context encoded character string
        tag = taglist.Peek()
        if _debug: NameValue._debug("    - name tag: %r", tag)
        if (tag is None) or (tag.tagClass != Tag.contextTagClass) or (tag.tagNumber != 0):
            raise MissingRequiredParameter("%s is a missing required element of %s" % ('name', self.__class__.__name__))

        # pop it off and save the value
        taglist.Pop()
        tag = tag.context_to_app(Tag.characterStringAppTag)
        self.name = CharacterString(tag).value

        # look for the optional application encoded value
        tag = taglist.Peek()
        if _debug: NameValue._debug("    - value tag: %r", tag)
        if tag and (tag.tagClass == Tag.applicationTagClass):

            # if it is a date check the next one for a time
            if (tag.tagNumber == Tag.dateAppTag) and (len(taglist.tagList) >= 2):
                next_tag = taglist.tagList[1]
                if _debug: NameValue._debug("    - next_tag: %r", next_tag)

                if (next_tag.tagClass == Tag.applicationTagClass) and (next_tag.tagNumber == Tag.timeAppTag):
                    if _debug: NameValue._debug("    - remaining tag list 0: %r", taglist.tagList)

                    self.value = DateTime()
                    self.value.decode(taglist)
                    if _debug: NameValue._debug("    - date time value: %r", self.value)

            # just a primitive value
            if self.value is None:
                taglist.Pop()
                self.value = tag.app_to_object()

class NameValueCollection(Sequence):
    sequenceElements = \
        [ Element('members', SequenceOf(NameValue), 0)
        ]

class DeviceAddress(Sequence):
    sequenceElements = \
        [ Element('networkNumber', Unsigned)
        , Element('macAddress', OctetString)
        ]

class DeviceObjectPropertyReference(Sequence):
    sequenceElements = \
        [ Element('objectIdentifier', ObjectIdentifier, 0)
        , Element('propertyIdentifier', PropertyIdentifier, 1)
        , Element('propertyArrayIndex', Unsigned, 2, True)
        , Element('deviceIdentifier', ObjectIdentifier, 3, True)
        ]

class DeviceObjectReference(Sequence):
    sequenceElements = \
        [ Element('deviceIdentifier', ObjectIdentifier, 0, True)
        , Element('objectIdentifier', ObjectIdentifier, 1)
        ]

class DateTime(Sequence):
    sequenceElements = \
        [ Element('date', Date)
        , Element('time', Time)
        ]

    def __str__(self):
        return "%s(date=%s, time=%s)" % (self.__class__.__name__, self.date, self.time)

class DateRange(Sequence):
    sequenceElements = \
        [ Element('startDate', Date)
        , Element('endDate', Date)
        ]

class ErrorType(Sequence):
    sequenceElements = \
        [ Element('errorClass', ErrorClass)
        , Element('errorCode', ErrorCode)
        ]


class LandingCallStatusCommand(Choice):
    choiceElements = \
        [ Element('direction', LiftCarDirection, 1)
        , Element('destination', Unsigned8, 2)
        ]

class LandingCallStatus(Sequence):
    sequenceElements = \
        [ Element('floorNumber', Unsigned8, 0)
        , Element('command', LandingCallStatusCommand)
        , Element('floorText', CharacterString, 3, True)
        ]

class LandingDoorStatusLandingDoor(Sequence):
    sequenceElements = \
        [ Element('floorNumber', Unsigned8, 0)
        , Element('doorStatus', DoorStatus, 1)
        ]

class LandingDoorStatus(Sequence):
    sequenceElements = \
        [ Element('landingDoors', SequenceOf(LandingDoorStatusLandingDoor), 0)
        ]

class LiftCarCallList(Sequence):
    sequenceElements = \
        [ Element('floorNumbers', SequenceOf(Unsigned8), 0)
        ]

class LightingCommand(Sequence):
    sequenceElements = \
        [ Element('operation', LightingOperation, 0)
        , Element('targetLevel', Real, 1, True)
        , Element('rampRate', Real, 2, True)
        , Element('stepIncrement', Real, 3, True)
        , Element('fadeTime', Unsigned, 4, True)
        , Element('priority', Unsigned, 5, True)
        ]

class ObjectPropertyReference(Sequence):
    sequenceElements = \
        [ Element('objectIdentifier', ObjectIdentifier, 0)
        , Element('propertyIdentifier', PropertyIdentifier, 1)
        , Element('propertyArrayIndex', Unsigned, 2, True)
        ]

class OptionalBinaryPV(Choice):
    choiceElements = \
        [ Element('null', Null)
        , Element('binaryPV', BinaryPV)
        ]

class OptionalCharacterString(Choice):
    choiceElements = \
        [ Element('null', Null)
        , Element('characterstring', CharacterString)
        ]

class OptionalPriorityFilter(Choice):
    choiceElements = \
        [ Element('null', Null)
        , Element('filter', PriorityFilter)
        ]

class OptionalReal(Choice):
    choiceElements = \
        [ Element('null', Null)
        , Element('real', Real)
        ]

class OptionalUnsigned(Choice):
    choiceElements = \
        [ Element('null', Null)
        , Element('unsigned', Unsigned)
        ]

class ProcessIdSelection(Choice):
    choiceElements = \
        [ Element('processIdentifier', Unsigned)
        , Element('nullValue', Null)
        ]

class PropertyStates(Choice):
    vendor_range = (64, 254)
    choiceElements = \
        [ Element('booleanValue', Boolean, 0)
        , Element('binaryValue', BinaryPV, 1)
        , Element('eventType', EventType, 2)
        , Element('polarity', Polarity, 3)
        , Element('programChange', ProgramRequest, 4)
        , Element('programState', ProgramState, 5)
        , Element('reasonForHalt', ProgramError, 6)
        , Element('reliability', Reliability, 7)
        , Element('state', EventState, 8)
        , Element('systemStatus', DeviceStatus, 9)
        , Element('units', EngineeringUnits, 10)
        , Element('unsignedValue', Unsigned, 11)
        , Element('lifeSafetyMode', LifeSafetyMode, 12)
        , Element('lifeSafetyState', LifeSafetyState, 13)
        , Element('restartReason', RestartReason, 14)
        , Element('doorAlarmState', DoorAlarmState, 15)
        , Element('action', Action, 16)
        , Element('doorSecuredStatus', DoorSecuredStatus, 17)
        , Element('doorStatus', DoorStatus, 18)
        , Element('doorValue', DoorValue, 19)
        , Element('fileAccessMethod', FileAccessMethod, 20)
        , Element('lockStatus', LockStatus, 21)
        , Element('lifeSafetyOperation', LifeSafetyOperation, 22)
        , Element('maintenance', Maintenance, 23)
        , Element('nodeType', NodeType, 24)
        , Element('notifyType', NotifyType, 25)
        , Element('securityLevel', SecurityLevel, 26)
        , Element('shedState', ShedState, 27)
        , Element('silencedState', SilencedState, 28)
        , Element('accessEvent', AccessEvent, 30)
        , Element('zoneOccupancyState', AccessZoneOccupancyState, 31)
        , Element('accessCredentialDisableReason', AccessCredentialDisableReason, 32)
        , Element('accessCredentialDisable', AccessCredentialDisable, 33)
        , Element('authenticationStatus', AuthenticationStatus, 34)
        , Element('backupState', BackupState, 36)
        , Element('writeStatus', WriteStatus, 370)
        , Element('lightingInProgress', LightingInProgress, 38)
        , Element('lightingOperation', LightingOperation, 39)
        , Element('lightingTransition', LightingTransition, 40)
        ]

class PropertyValue(Sequence):
    sequenceElements = \
        [ Element('propertyIdentifier', PropertyIdentifier, 0)
        , Element('propertyArrayIndex', Unsigned, 1, True)
        , Element('value', Any, 2)
        , Element('priority', Unsigned, 3, True)
        ]

class Recipient(Choice):
    choiceElements = \
        [ Element('device', ObjectIdentifier, 0)
        , Element('address', DeviceAddress, 1)
        ]

class RecipientProcess(Sequence):
    sequenceElements = \
        [ Element('recipient', Recipient, 0)
        , Element('processIdentifier', Unsigned, 1)
        ]

class TimerStateChangeValue(Choice):
    choiceElements = \
        [ Element('null', Null)
        , Element('boolean', Boolean)
        , Element('unsigned', Unsigned)
        , Element('integer', Integer)
        , Element('real', Real)
        , Element('double', Double)
        , Element('octetstring', OctetString)
        , Element('characterstring', CharacterString)
        , Element('bitstring', BitString)
        , Element('enumerated', Enumerated)
        , Element('date', Date)
        , Element('time', Time)
        , Element('objectidentifier', ObjectIdentifier)
        , Element('noValue', Null, 0)
        , Element('constructedValue', Any, 1)
        , Element('datetime', DateTime, 2)
        , Element('lightingCommand', LightingCommand, 3)
        ]

class TimeStamp(Choice):
    choiceElements = \
        [ Element('time', Time, 0)
        , Element('sequenceNumber', Unsigned, 1)
        , Element('dateTime', DateTime, 2)
        ]

class TimeValue(Sequence):
    sequenceElements = \
        [ Element('time', Time)
        , Element('value', AnyAtomic)
        ]

class WeekNDay(OctetString):

    def __str__(self):
        if len(self.value) != 3:
            return "WeekNDay(?): " + OctetString.__str__(self)
        else:
            return "WeekNDay(%d, %d, %d)" % (ord(self.value[0]), ord(self.value[1]), ord(self.value[2]))

#
#   Sequences
#

class AccessRule(Sequence):
    sequenceElements = \
        [ Element('timeRangeSpecifier', AccessRuleTimeRangeSpecifier, 0)
        , Element('timeRange', DeviceObjectPropertyReference, 1, True)
        , Element('locationSpecifier', AccessRuleLocationSpecifier, 2)
        , Element('location', DeviceObjectReference, 3, True)
        , Element('enable', Boolean, 4)
        ]

class AccessThreatLevel(Unsigned):
    _low_limit = 0
    _high_limit = 100

class AccumulatorRecord(Sequence):
    sequenceElements = \
        [ Element('timestamp', DateTime, 0)
        , Element('presentValue', Unsigned, 1)
        , Element('accumulatedValue', Unsigned, 2)
        , Element('accumulatorStatus', AccumulatorRecordAccumulatorStatus, 3)
        ]

class ActionCommand(Sequence):
    sequenceElements = \
        [ Element('deviceIdentifier', ObjectIdentifier, 0, True)
        , Element('objectIdentifier', ObjectIdentifier, 1)
        , Element('propertyIdentifier', PropertyIdentifier, 2)
        , Element('propertyArrayIndex', Unsigned, 3, True)
        , Element('propertyValue', Any, 4)
        , Element('priority', Unsigned, 5, True)
        , Element('postDelay', Unsigned, 6, True)
        , Element('quiteOnFailure', Boolean, 7)
        , Element('writeSuccessFul', Boolean, 8)
        ]

class ActionList(Sequence):
    sequenceElements = \
        [ Element('action', SequenceOf(ActionCommand), 0)
        ]

class Address(Sequence):
    sequenceElements = \
        [ Element('networkNumber', Unsigned16)
        , Element('macAddress', OctetString)
        ]

class AddressBinding(Sequence):
    sequenceElements = \
        [ Element('deviceObjectIdentifier', ObjectIdentifier)
        , Element('deviceAddress', DeviceAddress)
        ]

class AssignedAccessRights(Sequence):
    serviceChoice = 15
    sequenceElements = \
        [ Element('assignedAccessRights', DeviceObjectReference, 0)
        , Element('enable', Boolean, 1)
        ]

class AssignedLandingCallsLandingCalls(Sequence):
    sequenceElements = \
        [ Element('floorNumber', Unsigned8, 0)
        , Element('direction', LiftCarDirection, 1)
        ]

class AssignedLandingCalls(Sequence):
    sequenceElements = \
        [ Element('landingCalls', SequenceOf(AssignedLandingCallsLandingCalls), 0)
        ]

class AuditNotification(Sequence):
    sequenceElements = \
        [ Element('sourceTimestamp', TimeStamp, 0, True)
        , Element('targetTimestamp', TimeStamp, 1, True)
        , Element('sourceDevice', Recipient, 2)
        , Element('sourceObject', ObjectIdentifier, 3, True)
        , Element('operation', AuditOperation, 4)
        , Element('sourceComment', CharacterString, 5, True)
        , Element('targetComment', CharacterString, 6, True)
        , Element('invokeID', Unsigned8, 7, True)
        , Element('sourceUserID', Unsigned16, 8, True)
        , Element('sourceUserRole', Unsigned8, 9, True)
        , Element('targetDevice', Recipient, 10)
        , Element('targetObject', ObjectIdentifier, 11, True)
        , Element('targetProperty', PropertyReference, 12, True)
        , Element('targetPriority', Unsigned, 13, True)  # 1..16
        , Element('targetValue', Any, 14, True)
        , Element('currentValue', Any, 15, True)
        , Element('result', ErrorType, 16, True)
        ]

class AuditLogRecordLogDatum(Choice):
    choiceElements = \
        [ Element('logStatus', LogStatus, 0)
        , Element('auditNotification', AuditNotification, 1)
        , Element('timeChange', Real)
        ]

class AuditLogRecord(Sequence):
    sequenceElements = \
        [ Element('timestamp', DateTime, 0)
        , Element('logDatum', AuditLogRecordLogDatum, 1)
        ]

class AuditLogRecordResult(Sequence):
    sequenceElements = \
        [ Element('sequenceNumber', Unsigned, 0) # Unsigned64
        , Element('logRecord', AuditLogRecord, 1)
        ]

class AuditLogQueryParametersByTarget(Sequence):
    sequenceElements = \
        [ Element('targetDeviceIdentifier', ObjectIdentifier, 0)
        , Element('targetDeviceAddress', Address, 1, True)
        , Element('targetObjectIdentifier', ObjectIdentifier, 2, True)
        , Element('targetPropertyIdentifier', PropertyIdentifier, 3, True)
        , Element('targetArrayIndex', Unsigned, 4, True)
        , Element('targetPriority', Unsigned, 5, True)
        , Element('operations', AuditOperationFlags, 6, True)
        , Element('successfulActionsOnly', Boolean, 7)
        ]

class AuditLogQueryParametersBySource(Sequence):
    sequenceElements = \
        [ Element('sourceDeviceIdentifier', ObjectIdentifier, 0)
        , Element('sourceDeviceAddress', Address, 1, True)
        , Element('sourceObjectIdentifier', ObjectIdentifier, 2, True)
        , Element('operations', AuditOperationFlags, 3, True)
        , Element('successfulActionsOnly', Boolean, 4)
        ]

class AuditLogQueryParameters(Choice):
    choiceElements = \
        [ Element('byTarget', AuditLogQueryParametersByTarget, 0)
        , Element('bySource', AuditLogQueryParametersBySource, 1)
        ]

class AuthenticationFactor(Sequence):
    sequenceElements = \
        [ Element('formatType', AuthenticationFactorType, 0)
        , Element('formatClass', Unsigned, 1)
        , Element('value', OctetString, 2)
        ]

class AuthenticationFactorFormat(Sequence):
    sequenceElements = \
        [ Element('formatType', AuthenticationFactorType, 0)
        , Element('vendorId', Unsigned, 1, True)
        , Element('vendorFormat', Unsigned, 2, True)
        ]

class AuthenticationPolicyPolicy(Sequence):
    sequenceElements = \
        [ Element('credentialDataInput', DeviceObjectReference, 0)
        , Element('index', Unsigned, 1)
        ]

class AuthenticationPolicy(Sequence):
    sequenceElements = \
        [ Element('policy', SequenceOf(AuthenticationPolicyPolicy), 0)
        , Element('orderEnforced', Boolean, 1)
        , Element('timeout', Unsigned, 2)
        ]

class CalendarEntry(Choice):
    choiceElements = \
        [ Element('date', Date, 0)
        , Element('dateRange', DateRange, 1)
        , Element('weekNDay', WeekNDay, 2)
        ]

class ChannelValue(Choice):
    choiceElements = \
        [ Element('null', Null)
        , Element('real', Real)
        , Element('enumerated', Enumerated)
        , Element('unsigned', Unsigned)
        , Element('boolean', Boolean)
        , Element('integer', Integer)
        , Element('double', Double)
        , Element('time', Time)
        , Element('characterString', CharacterString)
        , Element('octetString', OctetString)
        , Element('bitString', BitString)
        , Element('date', Date)
        , Element('objectidentifier', ObjectIdentifier)
        , Element('lightingCommand', LightingCommand, 0)
        ]

class ClientCOV(Choice):
    choiceElements = \
        [ Element('realIncrement', Real)
        , Element('defaultIncrement', Null)
        ]

class COVMultipleSubscriptionListOfCOVReference(Sequence):
    sequenceElements = \
        [ Element('monitoredProperty', PropertyReference, 0)
        , Element('covIncrement', Real, 1, True)
        , Element('timestamped', Boolean, 2)
        ]

class COVMultipleSubscriptionList(Sequence):
    sequenceElements = \
        [ Element('monitoredObjectIdentifier', ObjectIdentifier, 0)
        , Element('listOfCOVReferences', SequenceOf(COVMultipleSubscriptionListOfCOVReference), 1)
        ]

class COVMultipleSubscription(Sequence):
    sequenceElements = \
        [ Element('recipient', RecipientProcess, 0)
        , Element('issueConfirmedNotifications', Boolean, 1)
        , Element('timeRemaining', Unsigned, 2)
        , Element('maxNotificationDelay', Unsigned, 3)
        , Element('listOfCOVSubscriptionSpecifications', SequenceOf(COVMultipleSubscriptionList), 4)
        ]

class COVSubscription(Sequence):
    sequenceElements = \
        [ Element('recipient', RecipientProcess, 0)
        , Element('monitoredPropertyReference', ObjectPropertyReference, 1)
        , Element('issueConfirmedNotifications', Boolean, 2)
        , Element('timeRemaining', Unsigned, 3)
        , Element('covIncrement', Real, 4, True)
        ]

class CredentialAuthenticationFactor(Sequence):
    sequenceElements = \
        [ Element('disable', AccessAuthenticationFactorDisable, 0)
        , Element('authenticationFactor', AuthenticationFactor, 1)
        ]

class DailySchedule(Sequence):
    sequenceElements = \
        [ Element('daySchedule', SequenceOf(TimeValue), 0)
        ]

class Destination(Sequence):
    sequenceElements = \
        [ Element('validDays', DaysOfWeek)
        , Element('fromTime', Time)
        , Element('toTime', Time)
        , Element('recipient', Recipient)
        , Element('processIdentifier', Unsigned)
        , Element('issueConfirmedNotifications', Boolean)
        , Element('transitions', EventTransitionBits)
        ]

class DeviceObjectPropertyValue(Sequence):
    sequenceElements = \
        [ Element('deviceIdentifier', ObjectIdentifier, 0)
        , Element('objectIdentifier', ObjectIdentifier, 1)
        , Element('propertyIdentifier', PropertyIdentifier, 2)
        , Element('arrayIndex', Unsigned, 3, True)
        , Element('value', Any, 4)
        ]

class EventNotificationSubscription(Sequence):
    sequenceElements = \
        [ Element('recipient', Recipient, 0)
        , Element('processIdentifier', Unsigned, 1)
        , Element('issueConfirmedNotifications', Boolean, 2)
        , Element('timeRemaining', Unsigned, 3)
        ]

class EventParameterChangeOfBitstring(Sequence):
    sequenceElements = \
        [ Element('timeDelay', Unsigned, 0)
        , Element('bitmask', BitString, 1)
        , Element('listOfBitstringValues', SequenceOf(BitString), 2)
        ]

class EventParameterChangeOfState(Sequence):
    sequenceElements = \
        [ Element('timeDelay', Unsigned, 0)
        , Element('listOfValues', SequenceOf(PropertyStates), 1)
        ]

class EventParameterChangeOfValueCOVCriteria(Choice):
    choiceElements = \
        [ Element('bitmask', BitString, 0)
        , Element('referencedPropertyIncrement', Real, 1)
        ]

class EventParameterChangeOfValue(Sequence):
    sequenceElements = \
        [ Element('timeDelay', Unsigned, 0)
        , Element('covCriteria', EventParameterChangeOfValueCOVCriteria, 1)
        ]

class EventParameterCommandFailure(Sequence):
    sequenceElements = \
        [ Element('timeDelay', Unsigned, 0)
        , Element('feedbackPropertyReference', DeviceObjectPropertyReference, 1)
        ]

class EventParameterFloatingLimit(Sequence):
    sequenceElements = \
        [ Element('timeDelay', Unsigned, 0)
        , Element('setpointReference', DeviceObjectPropertyReference, 1)
        , Element('lowDiffLimit', Real, 2)
        , Element('highDiffLimit', Real, 3)
        , Element('deadband', Real, 4)
        ]

class EventParameterOutOfRange(Sequence):
    sequenceElements = \
        [ Element('timeDelay', Unsigned, 0)
        , Element('lowLimit', Real, 1)
        , Element('highLimit', Real, 2)
        , Element('deadband', Real, 3)
        ]

class EventParameterChangeOfLifeSafety(Sequence):
    sequenceElements = \
        [ Element('timeDelay', Unsigned, 0)
        , Element('listOfLifeSafetyAlarmValues', SequenceOf(LifeSafetyState), 1)
        , Element('listOfAlarmValues', SequenceOf(LifeSafetyState), 2)
        , Element('modePropertyReference', DeviceObjectPropertyReference, 3)
        ]

class EventParameterExtendedParameters(Choice):
    choiceElements = \
        [ Element('null', Null, 0)
        , Element('real', Real, 1)
        , Element('integer', Unsigned, 2)
        , Element('boolean', Boolean, 3)
        , Element('double', Double, 4)
        , Element('octet', OctetString, 5)
        , Element('bitstring', BitString, 6)
        , Element('enum', Enumerated, 7)
        , Element('reference', DeviceObjectPropertyReference, 8)
        ]

class EventParameterExtended(Sequence):
    sequenceElements = \
        [ Element('vendorId', Unsigned, 0)
        , Element('extendedEventType', Unsigned, 1)
        , Element('parameters', SequenceOf(EventParameterExtendedParameters), 2)
        ]

class EventParameterBufferReady(Sequence):
    sequenceElements = \
        [ Element('notificationThreshold', Unsigned, 0)
        , Element('previousNotificationCount', Unsigned, 1)
        ]

class EventParameterUnsignedRange(Sequence):
    sequenceElements = \
        [ Element('timeDelay', Unsigned, 0)
        , Element('lowLimit', Unsigned, 1)
        , Element('highLimit', Unsigned, 2)
        ]

class EventParameterAccessEventAccessEvent(Sequence):
    sequenceElements = \
        [ Element('listOfAccessEvents', SequenceOf(AccessEvent), 0)
        , Element('accessEventTimeReference', DeviceObjectPropertyReference, 1)
        ]

class EventParameterAccessEvent(Sequence):
    sequenceElements = \
        [ Element('accessEvent', SequenceOf(EventParameterAccessEventAccessEvent), 0)
        ]

class EventParameterDoubleOutOfRange(Sequence):
    sequenceElements = \
        [ Element('timeDelay', Unsigned, 0)
        , Element('lowLimit', Double, 1)
        , Element('highLimit', Double, 2)
        , Element('deadband', Double, 3)
        ]

class EventParameterSignedOutOfRange(Sequence):
    sequenceElements = \
        [ Element('timeDelay', Unsigned, 0)
        , Element('lowLimit', Integer, 1)
        , Element('highLimit', Integer, 2)
        , Element('deadband', Unsigned, 3)
        ]

class EventParameterUnsignedOutOfRange(Sequence):
    sequenceElements = \
        [ Element('timeDelay', Unsigned, 0)
        , Element('lowLimit', Unsigned, 1)
        , Element('highLimit', Unsigned, 2)
        , Element('deadband', Unsigned, 3)
        ]

class EventParameterChangeOfCharacterString(Sequence):
    sequenceElements = \
        [ Element('timeDelay', Unsigned, 0)
        , Element('listOfAlarmValues', SequenceOf(CharacterString), 1)
        ]

class EventParameterChangeOfStatusFlags(Sequence):
    sequenceElements = \
        [ Element('timeDelay', Unsigned, 0)
        , Element('selectedFlags', StatusFlags, 1)
        ]

class EventParameter(Choice):
    choiceElements = \
        [ Element('changeOfBitstring', EventParameterChangeOfBitstring, 0)
        , Element('changeOfState', EventParameterChangeOfState, 1)
        , Element('changeOfValue', EventParameterChangeOfValue, 2)
        , Element('commandFailure', EventParameterCommandFailure, 3)
        , Element('floatingLimit', EventParameterFloatingLimit, 4)
        , Element('outOfRange', EventParameterOutOfRange, 5)
        , Element('changeOfLifesafety', EventParameterChangeOfLifeSafety, 8)
        , Element('extended', EventParameterExtended, 9)
        , Element('bufferReady', EventParameterBufferReady, 10)
        , Element('unsignedRange', EventParameterUnsignedRange, 11)
        , Element('accessEvent', EventParameterAccessEvent, 13)
        , Element('doubleOutOfRange', EventParameterDoubleOutOfRange, 14)
        , Element('signedOutOfRange', EventParameterSignedOutOfRange, 15)
        , Element('unsignedOutOfRange', EventParameterUnsignedOutOfRange, 16)
        , Element('changeOfCharacterstring', EventParameterChangeOfCharacterString, 17)
        , Element('changeOfStatusflags', EventParameterChangeOfStatusFlags, 18)
        ]

class FaultParameterCharacterString(Sequence):
    sequenceElements = \
        [ Element('listOfFaultValues', SequenceOf(CharacterString), 0)
        ]

class FaultParameterExtendedParameters(Choice):
    choiceElements = \
        [ Element('null', Null)
        , Element('real', Real)
        , Element('unsigned', Unsigned)
        , Element('boolean', Boolean)
        , Element('integer', Integer)
        , Element('double', Double)
        , Element('octet', OctetString)
        , Element('characterString', CharacterString)
        , Element('bitstring', BitString)
        , Element('enum', Enumerated)
        , Element('date', Date)
        , Element('time', Time)
        , Element('objectIdentifier', ObjectIdentifier)
        , Element('reference', DeviceObjectPropertyReference, 0)
        ]

class FaultParameterExtended(Sequence):
    sequenceElements = \
        [ Element('vendorId', Unsigned, 0)
        , Element('extendedFaultType', Unsigned, 1)
        , Element('parameters', SequenceOf(FaultParameterExtendedParameters), 2)
        ]

class FaultParameterLifeSafety(Sequence):
    sequenceElements = \
        [ Element('listOfFaultValues', SequenceOf(LifeSafetyState), 0)
        , Element('modePropertyReference', DeviceObjectPropertyReference, 1)
        ]

class FaultParameterState(Sequence):
    sequenceElements = \
        [ Element('listOfFaultValues', SequenceOf(PropertyStates), 0)
        ]

class FaultParameterStatusFlags(Sequence):
    sequenceElements = \
        [ Element('statusFlagsReference', DeviceObjectPropertyReference, 0)
        ]

class FaultParameter(Choice):
    choiceElements = \
        [ Element('none', Null, 0)
        , Element('faultCharacterString', FaultParameterCharacterString, 1)
        , Element('faultExtended', FaultParameterExtended, 2)
        , Element('faultLifeSafety', FaultParameterLifeSafety, 3)
        , Element('faultState', FaultParameterState, 4)
        , Element('faultStatusFlags', FaultParameterStatusFlags, 5)
        ]

class KeyIdentifier(Sequence):
    sequenceElements = \
        [ Element('algorithm', Unsigned, 0)
        , Element('keyId', Unsigned, 1)
        ]

class LogDataLogData(Choice):
    choiceElements = \
        [ Element('booleanValue', Boolean, 0)
        , Element('realValue', Real, 1)
        , Element('enumValue', Enumerated, 2)
        , Element('unsignedValue', Unsigned, 3)
        , Element('signedValue', Integer, 4)
        , Element('bitstringValue', BitString, 5)
        , Element('nullValue', Null, 6)
        , Element('failure', ErrorType, 7)
        , Element('anyValue', Any, 8)
        ]

class LogData(Choice):
    choiceElements = \
        [ Element('logStatus', LogStatus, 0)
        , Element('logData', SequenceOf(LogDataLogData), 1)
        , Element('timeChange', Real, 2)
        ]

class LogMultipleRecord(Sequence):
    sequenceElements = \
        [ Element('timestamp', DateTime, 0)
        , Element('logData', LogData, 1)
        ]

class LogRecordLogDatum(Choice):
    choiceElements = \
        [ Element('logStatus', LogStatus, 0)
        , Element('booleanValue', Boolean, 1)
        , Element('realValue', Real, 2)
        , Element('enumValue', Enumerated, 3)
        , Element('unsignedValue', Unsigned, 4)
        , Element('signedValue', Integer, 5)
        , Element('bitstringValue', BitString, 6)
        , Element('nullValue', Null, 7)
        , Element('failure', ErrorType, 8)
        , Element('timeChange', Real, 9)
        , Element('anyValue', Any, 10)
        ]

class LogRecord(Sequence):
    sequenceElements = \
        [ Element('timestamp', DateTime, 0)
        , Element('logDatum', LogRecordLogDatum, 1)
        , Element('statusFlags', StatusFlags, 2, True)
        ]

class NetworkSecurityPolicy(Sequence):
    sequenceElements = \
        [ Element('portId', Unsigned, 0)
        , Element('securityLevel', SecurityPolicy, 1)
        ]

class NotificationParametersChangeOfBitstring(Sequence):
    sequenceElements = \
        [ Element('referencedBitstring', BitString, 0)
        , Element('statusFlags', StatusFlags, 1)
        ]

class NotificationParametersChangeOfState(Sequence):
    sequenceElements = \
        [ Element('newState', PropertyStates, 0)
        , Element('statusFlags', StatusFlags, 1)
        ]

class NotificationParametersChangeOfValueNewValue(Choice):
    choiceElements = \
        [ Element('changedBits', BitString, 0)
        , Element('changedValue', Real, 1)
        ]

class NotificationParametersChangeOfValue(Sequence):
    sequenceElements = \
        [ Element('newValue', NotificationParametersChangeOfValueNewValue, 0)
        , Element('statusFlags', StatusFlags, 1)
        ]

class NotificationParametersCommandFailure(Sequence):
    sequenceElements = \
        [ Element('commandValue', Any, 0)
        , Element('statusFlags', StatusFlags, 1)
        , Element('feedbackValue', Any, 2)
        ]

class NotificationParametersFloatingLimit(Sequence):
    sequenceElements = \
        [ Element('referenceValue', Real, 0)
        , Element('statusFlags', StatusFlags, 1)
        , Element('setpointValue', Real, 2)
        , Element('errorLimit', Real, 3)
        ]

class NotificationParametersOutOfRange(Sequence):
    sequenceElements = \
        [ Element('exceedingValue', Real, 0)
        , Element('statusFlags', StatusFlags, 1)
        , Element('deadband', Real, 2)
        , Element('exceededLimit', Real, 3)
        ]

class NotificationParametersExtendedParametersType(Choice):
    choiceElements = \
        [ Element('null', Null)
        , Element('real', Real)
        , Element('integer', Unsigned)
        , Element('boolean', Boolean)
        , Element('double', Double)
        , Element('octet', OctetString)
        , Element('bitstring', BitString)
        , Element('enum', Enumerated)
        , Element('propertyValue', DeviceObjectPropertyValue)
        ]

class NotificationParametersExtended(Sequence):
    sequenceElements = \
        [ Element('vendorId', Unsigned, 0)
        , Element('extendedEventType', Unsigned, 1)
        , Element('parameters', NotificationParametersExtendedParametersType, 2)
        ]

class NotificationParametersBufferReady(Sequence):
    sequenceElements = \
        [ Element('bufferProperty', DeviceObjectPropertyReference, 0)
        , Element('previousNotification', Unsigned, 1)
        , Element('currentNotification', Unsigned, 2)
        ]

class NotificationParametersUnsignedRange(Sequence):
    sequenceElements = \
        [ Element('exceedingValue', Unsigned, 0)
        , Element('statusFlags', StatusFlags, 1)
        , Element('exceedingLimit', Unsigned, 2)
        ]

class NotificationParametersComplexEventType(Sequence):
    sequenceElements = \
        [ Element('complexEventType', PropertyValue, 0)
        ]

class NotificationParametersChangeOfLifeSafety(Sequence):
    sequenceElements = \
        [ Element('newState', LifeSafetyState, 0)
        , Element('newMode', LifeSafetyMode, 1)
        , Element('statusFlags',StatusFlags, 2)
        , Element('operationExpected', LifeSafetyOperation, 3)
        ]

class NotificationParametersAccessEventType(Sequence):
    sequenceElements = \
        [ Element('accessEvent', AccessEvent, 0)
        , Element('statusFlags', StatusFlags, 1)
        , Element('accessEventTag', Unsigned, 2)
        , Element('accessEventTime', TimeStamp, 3)
        , Element('accessCredential', DeviceObjectReference, 4)
        , Element('authenicationFactor', AuthenticationFactorType, 5, True)
        ]

class NotificationParametersDoubleOutOfRangeType(Sequence):
    sequenceElements = \
        [ Element('exceedingValue', Double, 0)
        , Element('statusFlags', StatusFlags, 1)
        , Element('deadband', Double, 2)
        , Element('exceededLimit', Double, 3)
        ]

class NotificationParametersSignedOutOfRangeType(Sequence):
    sequenceElements = \
        [ Element('exceedingValue', Integer, 0)
        , Element('statusFlags', StatusFlags, 1)
        , Element('deadband', Unsigned, 2)
        , Element('exceededLimit', Integer, 3)
        ]

class NotificationParametersUnsignedOutOfRangeType(Sequence):
    sequenceElements = \
        [ Element('exceedingValue', Unsigned, 0)
        , Element('statusFlags', StatusFlags, 1)
        , Element('deadband', Unsigned, 2)
        , Element('exceededLimit', Unsigned, 3)
        ]

class NotificationParametersChangeOfCharacterStringType(Sequence):
    sequenceElements = \
        [ Element('changedValue', CharacterString, 0)
        , Element('statusFlags', StatusFlags, 1)
        , Element('alarmValue', CharacterString, 2)
        ]

class NotificationParametersChangeOfStatusFlagsType(Sequence):
    sequenceElements = \
        [ Element('presentValue', CharacterString, 0)
        , Element('referencedFlags', StatusFlags, 1)
        ]

class NotificationParametersChangeOfReliabilityType(Sequence):
    sequenceElements = \
        [ Element('reliability', Reliability, 0)
        , Element('statusFlags', StatusFlags, 1)
        , Element('propertyValues', SequenceOf(PropertyValue), 2)
        ]

class NotificationParameters(Choice):
    choiceElements = \
        [ Element('changeOfBitstring', NotificationParametersChangeOfBitstring, 0)
        , Element('changeOfState', NotificationParametersChangeOfState, 1)
        , Element('changeOfValue', NotificationParametersChangeOfValue, 2)
        , Element('commandFailure', NotificationParametersCommandFailure, 3)
        , Element('floatingLimit', NotificationParametersFloatingLimit, 4)
        , Element('outOfRange', NotificationParametersOutOfRange, 5)
        , Element('complexEventType', NotificationParametersComplexEventType, 6)
        , Element('changeOfLifeSafety', NotificationParametersChangeOfLifeSafety, 8)
        , Element('extended', NotificationParametersExtended, 9)
        , Element('bufferReady', NotificationParametersBufferReady, 10)
        , Element('unsignedRange', NotificationParametersUnsignedRange, 11)
        , Element('accessEvent', NotificationParametersAccessEventType, 13)
        , Element('doubleOutOfRange', NotificationParametersDoubleOutOfRangeType, 14)
        , Element('signedOutOfRange', NotificationParametersSignedOutOfRangeType, 15)
        , Element('unsignedOutOfRange', NotificationParametersUnsignedOutOfRangeType, 16)
        , Element('changeOfCharacterString', NotificationParametersChangeOfCharacterStringType, 17)
        , Element('changeOfStatusFlags', NotificationParametersChangeOfStatusFlagsType, 18)
        , Element('changeOfReliability', NotificationParametersChangeOfReliabilityType, 19)
        ]

class ObjectPropertyValue(Sequence):
    sequenceElements = \
        [ Element('objectIdentifier', ObjectIdentifier, 0)
        , Element('propertyIdentifier', PropertyIdentifier, 1)
        , Element('propertyArrayIndex', Unsigned, 2, True)
        , Element('value', Any, 3)
        , Element('priority', Unsigned, 4, True)
        ]

class ObjectSelector(Choice):
    choiceElements = \
        [ Element('none', Null)
        , Element('object', ObjectIdentifier)
        , Element('objectType', ObjectType)
        ]

class OptionalCharacterString(Choice):
    choiceElements = \
        [ Element('null', Null)
        , Element('characterString', CharacterString)
        ]

class PortPermission(Sequence):
    sequenceElements = \
        [ Element('portId', Unsigned, 0)
        , Element('enabled', Boolean, 1)
        ]

class Prescale(Sequence):
    sequenceElements = \
        [ Element('multiplier', Unsigned, 0)
        , Element('moduloDivide', Unsigned, 1)
        ]

class PriorityValue(Choice):
    choiceElements = \
        [ Element('null', Null)
        , Element('real', Real)
        , Element('enumerated', Enumerated)
        , Element('unsigned', Unsigned)
        , Element('boolean', Boolean)
        , Element('integer', Integer)
        , Element('double', Double)
        , Element('time', Time)
        , Element('characterString', CharacterString)
        , Element('octetString', OctetString)
        , Element('bitString', BitString)
        , Element('date', Date)
        , Element('objectidentifier', ObjectIdentifier)
        , Element('constructedValue', Any, 0)
        , Element('datetime', DateTime, 1)
        ]

class PriorityArray(ArrayOf(
        PriorityValue, fixed_length=16, prototype=PriorityValue(null=()),
        )):
    pass

class PropertyAccessResultAccessResult(Choice):
    choiceElements = \
        [ Element('propertyValue', Any, 4)
        , Element('propertyAccessError', ErrorType, 5)
        ]

class PropertyAccessResult(Sequence):
    sequenceElements = \
        [ Element('objectIdentifier', ObjectIdentifier, 0)
        , Element('propertyIdentifier', PropertyIdentifier, 1)
        , Element('propertyArrayIndex', Unsigned, 2, True)
        , Element('deviceIdentifier', ObjectIdentifier, 3, True)
        , Element('accessResult', PropertyAccessResultAccessResult)
        ]

class Scale(Choice):
    choiceElements = \
        [ Element('floatScale', Real, 0)
        , Element('integerScale', Integer, 1)
        ]

class SecurityKeySet(Sequence):
    sequenceElements = \
        [ Element('keyRevision', Unsigned, 0)
        , Element('activationTime', DateTime, 1)
        , Element('expirationTime', DateTime, 2)
        , Element('keyIds', SequenceOf(KeyIdentifier), 3)
        ]

class ShedLevel(Choice):
    choiceElements = \
        [ Element('percent', Unsigned, 0)
        , Element('level', Unsigned, 1)
        , Element('amount', Real, 2)
        ]

class SetpointReference(Sequence):
    sequenceElements = \
        [ Element('setpointReference', ObjectPropertyReference, 0, True)
        ]

class SpecialEventPeriod(Choice):
    choiceElements = \
        [ Element('calendarEntry', CalendarEntry, 0)
        , Element('calendarReference', ObjectIdentifier, 1)
        ]

class SpecialEvent(Sequence):
    sequenceElements = \
        [ Element('period', SpecialEventPeriod)
        , Element('listOfTimeValues', SequenceOf(TimeValue), 2)
        , Element('eventPriority', Unsigned, 3)
        ]

class StageLimitValue(Sequence):
    sequenceElements = \
        [ Element('limit', Real)
        , Element('values', BitString)
        , Element('deadband', Real)
        ]

class ValueSource(Choice):
    choiceElements = \
        [ Element('none', Null, 0)
        , Element('object', DeviceObjectReference, 1)
        , Element('address', Address, 2)
        ]


class VTSession(Sequence):
    sequenceElements = \
        [ Element('localVtSessionID', Unsigned)
        , Element('remoteVtSessionID', Unsigned)
        , Element('remoteVtAddress', DeviceAddress)
        ]

