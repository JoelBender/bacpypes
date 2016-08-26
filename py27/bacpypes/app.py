#!/usr/bin/python

"""
Application Module
"""

from .debugging import bacpypes_debugging, DebugContents, ModuleLogger
from .comm import ApplicationServiceElement, bind

from .pdu import Address, LocalStation, RemoteStation

from .primitivedata import Atomic, Date, Null, ObjectIdentifier, Time, Unsigned
from .constructeddata import Any, Array, ArrayOf

from .appservice import StateMachineAccessPoint, ApplicationServiceAccessPoint
from .netservice import NetworkServiceAccessPoint, NetworkServiceElement
from .bvllservice import BIPSimple, BIPForeign, AnnexJCodec, UDPMultiplexer

from .object import Property, PropertyError, DeviceObject, \
    registered_object_types, register_object_type
from .apdu import ConfirmedRequestPDU, SimpleAckPDU, RejectPDU, RejectReason
from .apdu import IAmRequest, ReadPropertyACK, Error
from .errors import ExecutionError, \
    RejectException, UnrecognizedService, MissingRequiredParameter, \
        ParameterOutOfRange, \
    AbortException

# for computing protocol services supported
from .apdu import confirmed_request_types, unconfirmed_request_types, \
    ConfirmedServiceChoice, UnconfirmedServiceChoice
from .basetypes import ServicesSupported

from .apdu import \
    AtomicReadFileACK, \
        AtomicReadFileACKAccessMethodChoice, \
            AtomicReadFileACKAccessMethodRecordAccess, \
            AtomicReadFileACKAccessMethodStreamAccess, \
    AtomicWriteFileACK

# some debugging
_debug = 0
_log = ModuleLogger(globals())

#
#   DeviceInfo
#

@bacpypes_debugging
class DeviceInfo(DebugContents):

    _debug_contents = (
        'deviceIdentifier',
        'address',
        'maxApduLengthAccepted',
        'segmentationSupported',
        'vendorID',
        'maxNpduLength',
        'maxSegmentsAccepted',
        )

    def __init__(self):
        # this information is from an IAmRequest
        self.deviceIdentifier = None                    # device identifier
        self.address = None                             # LocalStation or RemoteStation
        self.maxApduLengthAccepted = 1024               # maximum APDU device will accept
        self.segmentationSupported = 'noSegmentation'   # normally no segmentation
        self.vendorID = None                            # vendor identifier

        self.maxNpduLength = 1497           # maximum we can send in transit
        self.maxSegmentsAccepted = None     # value for proposed/actual window size

#
#   DeviceInfoCache
#

@bacpypes_debugging
class DeviceInfoCache:

    def __init__(self):
        if _debug: DeviceInfoCache._debug("__init__")

        # empty cache
        self.cache = {}

    def has_device_info(self, key):
        """Return true iff cache has information about the device."""
        if _debug: DeviceInfoCache._debug("has_device_info %r", key)

        return key in self.cache

    def add_device_info(self, apdu):
        """Create a device information record based on the contents of an
        IAmRequest and put it in the cache."""
        if _debug: DeviceInfoCache._debug("add_device_info %r", apdu)

        # get the existing cache record by identifier
        info = self.get_device_info(apdu.iAmDeviceIdentifier[1])
        if _debug: DeviceInfoCache._debug("    - info: %r", info)

        # update existing record
        if info:
            if (info.address == apdu.pduSource):
                return

            info.address = apdu.pduSource
        else:
            # get the existing record by address (creates a new record)
            info = self.get_device_info(apdu.pduSource)
            if _debug: DeviceInfoCache._debug("    - info: %r", info)

            info.deviceIdentifier = apdu.iAmDeviceIdentifier[1]

        # update the rest of the values
        info.maxApduLengthAccepted = apdu.maxAPDULengthAccepted
        info.segmentationSupported = apdu.segmentationSupported
        info.vendorID = apdu.vendorID

        # say this is an updated record
        self.update_device_info(info)

    def get_device_info(self, key):
        """Return the known information about the device.  If the key is the
        address of an unknown device, build a generic device information record
        add put it in the cache."""
        if _debug: DeviceInfoCache._debug("get_device_info %r", key)

        if isinstance(key, int):
            current_info = self.cache.get(key, None)

        elif not isinstance(key, Address):
            raise TypeError("key must be integer or an address")

        elif key.addrType not in (Address.localStationAddr, Address.remoteStationAddr):
            raise TypeError("address must be a local or remote station")

        else:
            current_info = self.cache.get(key, None)
            if not current_info:
                current_info = DeviceInfo()
                current_info.address = key
                current_info._cache_keys = (None, key)

                self.cache[key] = current_info

        if _debug: DeviceInfoCache._debug("    - current_info: %r", current_info)

        return current_info

    def update_device_info(self, info):
        """The application has updated one or more fields in the device
        information record and the cache needs to be updated to reflect the
        changes.  If this is a cached version of a persistent record then this 
        is the opportunity to update the database."""
        if _debug: DeviceInfoCache._debug("update_device_info %r", info)

        cache_id, cache_address = info._cache_keys

        if (cache_id is not None) and (info.deviceIdentifier != cache_id):
            if _debug: DeviceInfoCache._debug("    - device identifier updated")

            # remove the old reference, add the new one
            del self.cache[cache_id]
            self.cache[info.deviceIdentifier] = info

            cache_id = info.deviceIdentifier

        if (cache_address is not None) and (info.address != cache_address):
            if _debug: DeviceInfoCache._debug("    - device address updated")

            # remove the old reference, add the new one
            del self.cache[cache_address]
            self.cache[info.address] = info

            cache_address = info.address

        # update the keys
        info._cache_keys = (cache_id, cache_address)

    def release_device_info(self, info):
        """This function is called by the segmentation state machine when it
        has finished with the device information."""
        if _debug: DeviceInfoCache._debug("release_device_info %r", info)

        cache_id, cache_address = info._cache_keys
        if cache_id is not None:
            del self.cache[cache_id]
        if cache_address is not None:
            del self.cache[cache_address]

