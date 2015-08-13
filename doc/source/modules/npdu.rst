.. BACpypes npdu module

.. module:: npdu

Network Layer Protocol Data Units
=================================

This is a long line of text.

PDU Base Types
--------------

.. class:: NPCI(PCI)

    This is a long line of text.

    .. attribute:: npduVersion

        This is a long line of text.

    .. attribute:: npduControl

        This is a long line of text.

    .. attribute:: npduDADR

        This is a long line of text.

    .. attribute:: npduSADR

        This is a long line of text.

    .. attribute:: npduHopCount

        This is a long line of text.

    .. attribute:: npduNetMessage

        This is a long line of text.

    .. attribute:: npduVendorID

        This is a long line of text.

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

    This is a long line of text.

    .. method:: encode(npdu)
                decode(npdu)

        :param pdu: :class:`NPDU` buffer

        This is a long line of text.

.. class:: IAmRouterToNetwork(NPCI)

    This is a long line of text.

    .. method:: encode(npdu)
                decode(npdu)

        :param pdu: :class:`NPDU` buffer

        This is a long line of text.

.. class:: ICouldBeRouterToNetwork(NPCI)

    This is a long line of text.

    .. method:: encode(npdu)
                decode(npdu)

        :param pdu: :class:`NPDU` buffer

        This is a long line of text.

.. class:: RejectMessageToNetwork(NPCI)

    This is a long line of text.

    .. method:: encode(npdu)
                decode(npdu)

        :param pdu: :class:`NPDU` buffer

        This is a long line of text.

.. class:: RouterBusyToNetwork(NPCI)

    This is a long line of text.

    .. method:: encode(npdu)
                decode(npdu)

        :param pdu: :class:`NPDU` buffer

        This is a long line of text.

.. class:: RouterAvailableToNetwork(NPCI)

    This is a long line of text.

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

    This is a long line of text.

    .. method:: encode(npdu)
                decode(npdu)

        :param pdu: :class:`NPDU` buffer

        This is a long line of text.

.. class:: InitializeRoutingTableAck(NPCI)

    This is a long line of text.

    .. method:: encode(npdu)
                decode(npdu)

        :param pdu: :class:`NPDU` buffer

        This is a long line of text.

.. class:: EstablishConnectionToNetwork(NPCI)

    This is a long line of text.

    .. method:: encode(npdu)
                decode(npdu)

        :param pdu: :class:`NPDU` buffer

        This is a long line of text.

.. class:: DisconnectConnectionToNetwork(NPCI)

    This is a long line of text.

    .. method:: encode(npdu)
                decode(npdu)

        :param pdu: :class:`NPDU` buffer

        This is a long line of text.
