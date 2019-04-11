.. BACpypes npdu module

.. module:: npdu

Network Layer Protocol Data Units
=================================

This is a long line of text.

PDU Base Types
--------------

.. class:: NPCI(PCI)

    Header of the network layer message.

    .. attribute:: npduVersion

        This is the version number of the BACnet protocol used. Current version is (1).

    .. attribute:: npduControl

        This is the a single octet. Each bit of the byte indicates the presence of specific fields in the NPCI.

    .. attribute:: npduDADR

        This is the destination address of the network layer message.

    .. attribute:: npduSADR

        This is the source address of the network layer message.

    .. attribute:: npduHopCount

        This is used to determine if network layer messages are being routed in a circular path.

    .. attribute:: npduNetMessage

        This is the network layer message type.

    .. attribute:: npduVendorID

        This is vendor specific ID number used for vendor specific network layer message.

    .. method:: update(npci)

        This is a long line of text.

    .. method:: encode(pdu)
                decode(pdu)

        :param pdu: :class:`pdu.PDUData` buffer

        This is a long line of text.

.. class:: NPDU(NPCI, PDUData)

    This is a long line of text.

    .. method:: encode(pdu)
                decode(pdu)

        :param pdu: :class:`pdu.PDUData` buffer

        This is a long line of text.

Service Requests
----------------

.. class:: WhoIsRouterToNetwork(NPCI)

    This message is used to find the router that is the destination for a specific network. It is also used for routers to update           routing tables.

    .. method:: encode(npdu)
                decode(npdu)

        :param pdu: :class:`NPDU` buffer

        This is a long line of text.

.. class:: IAmRouterToNetwork(NPCI)

    Response to a WhoIsRouterToNetwork request. Contains network numbers of the networks a router provides access to.

    .. method:: encode(npdu)
                decode(npdu)

        :param pdu: :class:`NPDU` buffer

        This is a long line of text.

.. class:: ICouldBeRouterToNetwork(NPCI)

    Response to a WhoIsRouterToNetwork request. Contains network numbers of the networks a half-router could provide access to over a PTP     connection, but the connection is not currently established.

    .. method:: encode(npdu)
                decode(npdu)

        :param pdu: :class:`NPDU` buffer

        This is a long line of text.

.. class:: RejectMessageToNetwork(NPCI)

    This is a message sent in response to a network layer message that was rejected due to an error.

    .. method:: encode(npdu)
                decode(npdu)

        :param pdu: :class:`NPDU` buffer

        This is a long line of text.

.. class:: RouterBusyToNetwork(NPCI)

    This is a message sent by a router to temporarily stop messages to specific destination networks.

    .. method:: encode(npdu)
                decode(npdu)

        :param pdu: :class:`NPDU` buffer

        This is a long line of text.

.. class:: RouterAvailableToNetwork(NPCI)

    This is a message sent by a router to enable or re-enable messages to specific destination networks.

    .. method:: encode(npdu)
                decode(npdu)

        :param pdu: :class:`NPDU` buffer

        This is a long line of text.

.. class:: RoutingTableEntry()

    This is a long line of text.

    .. attribute:: rtDNET

        This is a long line of text.

    .. attribute:: rtPortID

        This is a long line of text.

    .. attribute:: rtPortInfo

        This is a long line of text.

.. class:: InitializeRoutingTable(NPCI)

    This is a message used to initialize the routing table of a router or get the contents of the current routing table.

    .. method:: encode(npdu)
                decode(npdu)

        :param pdu: :class:`NPDU` buffer

        This is a long line of text.

.. class:: InitializeRoutingTableAck(NPCI)

    This is a message indicating the routing table of a router has been changed or the routing table has been initialized.

    .. method:: encode(npdu)
                decode(npdu)

        :param pdu: :class:`NPDU` buffer

        This is a long line of text.

.. class:: EstablishConnectionToNetwork(NPCI)

    This is a message used to tell a half-router to make a PTP connection to a network.

    .. method:: encode(npdu)
                decode(npdu)

        :param pdu: :class:`NPDU` buffer

        This is a long line of text.

.. class:: DisconnectConnectionToNetwork(NPCI)

    This is a message used to tell a half-router to close a PTP connection to a network.

    .. method:: encode(npdu)
                decode(npdu)

        :param pdu: :class:`NPDU` buffer

        This is a long line of text.
