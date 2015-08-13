.. BACpypes apdu module

.. module:: apdu

Application Layer PDUs
======================

This is a long line of text.

Globals
-------

.. data:: apdu_types

    This is a long line of text.

.. data:: confirmed_request_types

    This is a long line of text.

.. data:: complex_ack_types

    This is a long line of text.

.. data:: unconfirmed_request_types

    This is a long line of text.

.. data:: error_types

    This is a long line of text.

Functions
---------

.. function:: register_apdu_type(klass)

    This is a long line of text.

.. function:: register_confirmed_request_type(klass)

    This is a long line of text.

.. function:: register_complex_ack_type(klass)

    This is a long line of text.

.. function:: register_unconfirmed_request_type(klass)

    This is a long line of text.

.. function:: register_error_type(klass)

    This is a long line of text.

.. function:: encode_max_apdu_segments(arg)
.. function:: decode_max_apdu_segments(arg)

    This is a long line of text.

.. function:: encode_max_apdu_response(arg)
.. function:: decode_max_apdu_response(arg)

    This is a long line of text.

PDU Base Types
--------------

This is a long line of text.

.. class:: APCI(PCI)

    .. attribute:: apduType
    .. attribute:: apduSeg
    .. attribute:: apduMor
    .. attribute:: apduSA
    .. attribute:: apduSrv
    .. attribute:: apduNak
    .. attribute:: apduSeq
    .. attribute:: apduWin
    .. attribute:: apduMaxSegs
    .. attribute:: apduMaxResp
    .. attribute:: apduService
    .. attribute:: apduInvokeID
    .. attribute:: apduAbortRejectReason

    This is a long line of text.

    .. method:: update(apci)

        :param apci: source data to copy

        This is a long line of text.

    .. method:: encode(pdu)
                decode(pdu)

        :param pdu: :class:`pdu.PDUData` buffer

        This is a long line of text.

.. class:: APDU(APCI, PDUData)

    This is a long line of text.

    .. method:: encode(pdu)
                decode(pdu)

        :param pdu: :class:`pdu.PDUData` buffer

        This is a long line of text.

.. class:: _APDU(APDU)

    This is a long line of text.

    .. method:: encode(pdu)
                decode(pdu)

        :param pdu: :class:`pdu.PDUData` buffer

        This is a long line of text.

    .. method:: set_context(context)

        :param context: :class:`APDU` reference

Basic Classes
-------------

This is a long line of text.

.. class:: ConfirmedRequestPDU(_APDU)

    This is a long line of text.

.. class:: ConfirmedRequestPDU(_APDU)

    This is a long line of text.

.. class:: UnconfirmedRequestPDU(_APDU)

    This is a long line of text.

.. class:: SimpleAckPDU(_APDU)

    This is a long line of text.

.. class:: ComplexAckPDU(_APDU)

    This is a long line of text.

.. class:: SegmentAckPDU(_APDU)

    This is a long line of text.

.. class:: ErrorPDU(_APDU)

    This is a long line of text.

.. class:: RejectPDU(_APDU)

    This is a long line of text.

.. class:: SimpleAckPDU(_APDU)

    This is a long line of text.

Sequence Classes
----------------

This is a long line of text.

.. class:: APCISequence(APCI, Sequence)

    This is a long line of text.

.. class:: ConfirmedRequestSequence(APCISequence, ConfirmedRequestPDU)

    This is a long line of text.

.. class:: ComplexAckSequence(APCISequence, ComplexAckPDU)

    This is a long line of text.

.. class:: UnconfirmedRequestSequence(APCISequence, UnconfirmedRequestPDU)

    This is a long line of text.

.. class:: ErrorSequence(APCISequence, ErrorPDU)

    This is a long line of text.

Errors
^^^^^^

This is a long line of text.

.. class:: ErrorClass(Enumerated)

    This is a long line of text.

.. class:: ErrorCode(Enumerated)

    This is a long line of text.

.. class:: ErrorType(Sequence)

    This is a long line of text.

.. class:: Error(ErrorSequence, ErrorType)

    This is a long line of text.

Who-Is/I-Am
^^^^^^^^^^^

This is a long line of text.

.. class:: WhoIsRequest(UnconfirmedRequestSequence)

    This is a long line of text.

.. class:: IAmRequest(UnconfirmedRequestSequence)

    This is a long line of text.

Who-Has/I-Have
^^^^^^^^^^^^^^

This is a long line of text.

.. class:: WhoHasRequest(UnconfirmedRequestSequence)

    This is a long line of text.

.. class:: WhoHasLimits(Sequence)

    This is a long line of text.

.. class:: WhoHasObject(Choice)

    This is a long line of text.

This is a long line of text.

.. class:: IHaveRequest(UnconfirmedRequestSequence)

    This is a long line of text.

Read-Property
^^^^^^^^^^^^^

This is a long line of text.

.. class:: ReadPropertyRequest(ConfirmedRequestSequence)

    This is a long line of text.

.. class:: ReadPropertyACK(ComplexAckSequence)

    This is a long line of text.

Write-Property
^^^^^^^^^^^^^^

This is a long line of text.

.. class:: WritePropertyRequest(ConfirmedRequestSequence)

    This is a long line of text.

Read-Property-Multiple
^^^^^^^^^^^^^^^^^^^^^^

This is a long line of text.

.. class:: ReadPropertyMultipleRequest(ConfirmedRequestSequence)

    This is a long line of text.

.. class:: ReadAccessSpecification(Sequence)

    This is a long line of text.

.. class:: ReadPropertyMultipleACK(ComplexAckSequence)

    This is a long line of text.

.. class:: ReadAccessResult(Sequence)

    This is a long line of text.

.. class:: ReadAccessResultElement(Sequence)

    This is a long line of text.

.. class:: ReadAccessResultElementChoice(Choice)

    This is a long line of text.

Write-Property-Multiple
^^^^^^^^^^^^^^^^^^^^^^^

This is a long line of text.

.. class:: WritePropertyMultipleRequest(ConfirmedRequestSequence)

    This is a long line of text.

.. class:: WriteAccessSpecification(Sequence)

    This is a long line of text.

.. class:: WritePropertyMultipleError(ErrorSequence)

    This is a long line of text.

Read-Range
^^^^^^^^^^

This is a long line of text.

.. class:: ReadRangeRequest(ConfirmedRequestSequence)

    This is a long line of text.

.. class:: Range(Choice)

    This is a long line of text.

.. class:: RangeByPosition(Sequence)

    This is a long line of text.

.. class:: RangeBySequenceNumber(Sequence)

    This is a long line of text.

.. class:: RangeByTime(Sequence)

    This is a long line of text.

.. class:: ReadRangeACK(ComplexAckSequence)

    This is a long line of text.

Event-Notification
^^^^^^^^^^^^^^^^^^

This is a long line of text.

.. class:: ConfirmedEventNotificationRequest(ConfirmedRequestSequence)

    This is a long line of text.

.. class:: UnconfirmedEventNotificationRequest(Sequence)

    This is a long line of text.

Change-Of-Value-Notification
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This is a long line of text.

.. class:: UnconfirmedCOVNotificationRequest(UnconfirmedRequestSequence)

    This is a long line of text.

Other Errors
^^^^^^^^^^^^

This is a long line of text.

.. class:: ChangeListError(ErrorSequence)

    This is a long line of text.

.. class:: CreateObjectError(ErrorSequence)

    This is a long line of text.

.. class:: ConfirmedPrivateTransferError(ErrorSequence)

    This is a long line of text.

.. class:: VTCloseError(ErrorSequence)

    This is a long line of text.