#
#   CurrentDateProperty
#

class CurrentDateProperty(Property):

    def __init__(self, identifier):
        Property.__init__(self, identifier, Date, default=None, optional=True, mutable=False)

    def ReadProperty(self, obj, arrayIndex=None):
        # access an array
        if arrayIndex is not None:
            raise TypeError("{0} is unsubscriptable".format(self.identifier))

        # get the value
        now = Date()
        now.now()
        return now.value

    def WriteProperty(self, obj, value, arrayIndex=None, priority=None):
        raise ExecutionError(errorClass='property', errorCode='writeAccessDenied')

#
#   CurrentTimeProperty
#

class CurrentTimeProperty(Property):

    def __init__(self, identifier):
        Property.__init__(self, identifier, Time, default=None, optional=True, mutable=False)

    def ReadProperty(self, obj, arrayIndex=None):
        # access an array
        if arrayIndex is not None:
            raise TypeError("{0} is unsubscriptable".format(self.identifier))

        # get the value
        now = Time()
        now.now()
        return now.value

    def WriteProperty(self, obj, value, arrayIndex=None, priority=None):
        raise ExecutionError(errorClass='property', errorCode='writeAccessDenied')

#
#   LocalDeviceObject
#

@bacpypes_debugging
class LocalDeviceObject(DeviceObject):

    properties = \
        [ CurrentTimeProperty('localTime')
        , CurrentDateProperty('localDate')
        ]

    defaultProperties = \
        { 'maxApduLengthAccepted': 1024
        , 'segmentationSupported': 'segmentedBoth'
        , 'maxSegmentsAccepted': 16
        , 'apduSegmentTimeout': 5000
        , 'apduTimeout': 3000
        , 'numberOfApduRetries': 3
        }

    def __init__(self, **kwargs):
        if _debug: LocalDeviceObject._debug("__init__ %r", kwargs)

        # fill in default property values not in kwargs
        for attr, value in LocalDeviceObject.defaultProperties.items():
            if attr not in kwargs:
                kwargs[attr] = value

        # check for registration
        if self.__class__ not in registered_object_types.values():
            if 'vendorIdentifier' not in kwargs:
                raise RuntimeError("vendorIdentifier required to auto-register the LocalDeviceObject class")
            register_object_type(self.__class__, vendor_id=kwargs['vendorIdentifier'])

        # check for local time
        if 'localDate' in kwargs:
            raise RuntimeError("localDate is provided by LocalDeviceObject and cannot be overridden")
        if 'localTime' in kwargs:
            raise RuntimeError("localTime is provided by LocalDeviceObject and cannot be overridden")

        # check for a minimum value
        if kwargs['maxApduLengthAccepted'] < 50:
            raise ValueError("invalid max APDU length accepted")

        # dump the updated attributes
        if _debug: LocalDeviceObject._debug("    - updated kwargs: %r", kwargs)

        # proceed as usual
        DeviceObject.__init__(self, **kwargs)

        # create a default implementation of an object list for local devices.
        # If it is specified in the kwargs, that overrides this default.
        if ('objectList' not in kwargs):
            self.objectList = ArrayOf(ObjectIdentifier)([self.objectIdentifier])

            # if the object has a property list and one wasn't provided
            # in the kwargs, then it was created by default and the objectList
            # property should be included
            if ('propertyList' not in kwargs) and self.propertyList:
                # make sure it's not already there
                if 'objectList' not in self.propertyList:
                    self.propertyList.append('objectList')

