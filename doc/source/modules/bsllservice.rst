.. BACpypes bsll module

.. module:: bsllservice

BACnet Streaming Link Layer Service
===================================

BACnet streaming link layer...

Streaming Packets
-----------------

.. function:: _Packetize(data)

    :param data: octet stream to slice into packets

    This is a long line of text.

.. class:: _StreamToPacket(StreamToPacket)

    This is a long line of text.

User Information
----------------

This is a long line of text.

.. class:: UserInformation()

    .. method:: __init__(**kwargs)

        :param string username: the user name
        :param string password: the user password
        :param boolean allServices:
        :param boolean deviceToDeviceService:
        :param boolean routerToRouterService:
        :param boolean proxyService:
        :param boolean laneService:
        :param boolean proxyNetwork:

    This is a long line of text.

Connection State
----------------

Every thing is connected and every connection has a state.

* NOT_AUTHENTICATED - no authentication attempted
* REQUESTED - access request sent to the server (client only)
* CHALLENGED - access challenge sent to the client (server only)
* AUTHENTICATED - authentication successful

This is a long line of text.

.. class:: ConnectionState

    This is a long line of text.

    .. attribute:: address

        This is a long line of text.

    .. attribute:: service

        This is a long line of text.

    .. attribute:: connected

        This is a long line of text.

    .. attribute:: accessState

        This is a long line of text.

    .. attribute:: challenge

        This is a long line of text.

    .. attribute:: userinfo

        This is a long line of text.

    .. attribute:: proxyAdapter

        This is a long line of text.

Service Adapter
---------------

This is a long line of text.

.. class:: ServiceAdapter()

    This is a long line of text.

    .. method:: __init__(mux)

        This is a long line of text.

    .. method:: authentication_required(addr)

        This is a long line of text.

    .. method:: get_default_user_info(addr)

        This is a long line of text.

    .. method:: get_user_info(username)

        This is a long line of text.

    .. method:: add_connection(conn)

        This is a long line of text.

    .. method:: remove_connection(conn)

        This is a long line of text.

    .. method:: service_request(pdu)

        This is a long line of text.

    .. method:: service_confirmation(conn, pdu)

        This is a long line of text.

.. class:: NetworkServiceAdapter(ServiceAdapter, NetworkAdapter)

    This is a long line of text.

TCP Multiplexing
----------------

This is a long line of text.

.. class:: TCPServerMultiplexer(Client)

    This is a long line of text.

    .. method:: __init__(addr=None)

        :param addr: address to bind

        This is a long line of text.

    .. method:: request(pdu)

        :param pdu: message to process

        This is a long line of text.

    .. method:: indication(server, pdu)

        :param server: multiplexer reference
        :param pdu: message to process

        This is a long line of text.

    .. method:: confirmation(pdu)

        :param pdu: message to process

        This is a long line of text.

    .. method:: do_AccessRequest(conn, bslpdu)

        :param conn: message to process
        :param bslpdu: message to process

        This is a long line of text.

    .. method:: do_AccessResponse(conn, bslpdu)

        :param conn: message to process
        :param bslpdu: message to process

        This is a long line of text.

.. class:: TCPClientMultiplexer(Client)

    This is a long line of text.

    .. method:: __init__()

        This is a long line of text.

    .. method:: request(pdu)

        :param pdu: message to process

        This is a long line of text.

    .. method:: indication(server, pdu)

        :param server: multiplexer reference
        :param pdu: message to process

        This is a long line of text.

    .. method:: confirmation(pdu)

        :param pdu: message to process

        This is a long line of text.

    .. method:: do_AccessChallenge(conn, bslpdu)

        :param conn: message to process
        :param bslpdu: message to process

        This is a long line of text.

.. class:: TCPMultiplexerASE(ApplicationServiceElement)

    This is a long line of text.

    .. method:: __init__(self, mux)

        This is a long line of text.

    .. method:: indication(*args, **kwargs)

        :param addPeer: peer address to add
        :param delPeer: peer address to delete

        This is a long line of text.

Device-to-Device Service
------------------------

This is a long line of text.

.. class:: DeviceToDeviceServerService(NetworkServiceAdapter)

    This is a long line of text.

    .. method:: process_npdu(npdu)

        This is a long line of text.

    .. method:: service_confirmation(conn, pdu)

        This is a long line of text.

.. class:: DeviceToDeviceClientService(NetworkServiceAdapter)

    This is a long line of text.

    .. method:: process_npdu(npdu)

        This is a long line of text.

    .. method:: connect(addr)

        This is a long line of text.

    .. method:: connect_ack(conn, pdu)

        This is a long line of text.

    .. method:: service_confirmation(conn, pdu)

        This is a long line of text.

Router-to-Router Service
------------------------

This is a long line of text.

.. class:: RouterToRouterService(NetworkServiceAdapter)

    This is a long line of text.

    .. method:: process_npdu(npdu)

        This is a long line of text.

    .. method:: connect(addr)

        This is a long line of text.

    .. method:: connect_ack(conn, pdu)

        This is a long line of text.

    .. method:: add_connection(conn)

        This is a long line of text.

    .. method:: remove_connection(conn)

        This is a long line of text.

    .. method:: service_confirmation(conn, pdu)

        This is a long line of text.

Proxy Service
-------------

This is a long line of text.

.. class:: ProxyServiceNetworkAdapter(NetworkAdapter)

    This is a long line of text.

    .. method:: process_npdu(npdu)

        This is a long line of text.

    .. method:: service_confirmation(conn, pdu)

        This is a long line of text.

.. class:: ProxyServerService(ServiceAdapter)

    This is a long line of text.

    .. method:: add_connection(conn)

        This is a long line of text.

    .. method:: remove_connection(conn)

        This is a long line of text.

    .. method:: service_confirmation(conn, bslpdu)

        This is a long line of text.

.. class:: ProxyClientService(ServiceAdapter)

    This is a long line of text.

    .. method:: __init__(self, mux, addr=None, userinfo=None)

        :param mux:
        :param addr:
        :param userinfo:

        This is a long line of text.

    .. method:: get_default_user_info(addr)

        This is a long line of text.

    .. method:: connect(addr=None, userinfo=None)

        This is a long line of text.

    .. method:: connect_ack(conn, bslpdu)

        This is a long line of text.

    .. method:: service_confirmation(conn, bslpdu)

        This is a long line of text.

    .. method:: confirmation(pdu)

        This is a long line of text.

LAN Emulation Service
---------------------

To be developed.
