#!/usr/bin/python

#
#   ConfigurationError
#

class ConfigurationError(ValueError):

    """This error is raised when there is a configuration problem such as
    bindings between layers or required parameters that are missing.
    """

    def __init__(self, *args):
        self.args = args

#
#   EncodingError
#

class EncodingError(ValueError):

    """This error is raised if there is a problem during encoding.
    """

    def __init__(self, *args):
        self.args = args

#
#   DecodingError
#

class DecodingError(ValueError):

    """This error is raised if there is a problem during decoding.
    """

    def __init__(self, *args):
        self.args = args

#
#   ExecutionError
#

class ExecutionError(RuntimeError):

    """This error is raised for if there is an error during the execution of
    a service or function at the application layer of stack and the error
    translated into an ErrorPDU.
    """

    def __init__(self, errorClass, errorCode):
        self.errorClass = errorClass
        self.errorCode = errorCode
        self.args = (errorClass, errorCode)


#
#   Reject Exception Family
#

class RejectException(Exception):

    """Exceptions in this family correspond to reject reasons.  If the
    application raises one of these errors while processing a confirmed
    service request, the stack will form an appropriate RejectPDU and
    send it to the client.
    """

    rejectReason = None

    def __init__(self, *args):
        if not self.rejectReason:
            raise NotImplementedError("use a derived class")

        # save the args
        self.args = args


class RejectOther(RejectException):

    """Generated in response to a confirmed request APDU that contains a
    syntax error for which an error code has not been explicitly defined.
    """

    rejectReason = 'other'


class RejectBufferOverflow(RejectException):

    """A buffer capacity has been exceeded.
    """

    rejectReason = 'bufferOverflow'


class InconsistentParameters(RejectException):

    """Generated in response to a confirmed request APDU that omits a
    conditional service argument that should be present or contains a
    conditional service argument that should not be present. This condition
    could also elicit a Reject PDU with a Reject Reason of INVALID_TAG.
    """

    rejectReason = 'inconsistentParameters'


class InvalidParameterDatatype(RejectException):

    """Generated in response to a confirmed request APDU in which the encoding
    of one or more of the service parameters does not follow the correct type
    specification. This condition could also elicit a Reject PDU with a Reject
    Reason of INVALID_TAG.
    """

    rejectReason = 'invalidParameterDatatype'


class InvalidTag(RejectException):

    """While parsing a message, an invalid tag was encountered. Since an
    invalid tag could confuse the parsing logic, any of the following Reject
    Reasons may also be generated in response to a confirmed request
    containing an invalid tag: INCONSISTENT_PARAMETERS,
    INVALID_PARAMETER_DATA_TYPE, MISSING_REQUIRED_PARAMETER, and
    TOO_MANY_ARGUMENTS.
    """

    rejectReason = 'invalidTag'


class MissingRequiredParameter(RejectException):

    """Generated in response to a confirmed request APDU that is missing at
    least one mandatory service argument. This condition could also elicit a
    Reject PDU with a Reject Reason of INVALID_TAG.
    """

    rejectReason = 'missingRequiredParameter'


class ParameterOutOfRange(RejectException):

    """Generated in response to a confirmed request APDU that conveys a
    parameter whose value is outside the range defined for this service.
    """

    rejectReason = 'parameterOutOfRange'


class TooManyArguments(RejectException):

    """Generated in response to a confirmed request APDU in which the total
    number of service arguments is greater than specified for the service.
    This condition could also elicit a Reject PDU with a Reject Reason of
    INVALID_TAG.
    """

    rejectReason = 'tooManyArguments'


class UndefinedEnumeration(RejectException):

    """Generated in response to a confirmed request APDU in which one or
    more of the service parameters is decoded as an enumeration that is not
    defined by the type specification of this parameter.
    """

    rejectReason = 'undefinedEnumeration'


class UnrecognizedService(RejectException):

    """Generated in response to a confirmed request APDU in which the Service
    Choice field specifies an unknown or unsupported service.
    """

    rejectReason = 'unrecognizedService'


#
#   Abort Exception Family
#

class AbortException(Exception):

    """Exceptions in this family correspond to abort reasons.  If the
    application raises one of these errors while processing a confirmed
    service request, the stack will form an appropriate AbortPDU and
    send it to the client.
    """

    abortReason = None

    def __init__(self, *args):
        if not self.abortReason:
            raise NotImplementedError("use a derived class")

        # save the args
        self.args = args


class AbortOther(AbortException):

    """This abort reason is returned for a reason other than any of those
    for which an error code has not been explicitly defined.
    """

    abortReason = 'other'


class AbortBufferOverflow(AbortException):

    """A buffer capacity has been exceeded.
    """

    abortReason = 'bufferOverflow'


class InvalidAPDUInThisState(AbortException):

    """Generated in response to an APDU that is not expected in the present
    state of the Transaction State Machine.
    """

    abortReason = 'invalidApduInThisState'


class PreemptedByHigherPriorityTask(AbortException):

    """The transaction shall be aborted to permit higher priority processing.
    """

    abortReason = 'preemptedByHigherPriorityTask'


class SegmentationNotSupported(AbortException):

    """Generated in response to an APDU that has its segmentation bit set to
    TRUE when the receiving device does not support segmentation. It is also
    generated when a BACnet-ComplexACK-PDU is large enough to require
    segmentation but it cannot be transmitted because either the transmitting
    device or the receiving device does not support segmentation.
    """

    abortReason = 'segmentationNotSupported'


class SecurityError(AbortException):

    """The Transaction is aborted due to receipt of a security error.
    """

    abortReason = 'securityError'


class InsufficientSecurity(AbortException):

    """The transaction is aborted due to receipt of a PDU secured differently
    than the original PDU of the transaction.
    """

    abortReason = 'insufficientSecurity'


class WindowSizeOutOfRange(AbortException):

    """A device receives a request that is segmented, or receives any segment
    of a segmented request, where the Proposed Window Size field of the PDU
    header is either zero or greater than 127.
    """

    abortReason = 'windowSizeOutOfRange'


class ApplicationExceededReplyTime(AbortException):

    """A device receives a confirmed request but its application layer has not
    responded within the published APDU Timeout period.
    """

    abortReason = 'applicationExceededReplyTime'


class OutOfResources(AbortException):

    """A device receives a request but cannot start processing because it has
    run out of some internal resource.
    """

    abortReason = 'outOfResources'


class TSMTimeout(AbortException):

    """A transaction state machine timer exceeded the timeout applicable for
    the current state, causing the transaction machine to abort the
    transaction.
    """

    abortReason = 'tsmTimeout'


class APDUTooLong(AbortException):

    """An APDU was received from the local application program whose overall
    size exceeds the maximum transmittable length or exceeds the maximum number
    of segments accepted by the server.
    """

    abortReason = 'apduTooLong'


class ServerTimeout(AbortException):

    """BACpypes specific.
    """

    abortReason = 'serverTimeout'


class NoResponse(AbortException):

    """BACpypes specific.
    """

    abortReason = 'noResponse'