#
#   Application
#

@bacpypes_debugging
class Application(ApplicationServiceElement):

    def __init__(self, localDevice, localAddress, deviceInfoCache=None, aseID=None):
        if _debug: Application._debug("__init__ %r %r deviceInfoCache=%r aseID=%r", localDevice, localAddress, deviceInfoCache, aseID)
        ApplicationServiceElement.__init__(self, aseID)

        # keep track of the local device
        self.localDevice = localDevice

        # use the provided cache or make a default one
        if deviceInfoCache:
            self.deviceInfoCache = deviceInfoCache
        else:
            self.deviceInfoCache = DeviceInfoCache()

        # bind the device object to this application
        localDevice._app = self

        # allow the address to be cast to the correct type
        if isinstance(localAddress, Address):
            self.localAddress = localAddress
        else:
            self.localAddress = Address(localAddress)

        # local objects by ID and name
        self.objectName = {localDevice.objectName:localDevice}
        self.objectIdentifier = {localDevice.objectIdentifier:localDevice}

    def add_object(self, obj):
        """Add an object to the local collection."""
        if _debug: Application._debug("add_object %r", obj)

        # extract the object name and identifier
        object_name = obj.objectName
        if not object_name:
            raise RuntimeError("object name required")
        object_identifier = obj.objectIdentifier
        if not object_identifier:
            raise RuntimeError("object identifier required")

        # assuming the object identifier is well formed, check the instance number
        if (object_identifier[1] >= ObjectIdentifier.maximum_instance_number):
            raise RuntimeError("invalid object identifier")

        # make sure it hasn't already been defined
        if object_name in self.objectName:
            raise RuntimeError("already an object with name {0!r}".format(object_name))
        if object_identifier in self.objectIdentifier:
            raise RuntimeError("already an object with identifier {0!r}".format(object_identifier))

        # now put it in local dictionaries
        self.objectName[object_name] = obj
        self.objectIdentifier[object_identifier] = obj

        # append the new object's identifier to the device's object list
        self.localDevice.objectList.append(object_identifier)

        # let the object know which application stack it belongs to
        obj._app = self

    def delete_object(self, obj):
        """Add an object to the local collection."""
        if _debug: Application._debug("delete_object %r", obj)

        # extract the object name and identifier
        object_name = obj.objectName
        object_identifier = obj.objectIdentifier

        # delete it from the application
        del self.objectName[object_name]
        del self.objectIdentifier[object_identifier]

        # remove the object's identifier from the device's object list
        indx = self.localDevice.objectList.index(object_identifier)
        del self.localDevice.objectList[indx]

        # make sure the object knows it's detached from an application
        obj._app = None

    def get_object_id(self, objid):
        """Return a local object or None."""
        return self.objectIdentifier.get(objid, None)

    def get_object_name(self, objname):
        """Return a local object or None."""
        return self.objectName.get(objname, None)

    def iter_objects(self):
        """Iterate over the objects."""
        return iter(self.objectIdentifier.values())

    def get_services_supported(self):
        """Return a ServicesSupported bit string based in introspection, look
        for helper methods that match confirmed and unconfirmed services."""
        if _debug: Application._debug("get_services_supported")

        services_supported = ServicesSupported()

        # look through the confirmed services
        for service_choice, service_request_class in confirmed_request_types.items():
            service_helper = "do_" + service_request_class.__name__
            if hasattr(self, service_helper):
                service_supported = ConfirmedServiceChoice._xlate_table[service_choice]
                services_supported[service_supported] = 1

        # look through the unconfirmed services
        for service_choice, service_request_class in unconfirmed_request_types.items():
            service_helper = "do_" + service_request_class.__name__
            if hasattr(self, service_helper):
                service_supported = UnconfirmedServiceChoice._xlate_table[service_choice]
                services_supported[service_supported] = 1

        # return the bit list
        return services_supported

    #-----

    def indication(self, apdu):
        if _debug: Application._debug("indication %r", apdu)

        # get a helper function
        helperName = "do_" + apdu.__class__.__name__
        helperFn = getattr(self, helperName, None)
        if _debug: Application._debug("    - helperFn: %r", helperFn)

        # send back a reject for unrecognized services
        if not helperFn:
            if isinstance(apdu, ConfirmedRequestPDU):
                raise UnrecognizedService("no function %s" % (helperName,))
            return

        # pass the apdu on to the helper function
        try:
            helperFn(apdu)
        except RejectException as err:
            if _debug: Application._debug("    - reject exception: %r", err)
            raise
        except AbortException as err:
            if _debug: Application._debug("    - abort exception: %r", err)
            raise
        except ExecutionError as err:
            if _debug: Application._debug("    - execution error: %r", err)

            # send back an error
            if isinstance(apdu, ConfirmedRequestPDU):
                resp = Error(errorClass=err.errorClass, errorCode=err.errorCode, context=apdu)
                self.response(resp)

        except Exception as err:
            Application._exception("exception: %r", err)

            # send back an error
            if isinstance(apdu, ConfirmedRequestPDU):
                resp = Error(errorClass='device', errorCode='operationalProblem', context=apdu)
                self.response(resp)

    def do_WhoIsRequest(self, apdu):
        """Respond to a Who-Is request."""
        if _debug: Application._debug("do_WhoIsRequest %r", apdu)

        # extract the parameters
        low_limit = apdu.deviceInstanceRangeLowLimit
        high_limit = apdu.deviceInstanceRangeHighLimit

        # check for consistent parameters
        if (low_limit is not None):
            if (high_limit is None):
                raise MissingRequiredParameter("deviceInstanceRangeHighLimit required")
            if (low_limit < 0) or (low_limit > 4194303):
                raise ParameterOutOfRange("deviceInstanceRangeLowLimit out of range")
        if (high_limit is not None):
            if (low_limit is None):
                raise MissingRequiredParameter("deviceInstanceRangeLowLimit required")
            if (high_limit < 0) or (high_limit > 4194303):
                raise ParameterOutOfRange("deviceInstanceRangeHighLimit out of range")

        # see we should respond
        if (low_limit is not None):
            if (self.localDevice.objectIdentifier[1] < low_limit):
                return
        if (high_limit is not None):
            if (self.localDevice.objectIdentifier[1] > high_limit):
                return

        # create a I-Am "response" back to the source
        iAm = IAmRequest()
        iAm.pduDestination = apdu.pduSource
        iAm.iAmDeviceIdentifier = self.localDevice.objectIdentifier
        iAm.maxAPDULengthAccepted = self.localDevice.maxApduLengthAccepted
        iAm.segmentationSupported = self.localDevice.segmentationSupported
        iAm.vendorID = self.localDevice.vendorIdentifier
        if _debug: Application._debug("    - iAm: %r", iAm)

        # away it goes
        self.request(iAm)

    def do_IAmRequest(self, apdu):
        """Respond to an I-Am request."""
        if _debug: Application._debug("do_IAmRequest %r", apdu)

    def do_ReadPropertyRequest(self, apdu):
        """Return the value of some property of one of our objects."""
        if _debug: Application._debug("do_ReadPropertyRequest %r", apdu)

        # extract the object identifier
        objId = apdu.objectIdentifier

        # check for wildcard
        if (objId == ('device', 4194303)):
            if _debug: Application._debug("    - wildcard device identifier")
            objId = self.localDevice.objectIdentifier

        # get the object
        obj = self.get_object_id(objId)
        if _debug: Application._debug("    - object: %r", obj)

        if not obj:
            resp = Error(errorClass='object', errorCode='unknownObject', context=apdu)
        else:
            try:
                # get the datatype
                datatype = obj.get_datatype(apdu.propertyIdentifier)
                if _debug: Application._debug("    - datatype: %r", datatype)

                # get the value
                value = obj.ReadProperty(apdu.propertyIdentifier, apdu.propertyArrayIndex)
                if _debug: Application._debug("    - value: %r", value)
                if value is None:
                    raise PropertyError(apdu.propertyIdentifier)

                # change atomic values into something encodeable
                if issubclass(datatype, Atomic):
                    value = datatype(value)
                elif issubclass(datatype, Array) and (apdu.propertyArrayIndex is not None):
                    if apdu.propertyArrayIndex == 0:
                        value = Unsigned(value)
                    elif issubclass(datatype.subtype, Atomic):
                        value = datatype.subtype(value)
                    elif not isinstance(value, datatype.subtype):
                        raise TypeError("invalid result datatype, expecting {0} and got {1}" \
                            .format(datatype.subtype.__name__, type(value).__name__))
                elif not isinstance(value, datatype):
                    raise TypeError("invalid result datatype, expecting {0} and got {1}" \
                        .format(datatype.__name__, type(value).__name__))
                if _debug: Application._debug("    - encodeable value: %r", value)

                # this is a ReadProperty ack
                resp = ReadPropertyACK(context=apdu)
                resp.objectIdentifier = objId
                resp.propertyIdentifier = apdu.propertyIdentifier
                resp.propertyArrayIndex = apdu.propertyArrayIndex

                # save the result in the property value
                resp.propertyValue = Any()
                resp.propertyValue.cast_in(value)

            except PropertyError:
                resp = Error(errorClass='object', errorCode='unknownProperty', context=apdu)
        if _debug: Application._debug("    - resp: %r", resp)

        # return the result
        self.response(resp)

    def do_WritePropertyRequest(self, apdu):
        """Change the value of some property of one of our objects."""
        if _debug: Application._debug("do_WritePropertyRequest %r", apdu)

        # get the object
        obj = self.get_object_id(apdu.objectIdentifier)
        if _debug: Application._debug("    - object: %r", obj)

        if not obj:
            resp = Error(errorClass='object', errorCode='unknownObject', context=apdu)
        else:
            try:
                # check if the property exists
                if obj.ReadProperty(apdu.propertyIdentifier, apdu.propertyArrayIndex) is None:
                    raise PropertyError(apdu.propertyIdentifier)

                # get the datatype, special case for null
                if apdu.propertyValue.is_application_class_null():
                    datatype = Null
                else:
                    datatype = obj.get_datatype(apdu.propertyIdentifier)
                if _debug: Application._debug("    - datatype: %r", datatype)

                # special case for array parts, others are managed by cast_out
                if issubclass(datatype, Array) and (apdu.propertyArrayIndex is not None):
                    if apdu.propertyArrayIndex == 0:
                        value = apdu.propertyValue.cast_out(Unsigned)
                    else:
                        value = apdu.propertyValue.cast_out(datatype.subtype)
                else:
                    value = apdu.propertyValue.cast_out(datatype)
                if _debug: Application._debug("    - value: %r", value)

                # change the value
                value = obj.WriteProperty(apdu.propertyIdentifier, value, apdu.propertyArrayIndex, apdu.priority)

                # success
                resp = SimpleAckPDU(context=apdu)

            except PropertyError:
                resp = Error(errorClass='object', errorCode='unknownProperty', context=apdu)
        if _debug: Application._debug("    - resp: %r", resp)

        # return the result
        self.response(resp)

    def do_AtomicReadFileRequest(self, apdu):
        """Return one of our records."""
        if _debug: Application._debug("do_AtomicReadFileRequest %r", apdu)

        if (apdu.fileIdentifier[0] != 'file'):
            resp = Error(errorClass='services', errorCode='inconsistentObjectType', context=apdu)
            if _debug: Application._debug("    - error resp: %r", resp)
            self.response(resp)
            return

        # get the object
        obj = self.get_object_id(apdu.fileIdentifier)
        if _debug: Application._debug("    - object: %r", obj)

        if not obj:
            resp = Error(errorClass='object', errorCode='unknownObject', context=apdu)
        elif apdu.accessMethod.recordAccess:
            # check against the object
            if obj.fileAccessMethod != 'recordAccess':
                resp = Error(errorClass='services',
                    errorCode='invalidFileAccessMethod',
                    context=apdu
                    )
            ### verify start is valid - double check this (empty files?)
            elif (apdu.accessMethod.recordAccess.fileStartRecord < 0) or \
                    (apdu.accessMethod.recordAccess.fileStartRecord >= len(obj)):
                resp = Error(errorClass='services',
                    errorCode='invalidFileStartPosition',
                    context=apdu
                    )
            else:
                # pass along to the object
                end_of_file, record_data = obj.ReadFile(
                    apdu.accessMethod.recordAccess.fileStartRecord,
                    apdu.accessMethod.recordAccess.requestedRecordCount,
                    )
                if _debug: Application._debug("    - record_data: %r", record_data)

                # this is an ack
                resp = AtomicReadFileACK(context=apdu,
                    endOfFile=end_of_file,
                    accessMethod=AtomicReadFileACKAccessMethodChoice(
                        recordAccess=AtomicReadFileACKAccessMethodRecordAccess(
                            fileStartRecord=apdu.accessMethod.recordAccess.fileStartRecord,
                            returnedRecordCount=len(record_data),
                            fileRecordData=record_data,
                            ),
                        ),
                    )

        elif apdu.accessMethod.streamAccess:
            # check against the object
            if obj.fileAccessMethod != 'streamAccess':
                resp = Error(errorClass='services',
                    errorCode='invalidFileAccessMethod',
                    context=apdu
                    )
            ### verify start is valid - double check this (empty files?)
            elif (apdu.accessMethod.streamAccess.fileStartPosition < 0) or \
                    (apdu.accessMethod.streamAccess.fileStartPosition >= len(obj)):
                resp = Error(errorClass='services',
                    errorCode='invalidFileStartPosition',
                    context=apdu
                    )
            else:
                # pass along to the object
                end_of_file, record_data = obj.ReadFile(
                    apdu.accessMethod.streamAccess.fileStartPosition,
                    apdu.accessMethod.streamAccess.requestedOctetCount,
                    )
                if _debug: Application._debug("    - record_data: %r", record_data)

                # this is an ack
                resp = AtomicReadFileACK(context=apdu,
                    endOfFile=end_of_file,
                    accessMethod=AtomicReadFileACKAccessMethodChoice(
                        streamAccess=AtomicReadFileACKAccessMethodStreamAccess(
                            fileStartPosition=apdu.accessMethod.streamAccess.fileStartPosition,
                            fileData=record_data,
                            ),
                        ),
                    )

        if _debug: Application._debug("    - resp: %r", resp)

        # return the result
        self.response(resp)

    def do_AtomicWriteFileRequest(self, apdu):
        """Return one of our records."""
        if _debug: Application._debug("do_AtomicWriteFileRequest %r", apdu)

        if (apdu.fileIdentifier[0] != 'file'):
            resp = Error(errorClass='services', errorCode='inconsistentObjectType', context=apdu)
            if _debug: Application._debug("    - error resp: %r", resp)
            self.response(resp)
            return

        # get the object
        obj = self.get_object_id(apdu.fileIdentifier)
        if _debug: Application._debug("    - object: %r", obj)

        if not obj:
            resp = Error(errorClass='object', errorCode='unknownObject', context=apdu)
        elif apdu.accessMethod.recordAccess:
            # check against the object
            if obj.fileAccessMethod != 'recordAccess':
                resp = Error(errorClass='services',
                    errorCode='invalidFileAccessMethod',
                    context=apdu
                    )
                if _debug: Application._debug("    - error resp: %r", resp)
                self.response(resp)
                return

            # check for read-only
            if obj.readOnly:
                resp = Error(errorClass='services',
                    errorCode='fileAccessDenied',
                    context=apdu
                    )
                if _debug: Application._debug("    - error resp: %r", resp)
                self.response(resp)
                return

            # pass along to the object
            start_record = obj.WriteFile(
                apdu.accessMethod.recordAccess.fileStartRecord,
                apdu.accessMethod.recordAccess.recordCount,
                apdu.accessMethod.recordAccess.fileRecordData,
                )
            if _debug: Application._debug("    - start_record: %r", start_record)

            # this is an ack
            resp = AtomicWriteFileACK(context=apdu,
                fileStartRecord=start_record,
                )

        elif apdu.accessMethod.streamAccess:
            # check against the object
            if obj.fileAccessMethod != 'streamAccess':
                resp = Error(errorClass='services',
                    errorCode='invalidFileAccessMethod',
                    context=apdu
                    )
                if _debug: Application._debug("    - error resp: %r", resp)
                self.response(resp)
                return

            # check for read-only
            if obj.readOnly:
                resp = Error(errorClass='services',
                    errorCode='fileAccessDenied',
                    context=apdu
                    )
                if _debug: Application._debug("    - error resp: %r", resp)
                self.response(resp)
                return

            # pass along to the object
            start_position = obj.WriteFile(
                apdu.accessMethod.streamAccess.fileStartPosition,
                apdu.accessMethod.streamAccess.fileData,
                )
            if _debug: Application._debug("    - start_position: %r", start_position)

            # this is an ack
            resp = AtomicWriteFileACK(context=apdu,
                fileStartPosition=start_position,
                )

        if _debug: Application._debug("    - resp: %r", resp)

        # return the result
        self.response(resp)

