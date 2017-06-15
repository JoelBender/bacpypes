#!/usr/bin/python

"""
Application Layer
"""

from time import time as _time

from .debugging import ModuleLogger, DebugContents, bacpypes_debugging

from .comm import Client, ServiceAccessPoint, ApplicationServiceElement
from .task import OneShotTask

from .pdu import Address, LocalStation, RemoteStation
from .apdu import AbortPDU, AbortReason, ComplexAckPDU, \
    ConfirmedRequestPDU, Error, ErrorPDU, RejectPDU, SegmentAckPDU, \
    SimpleAckPDU, UnconfirmedRequestPDU, apdu_types, \
    unconfirmed_request_types, confirmed_request_types, complex_ack_types, \
    error_types
from .errors import RejectException, AbortException

# some debugging
_debug = 0
_log = ModuleLogger(globals())

#
#   SSM - Segmentation State Machine
#

# transaction states
IDLE = 0
SEGMENTED_REQUEST = 1
AWAIT_CONFIRMATION = 2
AWAIT_RESPONSE = 3
SEGMENTED_RESPONSE = 4
SEGMENTED_CONFIRMATION = 5
COMPLETED = 6
ABORTED = 7

@bacpypes_debugging
class SSM(OneShotTask, DebugContents):

    transactionLabels = ['IDLE'
        , 'SEGMENTED_REQUEST', 'AWAIT_CONFIRMATION', 'AWAIT_RESPONSE'
        , 'SEGMENTED_RESPONSE', 'SEGMENTED_CONFIRMATION', 'COMPLETED', 'ABORTED'
        ]

    _debug_contents = ('ssmSAP', 'localDevice', 'remoteDevice', 'invokeID'
        , 'state', 'segmentAPDU', 'segmentSize', 'segmentCount', 'maxSegmentsAccepted'
        , 'retryCount', 'segmentRetryCount', 'sentAllSegments', 'lastSequenceNumber'
        , 'initialSequenceNumber', 'actualWindowSize', 'proposedWindowSize'
        )

    def __init__(self, sap, remoteDevice):
        """Common parts for client and server segmentation."""
        if _debug: SSM._debug("__init__ %r %r", sap, remoteDevice)
        OneShotTask.__init__(self)

        self.ssmSAP = sap                   # service access point
        self.remoteDevice = remoteDevice    # remote device information, a DeviceInfo instance
        self.invokeID = None                # invoke ID

        self.state = IDLE                   # initial state
        self.segmentAPDU = None             # refers to request or response
        self.segmentSize = None             # how big the pieces are
        self.segmentCount = None

        self.retryCount = None
        self.segmentRetryCount = None
        self.sentAllSegments = None
        self.lastSequenceNumber = None
        self.initialSequenceNumber = None
        self.actualWindowSize = None
        self.proposedWindowSize = None

        # the maximum number of segments starts out being what's in the SAP
        # which is the defaults or values from the local device.
        self.maxSegmentsAccepted = self.ssmSAP.maxSegmentsAccepted

    def start_timer(self, msecs):
        if _debug: SSM._debug("start_timer %r", msecs)

        # if this is active, pull it
        if self.isScheduled:
            if _debug: SSM._debug("    - is scheduled")
            self.suspend_task()

        # now install this
        self.install_task(_time() + (msecs / 1000.0))

    def stop_timer(self):
        if _debug: SSM._debug("stop_timer")

        # if this is active, pull it
        if self.isScheduled:
            if _debug: SSM._debug("    - is scheduled")
            self.suspend_task()

    def restart_timer(self, msecs):
        if _debug: SSM._debug("restart_timer %r", msecs)

        # if this is active, pull it
        if self.isScheduled:
            if _debug: SSM._debug("    - is scheduled")
            self.suspend_task()

        # now install this
        self.install_task(_time() + (msecs / 1000.0))

    def set_state(self, newState, timer=0):
        """This function is called when the derived class wants to change state."""
        if _debug: SSM._debug("set_state %r (%s) timer=%r", newState, SSM.transactionLabels[newState], timer)

        # make sure we have a correct transition
        if (self.state == COMPLETED) or (self.state == ABORTED):
            e = RuntimeError("invalid state transition from %s to %s" % (SSM.transactionLabels[self.state], SSM.transactionLabels[newState]))
            SSM._exception(e)
            raise e

        # stop any current timer
        self.stop_timer()

        # make the change
        self.state = newState

        # if another timer should be started, start it
        if timer:
            self.start_timer(timer)

    def set_segmentation_context(self, apdu):
        """This function is called to set the segmentation context."""
        if _debug: SSM._debug("set_segmentation_context %s", repr(apdu))

        # set the context
        self.segmentAPDU = apdu

    def get_segment(self, indx):
        """This function returns an APDU coorisponding to a particular
        segment of a confirmed request or complex ack.  The segmentAPDU
        is the context."""
        if _debug: SSM._debug("get_segment %r", indx)

        # check for no context
        if not self.segmentAPDU:
            raise RuntimeError("no segmentation context established")

        # check for invalid segment number
        if indx >= self.segmentCount:
            raise RuntimeError("invalid segment number {0}, APDU has {1} segments".format(indx, self.segmentCount))

        if self.segmentAPDU.apduType == ConfirmedRequestPDU.pduType:
            if _debug: SSM._debug("    - confirmed request context")

            segAPDU = ConfirmedRequestPDU(self.segmentAPDU.apduService)

            segAPDU.apduMaxSegs = self.maxSegmentsAccepted
            segAPDU.apduMaxResp = self.ssmSAP.maxApduLengthAccepted
            segAPDU.apduInvokeID = self.invokeID;

            # segmented response accepted?
            segAPDU.apduSA = self.ssmSAP.segmentationSupported in ('segmentedReceive', 'segmentedBoth')
            if _debug: SSM._debug("    - segmented response accepted: %r", segAPDU.apduSA)

        elif self.segmentAPDU.apduType == ComplexAckPDU.pduType:
            if _debug: SSM._debug("    - complex ack context")

            segAPDU = ComplexAckPDU(self.segmentAPDU.apduService, self.segmentAPDU.apduInvokeID)
        else:
            raise RuntimeError("invalid APDU type for segmentation context")

        # maintain the the user data reference
        segAPDU.pduUserData = self.segmentAPDU.pduUserData

        # make sure the destination is set
        segAPDU.pduDestination = self.remoteDevice.address

        # segmented message?
        if (self.segmentCount != 1):
            segAPDU.apduSeg = True
            segAPDU.apduMor = (indx < (self.segmentCount - 1)) # more follows
            segAPDU.apduSeq = indx % 256                       # sequence number
            segAPDU.apduWin = self.proposedWindowSize          # window size
        else:
            segAPDU.apduSeg = False
            segAPDU.apduMor = False

        # add the content
        offset = indx * self.segmentSize
        segAPDU.put_data( self.segmentAPDU.pduData[offset:offset+self.segmentSize] )

        # success
        return segAPDU

    def append_segment(self, apdu):
        """This function appends the apdu content to the end of the current
        APDU being built.  The segmentAPDU is the context."""
        if _debug: SSM._debug("append_segment %r", apdu)

        # check for no context
        if not self.segmentAPDU:
            raise RuntimeError("no segmentation context established")

        # append the data
        self.segmentAPDU.put_data(apdu.pduData)

    def in_window(self, seqA, seqB):
        if _debug: SSM._debug("in_window %r %r", seqA, seqB)

        rslt = ((seqA - seqB + 256) % 256) < self.actualWindowSize
        if _debug: SSM._debug("    - rslt: %r", rslt)

        return rslt

    def FillWindow(self, seqNum):
        """This function sends all of the packets necessary to fill
        out the segmentation window."""
        if _debug: SSM._debug("FillWindow %r", seqNum)

        for ix in range(self.actualWindowSize):
            apdu = self.get_segment(seqNum + ix)

            # send the message
            self.ssmSAP.request(apdu)

            # check for no more follows
            if not apdu.apduMor:
                self.sentAllSegments = True
                break

