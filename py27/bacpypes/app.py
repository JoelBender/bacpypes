#!/usr/bin/python

"""
Application Module
"""

from .debugging import ModuleLogger, Logging
from .comm import ApplicationServiceElement, bind

from .pdu import Address

from .primitivedata import Atomic, Date, Null, ObjectIdentifier, Time, Unsigned
from .constructeddata import Any, Array, ArrayOf

from .appservice import StateMachineAccessPoint, ApplicationServiceAccessPoint
from .netservice import NetworkServiceAccessPoint, NetworkServiceElement
from .bvllservice import BIPSimple, BIPForeign, AnnexJCodec, UDPMultiplexer

from .object import Property, PropertyError, DeviceObject, \
    registered_object_types, register_object_type
from .apdu import ConfirmedRequestPDU, SimpleAckPDU, RejectPDU, RejectReason
from .apdu import IAmRequest, ReadPropertyACK, Error
from .errors import ExecutionError

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

class LocalDeviceObject(DeviceObject, Logging):

    properties = \
        [ CurrentTimeProperty('localTime')
        , CurrentDateProperty('localDate')
        ]

    defaultProperties = \
        { 'maxApduLengthAccepted': 1024
        , 'segmentationSupported': 'segmentedBoth'
        , 'maxSegmentsAccepted': 16
        , 'apduSegmentTimeout': 20000
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

class Application(ApplicationServiceElement, Logging):

    def __init__(self, localDevice, localAddress, aseID=None):
        if _debug: Application._debug("__init__ %r %r aseID=%r", localDevice, localAddress, aseID)
        ApplicationServiceElement.__init__(self, aseID)

        # keep track of the local device
        self.localDevice = localDevice

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
                response = RejectPDU( apdu.apduInvokeID, RejectReason.UNRECOGNIZEDSERVICE, context=apdu)
                self.response(response)
            return

        # pass the apdu on to the helper function
        try:
            helperFn(apdu)

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

        # may be a restriction
        if (apdu.deviceInstanceRangeLowLimit is not None) and \
                (apdu.deviceInstanceRangeHighLimit is not None):
            if (self.localDevice.objectIdentifier[1] < apdu.deviceInstanceRangeLowLimit):
                return
            if (self.localDevice.objectIdentifier[1] > apdu.deviceInstanceRangeHighLimit):
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

class BIPSimpleApplication(Application, Logging):

    def __init__(self, localDevice, localAddress, aseID=None):
        if _debug: BIPSimpleApplication._debug("__init__ %r %r aseID=%r", localDevice, localAddress, aseID)
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

class BIPForeignApplication(Application, Logging):

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

class BIPNetworkApplication(NetworkServiceElement, Logging):

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