#
#   BIPSimpleApplication
#

@bacpypes_debugging
class BIPSimpleApplication(Application):

    def __init__(self, localDevice, localAddress, deviceInfoCache=None, aseID=None):
        if _debug: BIPSimpleApplication._debug("__init__ %r %r deviceInfoCache=%r aseID=%r", localDevice, localAddress, deviceInfoCache, aseID)
        Application.__init__(self, localDevice, localAddress, deviceInfoCache, aseID)

        # include a application decoder
        self.asap = ApplicationServiceAccessPoint()

        # pass the device object to the state machine access point so it
        # can know if it should support segmentation
        self.smap = StateMachineAccessPoint(localDevice)

        # the segmentation state machines need access to the same device
        # information cache as the application
        self.smap.deviceInfoCache = self.deviceInfoCache

        # a network service access point will be needed
        self.nsap = NetworkServiceAccessPoint()

        # give the NSAP a generic network layer service element
        self.nse = NetworkServiceElement()
        bind(self.nse, self.nsap)

        # bind the top layers
        bind(self, self.asap, self.smap, self.nsap)

        # create a generic BIP stack, bound to the Annex J server
        # on the UDP multiplexer
        self.bip = BIPSimple()
        self.annexj = AnnexJCodec()
        self.mux = UDPMultiplexer(self.localAddress)

        # bind the bottom layers
        bind(self.bip, self.annexj, self.mux.annexJ)

        # bind the BIP stack to the network, no network number
        self.nsap.bind(self.bip)

