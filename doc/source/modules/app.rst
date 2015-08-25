.. BACpypes app module

.. module:: app

Application
===========

This is a long line of text.

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

    .. method:: add_object(obj)

        :param actor: the initial source value

        This is a long line of text.

    .. method:: delete_object(obj)

        :param actor: the initial source value

        This is a long line of text.

    .. method:: get_object_id(objid)

        :param address: the initial source value

        This is a long line of text.

    .. method:: get_object_name(objname)

        :param address: address to establish a connection
        :param reconnect: timer value

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

IP Applications
---------------

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

IP Network Application
----------------------

This is a long line of text.

.. class:: BIPNetworkApplication(NetworkServiceElement)

    .. method:: __init__(localAddress)

        :param localAddress: This is a long line of text.

        This is a long line of text.
