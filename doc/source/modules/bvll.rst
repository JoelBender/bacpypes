.. BACpypes bvll module

.. module:: bvll

BACnet Virtual Link Layer
=========================

BACnet virtual link layer...

PDU Base Types
--------------

This is a long line of text.

.. class:: BVLCI(PCI, DebugContents, Logging)

    .. attribute:: bvlciType
    .. attribute:: bvlciFunction
    .. attribute:: bvlciLength

    This is a long line of text.

.. class:: BVLPDU(BVLCI, PDUData)

    This is a long line of text.

PDU Types
---------

This is a long line of text.

.. class:: Result(BVLCI)

Broadcast Distribution Table
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This is a long line of text.

.. class:: ReadBroadcastDistributionTable(BVLCI)

    This is a long line of text.

.. class:: ReadBroadcastDistributionTableAck(BVLCI)

    This is a long line of text.

.. class:: WriteBroadcastDistributionTable(BVLCI)

    This is a long line of text.

Foreign Devices
^^^^^^^^^^^^^^^

This is a long line of text.

.. class:: FDTEntry(DebugContents)

    This is a long line of text.

.. class:: RegisterForeignDevice(BVLCI)

    This is a long line of text.

.. class:: ReadForeignDeviceTable(BVLCI)

    This is a long line of text.

.. class:: ReadForeignDeviceTableAck(BVLCI)

    This is a long line of text.

.. class:: DeleteForeignDeviceTableEntry(BVLCI)

    This is a long line of text.

Message Broadcasting
^^^^^^^^^^^^^^^^^^^^

This is a long line of text.

.. class:: OriginalUnicastNPDU(BVLPDU)

    This is a long line of text.

.. class:: OriginalBroadcastNPDU(BVLPDU)

    This is a long line of text.

.. class:: DistributeBroadcastToNetwork(BVLPDU)

    This is a long line of text.

.. class:: ForwardedNPDU(BVLPDU)

    This is a long line of text.