#
#   ClientSSM - Client Segmentation State Machine
#

@bacpypes_debugging
class ClientSSM(SSM):

    def __init__(self, sap, remoteDevice):
        if _debug: ClientSSM._debug("__init__ %s %r", sap, remoteDevice)
        SSM.__init__(self, sap, remoteDevice)

        # initialize the retry count
        self.retryCount = 0

    def set_state(self, newState, timer=0):
        """This function is called when the client wants to change state."""
        if _debug: ClientSSM._debug("set_state %r (%s) timer=%r", newState, SSM.transactionLabels[newState], timer)

        # do the regular state change
        SSM.set_state(self, newState, timer)

        # when completed or aborted, remove tracking
        if (newState == COMPLETED) or (newState == ABORTED):
            if _debug: ClientSSM._debug("    - remove from active transactions")
            self.ssmSAP.clientTransactions.remove(self)

            if _debug: ClientSSM._debug("    - release device information")
            self.ssmSAP.deviceInfoCache.release_device_info(self.remoteDevice)

    def request(self, apdu):
        """This function is called by client transaction functions when it wants
        to send a message to the device."""
        if _debug: ClientSSM._debug("request %r", apdu)

        # make sure it has a good source and destination
        apdu.pduSource = None
        apdu.pduDestination = self.remoteDevice.address

        # send it via the device
        self.ssmSAP.request(apdu)

    def indication(self, apdu):
        """This function is called after the device has bound a new transaction
        and wants to start the process rolling."""
        if _debug: ClientSSM._debug("indication %r", apdu)

        # make sure we're getting confirmed requests
        if (apdu.apduType != ConfirmedRequestPDU.pduType):
            raise RuntimeError("invalid APDU (1)")

        # save the request and set the segmentation context
        self.set_segmentation_context(apdu)

        # the segment size is the minimum of the maximum size I can transmit,
        # the maximum conveyable by the internetwork to the remote device, and
        # the maximum APDU size accepted by the remote device.
        self.segmentSize = min(
            self.ssmSAP.maxApduLengthAccepted,
            self.remoteDevice.maxNpduLength,
            self.remoteDevice.maxApduLengthAccepted,
            )
        if _debug: ClientSSM._debug("    - segment size: %r", self.segmentSize)

        # the maximum number of segments acceptable in the reply
        if apdu.apduMaxSegs is not None:
            # this request overrides the default
            self.maxSegmentsAccepted = apdu.apduMaxSegs

        # save the invoke ID
        self.invokeID = apdu.apduInvokeID
        if _debug: ClientSSM._debug("    - invoke ID: %r", self.invokeID)

        # compute the segment count ### minus the header?
        if not apdu.pduData:
            # always at least one segment
            self.segmentCount = 1
        else:
            # split into chunks, maybe need one more
            self.segmentCount, more = divmod(len(apdu.pduData), self.segmentSize)
            if more:
                self.segmentCount += 1
        if _debug: ClientSSM._debug("    - segment count: %r", self.segmentCount)

        # make sure we support segmented transmit if we need to
        if self.segmentCount > 1:
            if self.ssmSAP.segmentationSupported not in ('segmentedTransmit', 'segmentedBoth'):
                if _debug: ClientSSM._debug("    - local device can't send segmented requests")
                abort = self.abort(AbortReason.segmentationNotSupported)
                self.response(abort)
                return
            if self.remoteDevice.segmentationSupported not in ('segmentedReceive', 'segmentedBoth'):
                if _debug: ClientSSM._debug("    - remote device can't receive segmented requests")
                abort = self.abort(AbortReason.segmentationNotSupported)
                self.response(abort)
                return

        ### check for APDUTooLong?

        # send out the first segment (or the whole thing)
        if self.segmentCount == 1:
            # SendConfirmedUnsegmented
            self.sentAllSegments = True
            self.retryCount = 0
            self.set_state(AWAIT_CONFIRMATION, self.ssmSAP.retryTimeout)
        else:
            # SendConfirmedSegmented
            self.sentAllSegments = False
            self.retryCount = 0
            self.segmentRetryCount = 0
            self.initialSequenceNumber = 0
            self.proposedWindowSize = self.ssmSAP.maxSegmentsAccepted
            self.actualWindowSize = 1
            self.set_state(SEGMENTED_REQUEST, self.ssmSAP.segmentTimeout)

        # deliver to the device
        self.request(self.get_segment(0))

    def response(self, apdu):
        """This function is called by client transaction functions when they want
        to send a message to the application."""
        if _debug: ClientSSM._debug("response %r", apdu)

        # make sure it has a good source and destination
        apdu.pduSource = self.remoteDevice.address
        apdu.pduDestination = None

        # send it to the application
        self.ssmSAP.sap_response(apdu)

    def confirmation(self, apdu):
        """This function is called by the device for all upstream messages related
        to the transaction."""
        if _debug: ClientSSM._debug("confirmation %r", apdu)

        if self.state == SEGMENTED_REQUEST:
            self.segmented_request(apdu)
        elif self.state == AWAIT_CONFIRMATION:
            self.await_confirmation(apdu)
        elif self.state == SEGMENTED_CONFIRMATION:
            self.segmented_confirmation(apdu)
        else:
            raise RuntimeError("invalid state")

    def process_task(self):
        """This function is called when something has taken too long."""
        if _debug: ClientSSM._debug("process_task")

        if self.state == SEGMENTED_REQUEST:
            self.segmented_request_timeout()
        elif self.state == AWAIT_CONFIRMATION:
            self.await_confirmation_timeout()
        elif self.state == SEGMENTED_CONFIRMATION:
            self.segmented_confirmation_timeout()
        elif self.state == COMPLETED:
            pass
        elif self.state == ABORTED:
            pass
        else:
            e = RuntimeError("invalid state")
            ClientSSM._exception("exception: %r", e)
            raise e

    def abort(self, reason):
        """This function is called when the transaction should be aborted."""
        if _debug: ClientSSM._debug("abort %r", reason)

        # change the state to aborted
        self.set_state(ABORTED)

        # build an abort PDU to return
        abort_pdu = AbortPDU(False, self.invokeID, reason)

        # return it
        return abort_pdu

    def segmented_request(self, apdu):
        """This function is called when the client is sending a segmented request
        and receives an apdu."""
        if _debug: ClientSSM._debug("segmented_request %r", apdu)

        # client is ready for the next segment
        if apdu.apduType == SegmentAckPDU.pduType:
            if _debug: ClientSSM._debug("    - segment ack")

            # duplicate ack received?
            if not self.in_window(apdu.apduSeq, self.initialSequenceNumber):
                if _debug: ClientSSM._debug("    - not in window")
                self.restart_timer(self.ssmSAP.segmentTimeout)

            # final ack received?
            elif self.sentAllSegments:
                if _debug: ClientSSM._debug("    - all done sending request")
                self.set_state(AWAIT_CONFIRMATION, self.ssmSAP.retryTimeout)

            # more segments to send
            else:
                if _debug: ClientSSM._debug("    - more segments to send")

                self.initialSequenceNumber = (apdu.apduSeq + 1) % 256
                self.actualWindowSize = apdu.apduWin
                self.segmentRetryCount = 0
                self.FillWindow(self.initialSequenceNumber)
                self.restart_timer(self.ssmSAP.segmentTimeout)

        # simple ack
        elif (apdu.apduType == SimpleAckPDU.pduType):
            if _debug: ClientSSM._debug("    - simple ack")

            if not self.sentAllSegments:
                abort = self.abort(AbortReason.invalidApduInThisState)
                self.request(abort)     # send it to the device
                self.response(abort)    # send it to the application
            else:
                self.set_state(COMPLETED)
                self.response(apdu)

        elif (apdu.apduType == ComplexAckPDU.pduType):
            if _debug: ClientSSM._debug("    - complex ack")

            if not self.sentAllSegments:
                abort = self.abort(AbortReason.invalidApduInThisState)
                self.request(abort)     # send it to the device
                self.response(abort)    # send it to the application

            elif not apdu.apduSeg:
                self.set_state(COMPLETED)
                self.response(apdu)

            else:
                # set the segmented response context
                self.set_segmentation_context(apdu)

                self.actualWindowSize = min(apdu.apduWin, self.ssmSAP.maxSegmentsAccepted)
                self.lastSequenceNumber = 0
                self.initialSequenceNumber = 0
                self.set_state(SEGMENTED_CONFIRMATION, self.ssmSAP.segmentTimeout)

        # some kind of problem
        elif (apdu.apduType == ErrorPDU.pduType) or (apdu.apduType == RejectPDU.pduType) or (apdu.apduType == AbortPDU.pduType):
            if _debug: ClientSSM._debug("    - error/reject/abort")

            self.set_state(COMPLETED)
            self.response = apdu
            self.response(apdu)

        else:
            raise RuntimeError("invalid APDU (2)")

    def segmented_request_timeout(self):
        if _debug: ClientSSM._debug("segmented_request_timeout")

        # try again
        if self.segmentRetryCount < self.ssmSAP.retryCount:
            if _debug: ClientSSM._debug("    - retry segmented request")

            self.segmentRetryCount += 1
            self.start_timer(self.ssmSAP.segmentTimeout)
            self.FillWindow(self.initialSequenceNumber)
        else:
            if _debug: ClientSSM._debug("    - abort, no response from the device")

            abort = self.abort(AbortReason.noResponse)
            self.response(abort)

    def await_confirmation(self, apdu):
        if _debug: ClientSSM._debug("await_confirmation %r", apdu)

        if (apdu.apduType == AbortPDU.pduType):
            if _debug: ClientSSM._debug("    - server aborted")

            self.set_state(ABORTED)
            self.response(apdu)

        elif (apdu.apduType == SimpleAckPDU.pduType) or (apdu.apduType == ErrorPDU.pduType) or (apdu.apduType == RejectPDU.pduType):
            if _debug: ClientSSM._debug("    - simple ack, error, or reject")

            self.set_state(COMPLETED)
            self.response(apdu)

        elif (apdu.apduType == ComplexAckPDU.pduType):
            if _debug: ClientSSM._debug("    - complex ack")

            # if the response is not segmented, we're done
            if not apdu.apduSeg:
                if _debug: ClientSSM._debug("    - unsegmented")

                self.set_state(COMPLETED)
                self.response(apdu)

            elif self.ssmSAP.segmentationSupported not in ('segmentedReceive', 'segmentedBoth'):
                if _debug: ClientSSM._debug("    - local device can't receive segmented messages")
                abort = self.abort(AbortReason.segmentationNotSupported)
                self.response(abort)

            elif apdu.apduSeq == 0:
                if _debug: ClientSSM._debug("    - segmented response")

                # set the segmented response context
                self.set_segmentation_context(apdu)

                self.actualWindowSize = min(apdu.apduWin, self.ssmSAP.maxSegmentsAccepted)
                self.lastSequenceNumber = 0
                self.initialSequenceNumber = 0
                self.set_state(SEGMENTED_CONFIRMATION, self.ssmSAP.segmentTimeout)

                # send back a segment ack
                segack = SegmentAckPDU( 0, 0, self.invokeID, self.initialSequenceNumber, self.actualWindowSize )
                self.request(segack)

            else:
                if _debug: ClientSSM._debug("    - invalid APDU in this state")

                abort = self.abort(AbortReason.invalidApduInThisState)
                self.request(abort) # send it to the device
                self.response(abort) # send it to the application

        elif (apdu.apduType == SegmentAckPDU.pduType):
            if _debug: ClientSSM._debug("    - segment ack(!?)")

            self.restart_timer(self.ssmSAP.segmentTimeout)

        else:
            raise RuntimeError("invalid APDU (3)")

    def await_confirmation_timeout(self):
        if _debug: ClientSSM._debug("await_confirmation_timeout")

        self.retryCount += 1
        if self.retryCount < self.ssmSAP.retryCount:
            if _debug: ClientSSM._debug("    - no response, try again (%d < %d)", self.retryCount, self.ssmSAP.retryCount)

            # save the retry count, indication acts like the request is coming
            # from the application so the retryCount gets re-initialized.
            saveCount = self.retryCount
            self.indication(self.segmentAPDU)
            self.retryCount = saveCount
        else:
            if _debug: ClientSSM._debug("    - retry count exceeded")
            abort = self.abort(AbortReason.noResponse)
            self.response(abort)

    def segmented_confirmation(self, apdu):
        if _debug: ClientSSM._debug("segmented_confirmation %r", apdu)

        # the only messages we should be getting are complex acks
        if (apdu.apduType != ComplexAckPDU.pduType):
            if _debug: ClientSSM._debug("    - complex ack required")

            abort = self.abort(AbortReason.invalidApduInThisState)
            self.request(abort) # send it to the device
            self.response(abort) # send it to the application
            return

        # it must be segmented
        if not apdu.apduSeg:
            if _debug: ClientSSM._debug("    - must be segmented")

            abort = self.abort(AbortReason.invalidApduInThisState)
            self.request(abort) # send it to the device
            self.response(abort) # send it to the application
            return

        # proper segment number
        if apdu.apduSeq != (self.lastSequenceNumber + 1) % 256:
            if _debug: ClientSSM._debug("    - segment %s received out of order, should be %s", apdu.apduSeq, (self.lastSequenceNumber + 1) % 256)

            # segment received out of order
            self.restart_timer(self.ssmSAP.segmentTimeout)
            segack = SegmentAckPDU( 1, 0, self.invokeID, self.lastSequenceNumber, self.actualWindowSize )
            self.request(segack)
            return

        # add the data
        self.append_segment(apdu)

        # update the sequence number
        self.lastSequenceNumber = (self.lastSequenceNumber + 1) % 256

        # last segment received
        if not apdu.apduMor:
            if _debug: ClientSSM._debug("    - no more follows")

            # send a final ack
            segack = SegmentAckPDU( 0, 0, self.invokeID, self.lastSequenceNumber, self.actualWindowSize )
            self.request(segack)

            self.set_state(COMPLETED)
            self.response(self.segmentAPDU)

        elif apdu.apduSeq == ((self.initialSequenceNumber + self.actualWindowSize) % 256):
            if _debug: ClientSSM._debug("    - last segment in the group")

            self.initialSequenceNumber = self.lastSequenceNumber
            self.restart_timer(self.ssmSAP.segmentTimeout)
            segack = SegmentAckPDU( 0, 0, self.invokeID, self.lastSequenceNumber, self.actualWindowSize )
            self.request(segack)

        else:
            # wait for more segments
            if _debug: ClientSSM._debug("    - wait for more segments")

            self.restart_timer(self.ssmSAP.segmentTimeout)

    def segmented_confirmation_timeout(self):
        if _debug: ClientSSM._debug("segmented_confirmation_timeout")

        abort = self.abort(AbortReason.noResponse)
        self.response(abort)

