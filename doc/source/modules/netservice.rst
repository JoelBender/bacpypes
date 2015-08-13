.. BACpypes network service module

.. module:: netservice

Network Layer Service
=====================

BACnet network layer...

Connection State
----------------

Every thing is connected and every connection has a state.

* ROUTER_AVAILABLE - normal
* ROUTER_BUSY - router is busy
* ROUTER_DISCONNECTED - could make a connection, but hasn't
* ROUTER_UNREACHABLE - cannot route

This is a long line of text.

Reference Structures
--------------------

This is a long line of text.

.. class:: NetworkReference()

    This is a long line of text.

    .. attribute:: network

        This is a long line of text.

    .. attribute:: router

        This is a long line of text.

    .. attribute:: status

        This is a long line of text.

.. class:: RouterReference()

    This is a long line of text.

    .. attribute:: adapter

        This is a long line of text.

    .. attribute:: address

        This is a long line of text.

    .. attribute:: networks

        This is a long line of text.

    .. attribute:: status

        This is a long line of text.

Network Service
---------------

This is a long line of text.

.. class NetworkAdapter(Client)

    This is a long line of text.

    .. attribute:: adapterSAP

        This is a long line of text.

    .. attribute:: adapterNet

        This is a long line of text.

    .. method:: confirmation(pdu)

        :param pdu:

        This is a long line of text.

    .. method:: process_npdu(npdu)

        :param ndpu:

        This is a long line of text.

    .. method:: EstablishConnectionToNetwork(net)

        :param net:

        This is a long line of text.

    .. method:: DisconnectConnectionToNetwork(net)

        :param net:

        This is a long line of text.

.. class NetworkServiceAccessPoint(ServiceAccessPoint, Server)

    This is a long line of text.

    .. attribute:: adapters

        This is a long line of text.

    .. attribute:: routers

        This is a long line of text.

    .. attribute:: networks

        This is a long line of text.

    .. attribute:: localAdapter

        This is a long line of text.

    .. attribute:: localAddress

        This is a long line of text.

    .. method:: bind(server, net=None, address=None)

        :param server:
        :param net:
        :param address:

        This is a long line of text.

    .. method:: add_router_references(adapter, address, netlist)

        This is a long line of text.

    .. method:: remove_router_references(adapter, address=None)

        This is a long line of text.

    .. method:: indication(pdu)

        This is a long line of text.

    .. method:: process_npdu(adapter, npdu)

        This is a long line of text.

    .. method:: sap_indication(adapter, npdu)

        This is a long line of text.

    .. method:: sap_confirmation(adapter, npdu)

        This is a long line of text.

.. class:: NetworkServiceElement(ApplicationServiceElement)

    This is a long line of text.

    .. method:: indication(adapter, npdu)

        :param adapter:
        :param npdu:

        This is a long line of text.

    .. method:: confirmation(adapter, npdu)

        :param adapter:
        :param npdu:

        This is a long line of text.

    .. method:: WhoIsRouterToNetwork(adapter, npdu)

        This is a long line of text.

    .. method:: IAmRouterToNetwork(adapter, npdu)

        This is a long line of text.

    .. method:: ICouldBeRouterToNetwork(adapter, npdu)

        This is a long line of text.

    .. method:: RejectMessageToNetwork(adapter, npdu)

        This is a long line of text.

    .. method:: RouterBusyToNetwork(adapter, npdu)

        This is a long line of text.

    .. method:: RouterAvailableToNetwork(adapter, npdu)

        This is a long line of text.

    .. method:: InitializeRoutingTable(adapter, npdu)

        This is a long line of text.

    .. method:: InitializeRoutingTableAck(adapter, npdu)

        This is a long line of text.

    .. method:: EstablishConnectionToNetwork(adapter, npdu)

        This is a long line of text.

    .. method:: DisconnectConnectionToNetwork(adapter, npdu)

        This is a long line of text.
