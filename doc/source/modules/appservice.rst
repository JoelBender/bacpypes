.. BACpypes appservice module

.. module:: appservice

Application Service
===================

This is a long line of text.

Segmentation State Machine
--------------------------

This is a long line of text.

.. class:: SSM(OneShotTask)

    This is a long line of text.

    .. attribute:: remoteDevice

        This is a long line of text.

    .. attribute:: invokeID

        This is a long line of text.

    .. attribute:: state

        This is a long line of text.

    .. attribute:: segmentAPDU

        This is a long line of text.

    .. attribute:: segmentSize

        This is a long line of text.

    .. attribute:: segmentCount

        This is a long line of text.

    .. attribute:: maxSegmentsAccepted

        This is a long line of text.

    .. attribute:: retryCount

        This is a long line of text.

    .. attribute:: segmentRetryCount

        This is a long line of text.

    .. attribute:: sentAllSegments

        This is a long line of text.

    .. attribute:: lastSequenceNumber

        This is a long line of text.

    .. attribute:: initialSequenceNumber

        This is a long line of text.

    .. attribute:: actualWindowSize

        This is a long line of text.

    .. attribute:: proposedWindowSize

        This is a long line of text.

    .. method:: __init__(sap)

        :param sap: service access point reference

        This is a long line of text.

    .. method:: start_timer(msecs)

        :param msecs: milliseconds

        This is a long line of text.

    .. method:: stop_timer()

        This is a long line of text.

    .. method:: restart_timer(msecs)

        :param msecs: milliseconds

        This is a long line of text.

    .. method:: set_state(newState, timer=0)

        :param newState: new state
        :param timer: timer value

    .. method:: set_segmentation_context(apdu)

        :param apdu: application PDU

    .. method:: get_segment(indx)

        :param apdu: application layer PDU

        This is a long line of text.

    .. method:: append_segment(apdu)

        :param apdu: application PDU

        This is a long line of text.

    .. method:: in_window(seqA, seqB)

        :param int seqA: latest sequence number
        :param int seqB: initial sequence number

        This is a long line of text.

    .. method:: FillWindow(self, seqNum)

        :param int seqNum: initial sequence number

        This is a long line of text.

Client Segmentation State Machine
---------------------------------

This is a long line of text.

Server Segmentation State Machine
---------------------------------

This is a long line of text.

Application Stack
-----------------

This is a long line of text.

.. class:: StateMachineAccessPoint(DeviceInfo, Client, ServiceAccessPoint)

    This is a long line of text.

.. class:: ApplicationServiceAccessPoint(ApplicationServiceElement, ServiceAccessPoint)

    This is a long line of text.