#
#   ServerSSM - Server Segmentation State Machine
#

@bacpypes_debugging
class ServerSSM(SSM):

    def __init__(self, sap, remoteDevice):
        if _debug: ServerSSM._debug("__init__ %s %r", sap, remoteDevice)
        SSM.__init__(self, sap, remoteDevice)

    def set_state(self, newState, timer=0):
        """This function is called when the client wants to change state."""
        if _debug: ServerSSM._debug("set_state %r (%s) timer=%r", newState, SSM.transactionLabels[newState], timer)

        # do the regular state change
        SSM.set_state(self, newState, timer)

        # when completed or aborted, remove tracking
        if (newState == COMPLETED) or (newState == ABORTED):
            if _debug: ServerSSM._debug("    - remove from active transactions")
            self.ssmSAP.serverTransactions.remove(self)

            if _debug: ServerSSM._debug("    - release device information")
            self.ssmSAP.deviceInfoCache.release_device_info(self.remoteDevice)

    def request(self, apdu):
        """This function is called by transaction functions to send
        to the application."""
        if _debug: ServerSSM._debug("request %r", apdu)

        # make sure it has a good source and destination
        apdu.pduSource = self.remoteDevice.address
        apdu.pduDestination = None

        # send it via the device
        self.ssmSAP.sap_request(apdu)

    def indication(self, apdu):
        """This function is called for each downstream packet related to
        the transaction."""
        if _debug: ServerSSM._debug("indication %r", apdu)

        if self.state == IDLE:
            self.idle(apdu)
        elif self.state == SEGMENTED_REQUEST:
            self.segmented_request(apdu)
        elif self.state == AWAIT_RESPONSE:
            self.await_response(apdu)
        elif self.state == SEGMENTED_RESPONSE:
            self.segmented_response(apdu)
        else:
            if _debug: ServerSSM._debug("    - invalid state")

    def response(self, apdu):
        """This function is called by transaction functions when they want
        to send a message to the device."""
        if _debug: ServerSSM._debug("response %r", apdu)

        # make sure it has a good source and destination
        apdu.pduSource = None
        apdu.pduDestination = self.remoteDevice.address

        # send it via the device
        self.ssmSAP.request(apdu)

    def confirmation(self, apdu):
        """This function is called when the application has provided a response
        and needs it to be sent to the client."""
        if _debug: ServerSSM._debug("confirmation %r", apdu)

        # check to see we are in the correct state
        if self.state != AWAIT_RESPONSE:
            if _debug: ServerSSM._debug("    - warning: not expecting a response")

        # abort response
        if (apdu.apduType == AbortPDU.pduType):
            if _debug: ServerSSM._debug("    - abort")

            self.set_state(ABORTED)

            # send the response to the device
            self.response(apdu)
            return

        # simple response
        if (apdu.apduType == SimpleAckPDU.pduType) or (apdu.apduType == ErrorPDU.pduType) or (apdu.apduType == RejectPDU.pduType):
            if _debug: ServerSSM._debug("    - simple ack, error, or reject")

            # transaction completed
            self.set_state(COMPLETED)

            # send the response to the device
            self.response(apdu)
            return

        # complex ack
        if (apdu.apduType == ComplexAckPDU.pduType):
            if _debug: ServerSSM._debug("    - complex ack")

            # save the response and set the segmentation context
            self.set_segmentation_context(apdu)

            # the segment size is the minimum of the maximum size I can transmit
            # (assumed to have no local buffer limitations), the maximum conveyable
            # by the internetwork to the remote device, and the maximum APDU size
            # accepted by the remote device.
            self.segmentSize = min(self.remoteDevice.maxNpduLength, self.remoteDevice.maxApduLengthAccepted)
            if _debug: ServerSSM._debug("    - segment size: %r", self.segmentSize)

            # compute the segment count ### minus the header?
            if not apdu.pduData:
                # always at least one segment
                self.segmentCount = 1
            else:
                # split into chunks, maybe need one more
                self.segmentCount, more = divmod(len(apdu.pduData), self.segmentSize)
                if more:
                    self.segmentCount += 1
            if _debug: ServerSSM._debug("    - segment count: %r", self.segmentCount)

            # make sure we support segmented transmit if we need to
            if self.segmentCount > 1:
                if _debug: ServerSSM._debug("    - segmentation required, %d segments", self.segmentCount)

                # make sure we support segmented transmit
                if self.ssmSAP.segmentationSupported not in ('segmentedTransmit', 'segmentedBoth'):
                    if _debug: ServerSSM._debug("    - server can't send segmented responses")
                    abort = self.abort(AbortReason.segmentationNotSupported)
                    self.reponse(abort)
                    return

                # make sure client supports segmented receive
                if self.remoteDevice.segmentationSupported not in ('segmentedReceive', 'segmentedBoth'):
                    if _debug: ServerSSM._debug("    - client can't receive segmented responses")
                    abort = self.abort(AbortReason.segmentationNotSupported)
                    self.response(abort)
                    return

            ### check for APDUTooLong?

            # initialize the state
            self.segmentRetryCount = 0
            self.initialSequenceNumber = 0
            self.proposedWindowSize = self.ssmSAP.maxSegmentsAccepted
            self.actualWindowSize = 1

            # send out the first segment (or the whole thing)
            if self.segmentCount == 1:
                self.response(apdu)
                self.set_state(COMPLETED)
            else:
                self.response(self.get_segment(0))
                self.set_state(SEGMENTED_RESPONSE, self.ssmSAP.segmentTimeout)

        else:
            raise RuntimeError("invalid APDU (4)")

    def process_task(self):
        """This function is called when the client has failed to send all of the
        segments of a segmented request, the application has taken too long to
        complete the request, or the client failed to ack the segments of a
        segmented response."""
        if _debug: ServerSSM._debug("process_task")

        if self.state == SEGMENTED_REQUEST:
            self.segmented_request_timeout()
        elif self.state == AWAIT_RESPONSE:
            self.await_response_timeout()
        elif self.state == SEGMENTED_RESPONSE:
            self.segmented_response_timeout()
        elif self.state == COMPLETED:
            pass
        elif self.state == ABORTED:
            pass
        else:
            if _debug: ServerSSM._debug("invalid state")
            raise RuntimeError("invalid state")

    def abort(self, reason):
        """This function is called when the application would like to abort the
        transaction.  There is no notification back to the application."""
        if _debug: ServerSSM._debug("abort %r", reason)

        # change the state to aborted
        self.set_state(ABORTED)

        # return an abort APDU
        return AbortPDU(True, self.invokeID, reason)

    def idle(self, apdu):
        if _debug: ServerSSM._debug("idle %r", apdu)

        # make sure we're getting confirmed requests
        if not isinstance(apdu, ConfirmedRequestPDU):
            raise RuntimeError("invalid APDU (5)")

        # save the invoke ID
        self.invokeID = apdu.apduInvokeID
        if _debug: ServerSSM._debug("    - invoke ID: %r", self.invokeID)

        # make sure the device information is synced with the request
        if apdu.apduSA:
            if self.remoteDevice.segmentationSupported == 'noSegmentation':
                if _debug: ServerSSM._debug("    - client actually supports segmented receive")
                self.remoteDevice.segmentationSupported = 'segmentedReceive'

                if _debug: ServerSSM._debug("    - tell the cache the info has been updated")
                self.ssmSAP.deviceInfoCache.update_device_info(self.remoteDevice)

            elif self.remoteDevice.segmentationSupported == 'segmentedTransmit':
                if _debug: ServerSSM._debug("    - client actually supports both segmented transmit and receive")
                self.remoteDevice.segmentationSupported = 'segmentedBoth'

                if _debug: ServerSSM._debug("    - tell the cache the info has been updated")
                self.ssmSAP.deviceInfoCache.update_device_info(self.remoteDevice)

            elif self.remoteDevice.segmentationSupported == 'segmentedReceive':
                pass

            elif self.remoteDevice.segmentationSupported == 'segmentedBoth':
                pass

            else:
                raise RuntimeError("invalid segmentation supported in device info")

        if apdu.apduMaxSegs != self.remoteDevice.maxSegmentsAccepted:
            if _debug: ServerSSM._debug("    - update maximum segments accepted?")
        if apdu.apduMaxResp != self.remoteDevice.maxApduLengthAccepted:
            if _debug: ServerSSM._debug("    - update maximum max APDU length accepted?")

        # save the number of segments the client is willing to accept in the ack
        self.maxSegmentsAccepted = apdu.apduMaxSegs

        # unsegmented request
        if not apdu.apduSeg:
            self.set_state(AWAIT_RESPONSE, self.ssmSAP.applicationTimeout)
            self.request(apdu)
            return

        # make sure we support segmented requests
        if self.ssmSAP.segmentationSupported not in ('segmentedReceive', 'segmentedBoth'):
            abort = self.abort(AbortReason.segmentationNotSupported)
            self.response(abort)
            return

        # save the request and set the segmentation context
        self.set_segmentation_context(apdu)

        # the window size is the minimum of what I'm willing to receive and
        # what the device has said it would like to send
        self.actualWindowSize = min(apdu.apduWin, self.ssmSAP.maxSegmentsAccepted)

        # initialize the state
        self.lastSequenceNumber = 0
        self.initialSequenceNumber = 0
        self.set_state(SEGMENTED_REQUEST, self.ssmSAP.segmentTimeout)

        # send back a segment ack
        segack = SegmentAckPDU( 0, 1, self.invokeID, self.initialSequenceNumber, self.actualWindowSize )
        if _debug: ServerSSM._debug("    - segAck: %r", segack)

        self.response(segack)

    def segmented_request(self, apdu):
        if _debug: ServerSSM._debug("segmented_request %r", apdu)

        # some kind of problem
        if (apdu.apduType == AbortPDU.pduType):
            self.set_state(COMPLETED)
            self.response(apdu)
            return

        # the only messages we should be getting are confirmed requests
        elif (apdu.apduType != ConfirmedRequestPDU.pduType):
            abort = self.abort(AbortReason.invalidApduInThisState)
            self.request(abort) # send it to the device
            self.response(abort) # send it to the application
            return

        # it must be segmented
        elif not apdu.apduSeg:
            abort = self.abort(AbortReason.invalidApduInThisState)
            self.request(abort) # send it to the application
            self.response(abort) # send it to the device
            return

        # proper segment number
        if apdu.apduSeq != (self.lastSequenceNumber + 1) % 256:
            if _debug: ServerSSM._debug("    - segment %d received out of order, should be %d", apdu.apduSeq, (self.lastSequenceNumber + 1) % 256)

            # segment received out of order
            self.restart_timer(self.ssmSAP.segmentTimeout)

            # send back a segment ack
            segack = SegmentAckPDU( 1, 1, self.invokeID, self.initialSequenceNumber, self.actualWindowSize )

            self.response(segack)
            return

        # add the data
        self.append_segment(apdu)

        # update the sequence number
        self.lastSequenceNumber = (self.lastSequenceNumber + 1) % 256

        # last segment?
        if not apdu.apduMor:
            if _debug: ServerSSM._debug("    - no more follows")

            # send back a final segment ack
            segack = SegmentAckPDU( 0, 1, self.invokeID, self.lastSequenceNumber, self.actualWindowSize )
            self.response(segack)

            # forward the whole thing to the application
            self.set_state(AWAIT_RESPONSE, self.ssmSAP.applicationTimeout)
            self.request(self.segmentAPDU)

        elif apdu.apduSeq == ((self.initialSequenceNumber + self.actualWindowSize) % 256):
                if _debug: ServerSSM._debug("    - last segment in the group")

                self.initialSequenceNumber = self.lastSequenceNumber
                self.restart_timer(self.ssmSAP.segmentTimeout)

                # send back a segment ack
                segack = SegmentAckPDU( 0, 1, self.invokeID, self.initialSequenceNumber, self.actualWindowSize )
                self.response(segack)

        else:
            # wait for more segments
            if _debug: ServerSSM._debug("    - wait for more segments")

            self.restart_timer(self.ssmSAP.segmentTimeout)

    def segmented_request_timeout(self):
        if _debug: ServerSSM._debug("segmented_request_timeout")

        # give up
        self.set_state(ABORTED)

    def await_response(self, apdu):
        if _debug: ServerSSM._debug("await_response %r", apdu)

        if isinstance(apdu, ConfirmedRequestPDU):
            if _debug: ServerSSM._debug("    - client is trying this request again")

        elif isinstance(apdu, AbortPDU):
            if _debug: ServerSSM._debug("    - client aborting this request")

            # forward abort to the application
            self.set_state(ABORTED)
            self.request(apdu)

        else:
            raise RuntimeError("invalid APDU (6)")

    def await_response_timeout(self):
        """This function is called when the application has taken too long
        to respond to a clients request.  The client has probably long since
        given up."""
        if _debug: ServerSSM._debug("await_response_timeout")

        abort = self.abort(AbortReason.serverTimeout)
        self.request(abort)

    def segmented_response(self, apdu):
        if _debug: ServerSSM._debug("segmented_response %r", apdu)

        # client is ready for the next segment
        if (apdu.apduType == SegmentAckPDU.pduType):
            if _debug: ServerSSM._debug("    - segment ack")

            # duplicate ack received?
            if not self.in_window(apdu.apduSeq, self.initialSequenceNumber):
                if _debug: ServerSSM._debug("    - not in window")
                self.restart_timer(self.ssmSAP.segmentTimeout)

            # final ack received?
            elif self.sentAllSegments:
                if _debug: ServerSSM._debug("    - all done sending response")
                self.set_state(COMPLETED)

            else:
                if _debug: ServerSSM._debug("    - more segments to send")

                self.initialSequenceNumber = (apdu.apduSeq + 1) % 256
                self.actualWindowSize = apdu.apduWin
                self.segmentRetryCount = 0
                self.FillWindow(self.initialSequenceNumber)
                self.restart_timer(self.ssmSAP.segmentTimeout)

        # some kind of problem
        elif (apdu.apduType == AbortPDU.pduType):
            self.set_state(COMPLETED)
            self.response(apdu)

        else:
            raise RuntimeError("invalid APDU (7)")

    def segmented_response_timeout(self):
        if _debug: ServerSSM._debug("segmented_response_timeout")

        # try again
        if self.segmentRetryCount < self.ssmSAP.retryCount:
            self.segmentRetryCount += 1
            self.start_timer(self.ssmSAP.segmentTimeout)
            self.FillWindow(self.initialSequenceNumber)
        else:
            # give up
            self.set_state(ABORTED)

