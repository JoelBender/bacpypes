.. BACpypes bsll module

.. module:: bsll

BACnet Streaming Link Layer
===========================

BACnet streaming link layer...

PDU Base Types
--------------

.. class:: BSLCI(PCI)

    .. attribute:: bslciType
    .. attribute:: bslciFunction
    .. attribute:: bslciLength

    This is a long line of text.

.. class:: BSLPDU(BVSCI, PDUData)

    This is a long line of text.

Service Requests
----------------

.. class:: Result(BVLCI)

    .. attribute:: bslciResultCode

    This is a long line of text.

.. class:: ServiceRequest(BSLCI)

.. class:: AccessRequest(BSLCI)

.. class:: AccessChallenge(BSLCI)

.. class:: AccessResponse(BSLCI)

Device-To-Device Stream
-----------------------

.. class:: DeviceToDeviceAPDU(BSLPDU)

Router-To-Router Stream
-----------------------

.. class:: RouterToRouterNPDU(BSLPDU)

Proxy-To-Server Stream
----------------------

.. class:: ProxyToServerUnicastNPDU(BSLPDU)

.. class:: ProxyToServerBroadcastNPDU(BSLPDU)

.. class:: ServerToProxyUnicastNPDU(BSLPDU)

.. class:: ServerToProxyBroadcastNPDU(BSLPDU)

LAN Emulation Stream
--------------------

.. class:: ClientToLESUnicastNPDU(BSLPDU

.. class:: ClientToLESBroadcastNPDU(BSLPDU)

.. class:: LESToClientUnicastNPDU(BSLPDU)

.. class:: LESToClientBroadcastNPDU(BSLPDU)
