.. BACpypes app module

.. module:: app

Application
===========

This is a long line of text.

Device Information
------------------

The device information objects and associated cache are used to assist with
the following:

* Device-address-binding, the close associate between the device identifier
  for a device and its network address
* Construction of confirmed services to determine if a device can accept
  segmented requests and/or responses and the maximum size of an APDU
* The vendor of the device to know what additional vendor specific objects,
  properties, and other datatypes are available


.. class:: DeviceInfo

    This is a long line of text.

    .. attribute:: deviceIdentifier

        The device instance number associated with the device.

    .. attribute:: address

        The :class:`pdu.LocalStation` or :class:`pdu.RemoteStation` associated
        with the device.

    .. attribute:: maxApduLengthAccepted

        The maximum APDU length acccepted, which has the same value as the
        property of the :class:`object.DeviceObject` of the device.  This is
        typically initialized with the parameter with the same name from the
        :class:`apdu.IAmRequest`.

    .. attribute:: segmentationSupported

        The enumeration value :class:`basetypes.Segmentation` that describes
        the segmentation supported by the device; sending, receiving, both,
        or no segmentation supported.

    .. attribute:: vendorID

        The vendor identifier of the device.

    .. attribute:: maxNpduLength

        The maximum length of an NPDU permitted by the links used by the local,
        remote, and intervening networks.

    .. attribute:: maxSegmentsAccepted

        The maximum number of segments of an APDU that this device will accept.

    .. method:: __init__()

        Initialize a :class:`DeviceInfo` object using the default values that
        are typical for BACnet devices.

.. class:: DeviceInfoCache

    An instance of this class is used to manage the cache of device information
    on behalf of the application.  The information may come from interrogating
    the device as it presents itself on the network or from a database, or
    some combination of the two.

    The default implementation is to only use information from the network and
    provide some reasonable defaults when information isn't available.  The
    :class:`Application` is provided a reference to an instance of this class
    or a derived class, and multiple application instances may share a cache,
    if that's appropriate.

    .. attribute:: cache

        This is a private dictionary for use by the class or derived class
        methods.  The default implementation uses a mix of device identifiers,
        addresses, or both to reference :class:`DeviceInfo` objects.

    .. method:: has_device_info(key)

        :param key: a device object identifier, a :class:`pdu.LocalStation` or a 
            :class:`RemoteStation` address.

        Return true if there is a :class:`DeviceInfo` instance in the cache.

    .. method:: add_device_info(apdu)

        :param IAmRequest apdu: an IAmRequest

        This function is called by an application when it receives an
        :class:`apdu.IAmRequest` and it wants to cache the information.  For
        example the application had issued a :class:`apdu.WhoIsRequest` for a
        device and this is the corresponding :class:`apdu.IAmRequest`.

    .. method:: get_device_info(key)

        :param key: a device object identifier, a :class:`pdu.LocalStation` or a 
            :class:`RemoteStation` address.

        Return the :class:`DeviceInfo` instance in the cache associated with the
        key, or `None` if it does not exist.

    .. method:: update_device_info(info)

        :param DeviceInfo info: the updated device information

        This function is called by the application service layer when the device
        information has changed as a result of comparing it with incoming
        requests.  This function is overriden when the application has additional
        work, such as updating a database.

    .. method:: release_device_info(info)

        :param DeviceInfo info: device information no longer being used

        This function is called by the application service layer when there are
        no more confirmed requests associated with the device and the
        :class:`DeviceInfo` can be removed from the cache.  This function is
        overridden by a derived class to change the cache behaviour, for example
        perhaps the objects are removed from the cache until some timer expires.

Base Class
----------

This is a long line of text.

.. class:: Application(ApplicationServiceElement)

    This is a long line of text.

    .. method:: __init__(localDevice, localAddress)

        :param DeviceObject localDevice: the local device object
        :param Address localAddress: the local address
        :param actorClass: the initial source value

        This is a long line of text.

    .. method:: snork(address=None, segmentationSupported='no-segmentation', maxApduLengthAccepted=1024, maxSegmentsAccepted=None)

        :param Address localAddress: the local address
        :param segmentationSupported: enumeration :class:`basetypes.BACnetSegmentation`
        :param maxApduLengthAccepted: maximum APDU length
        :param maxSegmentsAccepted: segmentation parameter

        This is a long line of text.

    .. method:: add_object(obj)

        :param obj: the initial source value

        This is a long line of text.

    .. method:: delete_object(obj)

        :param obj: the initial source value

        This is a long line of text.

    .. method:: get_object_id(objid)

        :param obj: the initial source value

        This is a long line of text.

    .. method:: get_object_name(objname)

        :param objname: address to establish a connection

    .. method:: iter_objects()

        :param address: address to disconnect

    .. method:: indication(apdu)

        :param apdu: application layer PDU

        This is a long line of text.

    .. method:: do_WhoIsRequest(apdu)

        :param apdu: Who-Is request, :class:`apdu.WhoIsRequest`

        This is a long line of text.

    .. method:: do_IAmRequest(apdu)

        :param apdu: I-Am request, :class:`apdu.IAmRequest`

        This is a long line of text.

    .. method:: do_ReadPropertyRequest(apdu)

        :param apdu: Read-Property request, :class:`apdu.ReadPropertyRequest`

        This is a long line of text.

    .. method:: do_WritePropertyRequest(apdu)

        :param apdu: Write-Property request, :class:`apdu.WritePropertyRequest`

        This is a long line of text.

BACnet/IP Applications
----------------------

This is a long line of text.

.. class:: BIPSimpleApplication(Application)

    .. method:: __init__(localDevice, localAddress)

        :param localDevice: This is a long line of text.
        :param localAddress: This is a long line of text.

        This is a long line of text.

.. class:: BIPForeignApplication(Application)

    .. method:: __init__(localDevice, localAddress, bbmdAddress, bbmdTTL)

        :param localDevice: This is a long line of text.
        :param localAddress: This is a long line of text.
        :param bbmdAddress: This is a long line of text.
        :param bbmdTTL: This is a long line of text.

        This is a long line of text.

BACnet/IP Network Application
-----------------------------

This is a long line of text.

.. class:: BIPNetworkApplication(NetworkServiceElement)

    .. method:: __init__(localAddress)

        :param localAddress: This is a long line of text.

        This is a long line of text.