#
#   StateMachineAccessPoint
#

@bacpypes_debugging
class StateMachineAccessPoint(Client, ServiceAccessPoint):

    def __init__(self, localDevice=None, deviceInfoCache=None, sap=None, cid=None):
        if _debug: StateMachineAccessPoint._debug("__init__ localDevice=%r deviceInfoCache=%r sap=%r cid=%r", localDevice, deviceInfoCache, sap, cid)

        # basic initialization
        Client.__init__(self, cid)
        ServiceAccessPoint.__init__(self, sap)

        # save a reference to the device information cache
        self.deviceInfoCache = deviceInfoCache

        # client settings
        self.nextInvokeID = 1
        self.clientTransactions = []

        # server settings
        self.serverTransactions = []

        # confirmed request defaults
        self.retryCount = 3
        self.retryTimeout = 3000
        self.maxApduLengthAccepted = 1024

        # segmentation defaults
        self.segmentationSupported = 'noSegmentation'
        self.segmentTimeout = 1500
        self.maxSegmentsAccepted = 8

        # local device object provides these
        if localDevice:
            self.retryCount = localDevice.numberOfApduRetries
            self.retryTimeout = localDevice.apduTimeout
            self.segmentationSupported = localDevice.segmentationSupported
            self.segmentTimeout = localDevice.apduSegmentTimeout
            self.maxSegmentsAccepted = localDevice.maxSegmentsAccepted
            self.maxApduLengthAccepted = localDevice.maxApduLengthAccepted

        # how long the state machine is willing to wait for the application
        # layer to form a response and send it
        self.applicationTimeout = 3000

    def get_next_invoke_id(self, addr):
        """Called by clients to get an unused invoke ID."""
        if _debug: StateMachineAccessPoint._debug("get_next_invoke_id")

        initialID = self.nextInvokeID
        while 1:
            invokeID = self.nextInvokeID
            self.nextInvokeID = (self.nextInvokeID + 1) % 256

            # see if we've checked for them all
            if initialID == self.nextInvokeID:
                raise RuntimeError("no available invoke ID")

            for tr in self.clientTransactions:
                if (invokeID == tr.invokeID) and (addr == tr.remoteDevice.address):
                    break
            else:
                break

        return invokeID

    def confirmation(self, pdu):
        """Packets coming up the stack are APDU's."""
        if _debug: StateMachineAccessPoint._debug("confirmation %r", pdu)

        # make a more focused interpretation
        atype = apdu_types.get(pdu.apduType)
        if not atype:
            StateMachineAccessPoint._warning("    - unknown apduType: %r", pdu.apduType)
            return

        # decode it
        apdu = atype()
        apdu.decode(pdu)
        if _debug: StateMachineAccessPoint._debug("    - apdu: %r", apdu)

        if isinstance(apdu, ConfirmedRequestPDU):
            # find duplicates of this request
            for tr in self.serverTransactions:
                if (apdu.pduSource == tr.remoteDevice.address) and (apdu.apduInvokeID == tr.invokeID):
                    break
            else:
                # find the remote device information
                remoteDevice = self.deviceInfoCache.get_device_info(apdu.pduSource)

                # build a server transaction
                tr = ServerSSM(self, remoteDevice)

                # add it to our transactions to track it
                self.serverTransactions.append(tr)

            # let it run with the apdu
            tr.indication(apdu)

        elif isinstance(apdu, UnconfirmedRequestPDU):
            # deliver directly to the application
            self.sap_request(apdu)

        elif isinstance(apdu, SimpleAckPDU) \
            or isinstance(apdu, ComplexAckPDU) \
            or isinstance(apdu, ErrorPDU) \
            or isinstance(apdu, RejectPDU):

            # find the client transaction this is acking
            for tr in self.clientTransactions:
                if (apdu.apduInvokeID == tr.invokeID) and (apdu.pduSource == tr.remoteDevice.address):
                    break
            else:
                return

            # send the packet on to the transaction
            tr.confirmation(apdu)

        elif isinstance(apdu, AbortPDU):
            # find the transaction being aborted
            if apdu.apduSrv:
                for tr in self.clientTransactions:
                    if (apdu.apduInvokeID == tr.invokeID) and (apdu.pduSource == tr.remoteDevice.address):
                        break
                else:
                    return

                # send the packet on to the transaction
                tr.confirmation(apdu)
            else:
                for tr in self.serverTransactions:
                    if (apdu.apduInvokeID == tr.invokeID) and (apdu.pduSource == tr.remoteDevice.address):
                        break
                else:
                    return

                # send the packet on to the transaction
                tr.indication(apdu)

        elif isinstance(apdu, SegmentAckPDU):
            # find the transaction being aborted
            if apdu.apduSrv:
                for tr in self.clientTransactions:
                    if (apdu.apduInvokeID == tr.invokeID) and (apdu.pduSource == tr.remoteDevice.address):
                        break
                else:
                    return

                # send the packet on to the transaction
                tr.confirmation(apdu)
            else:
                for tr in self.serverTransactions:
                    if (apdu.apduInvokeID == tr.invokeID) and (apdu.pduSource == tr.remoteDevice.address):
                        break
                else:
                    return

                # send the packet on to the transaction
                tr.indication(apdu)

        else:
            raise RuntimeError("invalid APDU (8)")

    def sap_indication(self, apdu):
        """This function is called when the application is requesting
        a new transaction as a client."""
        if _debug: StateMachineAccessPoint._debug("sap_indication %r", apdu)

        if isinstance(apdu, UnconfirmedRequestPDU):
            # deliver to the device
            self.request(apdu)

        elif isinstance(apdu, ConfirmedRequestPDU):
            # make sure it has an invoke ID
            if apdu.apduInvokeID is None:
                apdu.apduInvokeID = self.get_next_invoke_id(apdu.pduDestination)
            else:
                # verify the invoke ID isn't already being used
                for tr in self.clientTransactions:
                    if (apdu.apduInvokeID == tr.invokeID) and (apdu.pduDestination == tr.remoteDevice.address):
                        raise RuntimeError("invoke ID in use")

            # warning for bogus requests
            if (apdu.pduDestination.addrType != Address.localStationAddr) and (apdu.pduDestination.addrType != Address.remoteStationAddr):
                StateMachineAccessPoint._warning("%s is not a local or remote station", apdu.pduDestination)

            # find the remote device information
            remoteDevice = self.deviceInfoCache.get_device_info(apdu.pduDestination)
            if _debug: StateMachineAccessPoint._debug("    - remoteDevice: %r", remoteDevice)

            # create a client transaction state machine
            tr = ClientSSM(self, remoteDevice)
            if _debug: StateMachineAccessPoint._debug("    - client segmentation state machine: %r", tr)

            # add it to our transactions to track it
            self.clientTransactions.append(tr)

            # let it run
            tr.indication(apdu)

        else:
            raise RuntimeError("invalid APDU (9)")

    def sap_confirmation(self, apdu):
        """This function is called when the application is responding
        to a request, the apdu may be a simple ack, complex ack, error, reject or abort."""
        if _debug: StateMachineAccessPoint._debug("sap_confirmation %r", apdu)

        if isinstance(apdu, SimpleAckPDU) \
                or isinstance(apdu, ComplexAckPDU) \
                or isinstance(apdu, ErrorPDU) \
                or isinstance(apdu, RejectPDU) \
                or isinstance(apdu, AbortPDU):
            # find the appropriate server transaction
            for tr in self.serverTransactions:
                if (apdu.apduInvokeID == tr.invokeID) and (apdu.pduDestination == tr.remoteDevice.address):
                    break
            else:
                return

            # pass control to the transaction
            tr.confirmation(apdu)

        else:
            raise RuntimeError("invalid APDU (10)")

