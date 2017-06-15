.. BACpypes device services

Device Services
===============

.. class:: WhoIsIAmServices(Capability)

    This class provides the capability to initiate and respond to
    device-address-binding PDUs.

    .. method:: do_WhoIsRequest(apdu)

        :param WhoIsRequest apdu: Who-Is Request from the network

        See Clause 16.10.1 for the parameters to this service.

    .. method:: do_IAmRequest(apdu)

        :param IAmRequest apdu: I-Am Request from the network

        See Clause 16.10.3 for the parameters to this service.

    .. method:: who_is(self, low_limit=None, high_limit=None, address=None)

        :param Unsigned low_limit: optional low limit
        :param Unsigned high_limit: optional high limit
        :param Address address: optional destination, defaults to a global broadcast

        This is a utility function that makes it simpler to generate a 
        `WhoIsRequest`.

    .. method:: i_am(self, address=None)

        :param Address address: optional destination, defaults to a global broadcast

        This is a utility function that makes it simpler to generate an
        `IAmRequest` with the contents of the local device object.

.. class:: WhoHasIHaveServices(Capability)

    This class provides the capability to initiate and respond to
    device and object binding PDU's.

    .. method:: do_WhoHasRequest(apdu)

        :param WhoHasRequest apdu: Who-Has Request from the network

        See Clause 16.9.1 for the parameters to this service.

    .. method:: do_IHaveRequest(apdu)

        :param IHaveRequest apdu: I-Have Request from the network

        See Clause 16.9.3 for the parameters to this service.

    .. method:: who_has(thing, address=None)

        :param thing: object identifier or object name
        :param Address address: optional destination, defaults to a global broadcast

        Not implemented.

    .. method:: i_have(thing, address=None)

        :param thing: object identifier or object name
        :param Address address: optional destination, defaults to a global broadcast

        This is a utility function that makes it simpler to generate an
        `IHaveRequest` given an object.

Support Classes
---------------

There are a few support classes in this module that make it simpler to build
the most common BACnet devices.

.. class:: CurrentDateProperty(Property)

    This class is a specialized readonly property that always returns the
    current date as provided by the operating system.

    .. method:: ReadProperty(self, obj, arrayIndex=None)

        Returns the current date as a 4-item tuple consistent with the
        Python implementation of the :class:`Date` primitive value.

    .. method:: WriteProperty(self, obj, value, arrayIndex=None, priority=None)

        Object instances of this class are readonly, so this method raises
        a `writeAccessDenied` error.

.. class:: CurrentTimeProperty(Property)

    This class is a specialized readonly property that always returns the
    current local time as provided by the operating system.

    .. method:: ReadProperty(self, obj, arrayIndex=None)

        Returns the current date as a 4-item tuple consistent with the
        Python implementation of the :class:`Time` primitive value.

    .. method:: WriteProperty(self, obj, value, arrayIndex=None, priority=None)

        Object instances of this class are readonly, so this method raises
        a `writeAccessDenied` error.

.. class:: LocalDeviceObject(DeviceObject)

    The :class:`LocalDeviceObject` is an implementation of a
    :class:`DeviceObject` that provides default implementations for common
    properties and behaviors of a BACnet device.  It has default values for
    communications properties, returning the local date and time, and
    the `objectList` property for presenting a list of the objects in the
    device.
