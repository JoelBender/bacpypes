.. BACpypes bvll module

.. module:: bvll

BACnet Virtual Link Layer Service
=================================

BACnet virtual link layer...

UDP Multiplexing
----------------

.. class:: UDPMultiplexer

    .. method:: __init__(addr=None, noBroadcast=False)

        :param addr: address to bind
        :param noBroadcast: option for separate broadcast socket

        This is a long line of text.

    .. method:: indication(server, pdu)

        :param server: multiplexer reference
        :param pdu: message to process

        This is a long line of text.

    .. method:: confirmation(client, pdu)

        :param server: multiplexer reference
        :param pdu: message to process

        This is a long line of text.

.. class:: _MultiplexClient

    .. attribute:: multiplexer

        This is a long line of text.

    .. method:: __init__(mux)

        :param mux: multiplexer reference

        This is a long line of text.

    .. method:: confirmation(pdu)

        :param pdu: message to process

        This is a long line of text.

.. class:: _MultiplexServer

    .. attribute:: multiplexer

        This is a long line of text.

    .. method:: __init__(mux)

        :param mux: multiplexer reference

        This is a long line of text.

    .. method:: confirmation(pdu)

        :param pdu: message to process

        This is a long line of text.

Annex H - Tunneling
-------------------

.. class:: BTR

    .. method:: __init__()

        This is a long line of text.

    .. method:: indication(pdu)

        :param pdu: message to process

        This is a long line of text.

    .. method:: confirmation(pdu)

        :param pdu: message to process

        This is a long line of text.

    .. method:: add_peer(peerAddr [, networks])

        :param peerAddr: peer address
        :param networks: list of networks reachable by peer

        This is a long line of text.

    .. method:: delete_peer(peerAddr)

        :param peerAddr: peer address

        This is a long line of text.

Annex J - B/IP
--------------

.. class AnnexJCodec(Client, Server)

    .. method:: __init__

        This is a long line of text.

    .. method:: indication(rpdu)

        :param rpdu: message to process

        This is a long line of text.

    .. method:: confirmation(rpdu)

        :param rpdu: message to process

        This is a long line of text.

Service Access Point Types
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. class:: BIPSAP(ServiceAccessPoint)

    .. method:: __init__

        This is a long line of text.

    .. method:: sap_indication(pdu)

        :param pdu: message to process

        This is a long line of text.

    .. method:: sap_confirmation(pdu)

        :param pdu: message to process

        This is a long line of text.

.. class:: BIPSimple(BIPSAP, Client, Server)

    .. method:: indication(pdu)

        :param pdu: message to process

        This is a long line of text.

    .. method:: confirmation(pdu)

        :param pdu: message to process

        This is a long line of text.

.. class:: BIPForeign(BIPSAP, Client, Server, OneShotTask)

    .. method:: indication(pdu)

        :param pdu: message to process

        This is a long line of text.

    .. method:: confirmation(pdu)

        :param pdu: message to process

        This is a long line of text.

    .. method:: register(addr, ttl)

        :param addr: message to process
        :param ttl: time-to-live

        This is a long line of text.

    .. method:: unregister()

        This is a long line of text.

    .. method:: process_task()

        This is a long line of text.

.. class:: BIPBBMD(BIPSAP, Client, Server, RecurringTask)

    .. method:: __init__(addr)

        :param addr: address of itself

        This is a long line of text.

    .. method:: indication(pdu)

        :param pdu: message to process

        This is a long line of text.

    .. method:: confirmation(pdu)

        :param pdu: message to process

        This is a long line of text.

    .. method:: RegisterForeignDevice(addr, ttl)

        :param addr: address of foreign device
        :param ttl: time-to-live

        This is a long line of text.

    .. method:: DeleteForeignDeviceTableEntry(addr)

        :param addr: address of foreign device to delete

        This is a long line of text.

    .. method:: process_task()

        This is a long line of text.

    .. method:: add_peer(addr)

        :param addr: address of peer to add

        This is a long line of text.

    .. method:: delete_peer(addr)

        :param addr: addess of peer to delete

        This is a long line of text.

Service Element
^^^^^^^^^^^^^^^

.. class:: BVLLServiceElement(ApplicationServiceElement)

    .. method:: indication(pdu)

        :param pdu: message to process

        This is a long line of text.

    .. method:: confirmation(pdu)

        :param pdu: message to process

        This is a long line of text.