#
#   BIPForeignApplication
#

@bacpypes_debugging
class BIPForeignApplication(Application):

    def __init__(self, localDevice, localAddress, bbmdAddress, bbmdTTL, aseID=None):
        if _debug: BIPForeignApplication._debug("__init__ %r %r %r %r aseID=%r", localDevice, localAddress, bbmdAddress, bbmdTTL, aseID)
        Application.__init__(self, localDevice, localAddress, aseID)

        # include a application decoder
        self.asap = ApplicationServiceAccessPoint()

        # pass the device object to the state machine access point so it
        # can know if it should support segmentation
        self.smap = StateMachineAccessPoint(localDevice)

        # a network service access point will be needed
        self.nsap = NetworkServiceAccessPoint()

        # give the NSAP a generic network layer service element
        self.nse = NetworkServiceElement()
        bind(self.nse, self.nsap)

        # bind the top layers
        bind(self, self.asap, self.smap, self.nsap)

        # create a generic BIP stack, bound to the Annex J server
        # on the UDP multiplexer
        self.bip = BIPForeign(bbmdAddress, bbmdTTL)
        self.annexj = AnnexJCodec()
        self.mux = UDPMultiplexer(self.localAddress, noBroadcast=True)

        # bind the bottom layers
        bind(self.bip, self.annexj, self.mux.annexJ)

        # bind the NSAP to the stack, no network number
        self.nsap.bind(self.bip)

#
#   BIPNetworkApplication
#

@bacpypes_debugging
class BIPNetworkApplication(NetworkServiceElement):

    def __init__(self, localAddress, eID=None):
        if _debug: BIPNetworkApplication._debug("__init__ %r eID=%r", localAddress, eID)
        NetworkServiceElement.__init__(self, eID)

        # allow the address to be cast to the correct type
        if isinstance(localAddress, Address):
            self.localAddress = localAddress
        else:
            self.localAddress = Address(localAddress)

        # a network service access point will be needed
        self.nsap = NetworkServiceAccessPoint()

        # give the NSAP a generic network layer service element
        bind(self, self.nsap)

        # create a generic BIP stack, bound to the Annex J server
        # on the UDP multiplexer
        self.bip = BIPSimple()
        self.annexj = AnnexJCodec()
        self.mux = UDPMultiplexer(self.localAddress)

        # bind the bottom layers
        bind(self.bip, self.annexj, self.mux.annexJ)

        # bind the NSAP to the stack, no network number
        self.nsap.bind(self.bip)