#
#   ApplicationServiceAccessPoint
#

@bacpypes_debugging
class ApplicationServiceAccessPoint(ApplicationServiceElement, ServiceAccessPoint):

    def __init__(self, aseID=None, sapID=None):
        if _debug: ApplicationServiceAccessPoint._debug("__init__ aseID=%r sapID=%r", aseID, sapID)
        ApplicationServiceElement.__init__(self, aseID)
        ServiceAccessPoint.__init__(self, sapID)

    def indication(self, apdu):
        if _debug: ApplicationServiceAccessPoint._debug("indication %r", apdu)

        if isinstance(apdu, ConfirmedRequestPDU):
            atype = confirmed_request_types.get(apdu.apduService)
            if not atype:
                if _debug: ApplicationServiceAccessPoint._debug("    - no confirmed request decoder")
                return

            # assume no errors found
            error_found = None

            try:
                xpdu = atype()
                xpdu.decode(apdu)
            except RejectException as err:
                ApplicationServiceAccessPoint._debug("    - decoding reject: %r", err)
                error_found = err
            except AbortException as err:
                ApplicationServiceAccessPoint._debug("    - decoding abort: %r", err)
                error_found = err

            # no error so far, keep going
            if not error_found:
                if _debug: ApplicationServiceAccessPoint._debug("    - no decoding error")

                try:
                    # forward the decoded packet
                    self.sap_request(xpdu)
                except RejectException as err:
                    ApplicationServiceAccessPoint._debug("    - execution reject: %r", err)
                    error_found = err
                except AbortException as err:
                    ApplicationServiceAccessPoint._debug("    - execution abort: %r", err)
                    error_found = err

            # if there was an error, send it back to the client
            if isinstance(error_found, RejectException):
                if _debug: ApplicationServiceAccessPoint._debug("    - reject exception: %r", error_found)

                reject_pdu = RejectPDU(reason=error_found.rejectReason)
                reject_pdu.set_context(apdu)
                if _debug: ApplicationServiceAccessPoint._debug("    - reject_pdu: %r", reject_pdu)

                # send it to the client
                self.response(reject_pdu)

            elif isinstance(error_found, AbortException):
                if _debug: ApplicationServiceAccessPoint._debug("    - abort exception: %r", error_found)

                abort_pdu = AbortPDU(reason=error_found.abortReason)
                abort_pdu.set_context(apdu)
                if _debug: ApplicationServiceAccessPoint._debug("    - abort_pdu: %r", abort_pdu)

                # send it to the client
                self.response(abort_pdu)

        elif isinstance(apdu, UnconfirmedRequestPDU):
            atype = unconfirmed_request_types.get(apdu.apduService)
            if not atype:
                if _debug: ApplicationServiceAccessPoint._debug("    - no unconfirmed request decoder")
                return

            try:
                xpdu = atype()
                xpdu.decode(apdu)
            except RejectException as err:
                ApplicationServiceAccessPoint._debug("    - decoding reject: %r", err)
                return
            except AbortException as err:
                ApplicationServiceAccessPoint._debug("    - decoding abort: %r", err)
                return

            try:
                # forward the decoded packet
                self.sap_request(xpdu)
            except RejectException as err:
                ApplicationServiceAccessPoint._debug("    - execution reject: %r", err)
            except AbortException as err:
                ApplicationServiceAccessPoint._debug("    - execution abort: %r", err)

        else:
            if _debug: ApplicationServiceAccessPoint._debug("    - unknown PDU type?!")

    def sap_indication(self, apdu):
        if _debug: ApplicationServiceAccessPoint._debug("sap_indication %r", apdu)

        if isinstance(apdu, ConfirmedRequestPDU):
            try:
                xpdu = ConfirmedRequestPDU()
                apdu.encode(xpdu)
                apdu._xpdu = xpdu
            except Exception as err:
                ApplicationServiceAccessPoint._exception("confirmed request encoding error: %r", err)
                return

        elif isinstance(apdu, UnconfirmedRequestPDU):
            try:
                xpdu = UnconfirmedRequestPDU()
                apdu.encode(xpdu)
                apdu._xpdu = xpdu
            except Exception as err:
                ApplicationServiceAccessPoint._exception("unconfirmed request encoding error: %r", err)
                return

        else:
            if _debug: ApplicationServiceAccessPoint._debug("    - unknown PDU type?!")
            return

        if _debug: ApplicationServiceAccessPoint._debug("    - xpdu %r", xpdu)

        # forward the encoded packet
        self.request(xpdu)

        # if the upper layers of the application did not assign an invoke ID,
        # copy the one that was assigned on its way down the stack
        if isinstance(apdu, ConfirmedRequestPDU) and apdu.apduInvokeID is None:
            if _debug: ApplicationServiceAccessPoint._debug("    - pass invoke ID upstream %r", xpdu.apduInvokeID)
            apdu.apduInvokeID = xpdu.apduInvokeID

    def confirmation(self, apdu):
        if _debug: ApplicationServiceAccessPoint._debug("confirmation %r", apdu)

        if isinstance(apdu, SimpleAckPDU):
            xpdu = apdu

        elif isinstance(apdu, ComplexAckPDU):
            atype = complex_ack_types.get(apdu.apduService)
            if not atype:
                if _debug: ApplicationServiceAccessPoint._debug("    - no complex ack decoder")
                return

            try:
                xpdu = atype()
                xpdu.decode(apdu)
            except Exception as err:
                ApplicationServiceAccessPoint._exception("unconfirmed request decoding error: %r", err)
                return

        elif isinstance(apdu, ErrorPDU):
            atype = error_types.get(apdu.apduService)
            if not atype:
                if _debug: ApplicationServiceAccessPoint._debug("    - no special error decoder")
                atype = Error

            try:
                xpdu = atype()
                xpdu.decode(apdu)
            except Exception as err:
                ApplicationServiceAccessPoint._exception("error PDU decoding error: %r", err)
                xpdu = Error(errorClass=0, errorCode=0)

        elif isinstance(apdu, RejectPDU):
            xpdu = apdu

        elif isinstance(apdu, AbortPDU):
            xpdu = apdu

        else:
            if _debug: ApplicationServiceAccessPoint._debug("    - unknown PDU type")
            return

        if _debug: ApplicationServiceAccessPoint._debug("    - xpdu %r", xpdu)

        # forward the decoded packet
        self.sap_response(xpdu)

    def sap_confirmation(self, apdu):
        if _debug: ApplicationServiceAccessPoint._debug("sap_confirmation %r", apdu)

        if isinstance(apdu, SimpleAckPDU):
            xpdu = apdu

        elif isinstance(apdu, ComplexAckPDU):
            xpdu = ComplexAckPDU()
            apdu.encode(xpdu)

        elif isinstance(apdu, ErrorPDU):
            xpdu = ErrorPDU()
            apdu.encode(xpdu)

        elif isinstance(apdu, RejectPDU):
            xpdu = apdu

        elif isinstance(apdu, AbortPDU):
            xpdu = apdu

        else:
            if _debug: ApplicationServiceAccessPoint._debug("    - unknown PDU type")
            return

        if _debug: ApplicationServiceAccessPoint._debug("    - xpdu %r", xpdu)

        # forward the encoded packet
        self.response(xpdu)
