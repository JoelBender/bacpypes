#!/usr/bin/env python

"""
Server with a Trend Log Object
"""

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser

from bacpypes.core import run
from bacpypes.errors import ExecutionError
from bacpypes.primitivedata import Date, Time
from bacpypes.constructeddata import Array, List, SequenceOfAny
from bacpypes.basetypes import DateTime, LogRecord, LogRecordLogDatum, StatusFlags
from bacpypes.apdu import ReadRangeACK

from bacpypes.app import BIPSimpleApplication
from bacpypes.local.device import LocalDeviceObject
from bacpypes.object import PropertyError, TrendLogObject


# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
this_application = None


#
#   ReadRangeApplication
#


@bacpypes_debugging
class ReadRangeApplication(BIPSimpleApplication):
    def __init__(self, *args):
        if _debug:
            ReadRangeApplication._debug("__init__ %r", args)
        BIPSimpleApplication.__init__(self, *args)

    def do_ReadRangeRequest(self, apdu):
        if _debug:
            ReadRangeApplication._debug("do_ReadRangeRequest %r", apdu)

        # extract the object identifier
        objId = apdu.objectIdentifier

        # get the object
        obj = self.get_object_id(objId)
        if _debug:
            ReadRangeApplication._debug("    - object: %r", obj)

        if not obj:
            raise ExecutionError(errorClass="object", errorCode="unknownObject")

        # get the datatype
        datatype = obj.get_datatype(apdu.propertyIdentifier)
        if _debug:
            ReadRangeApplication._debug("    - datatype: %r", datatype)

        # must be a list, or an array of lists
        if issubclass(datatype, List):
            pass
        elif (
            (apdu.propertyArrayIndex is not None)
            and issubclass(datatype, Array)
            and issubclass(datatype.subtype, List)
        ):
            pass
        else:
            raise ExecutionError(errorClass="property", errorCode="propertyIsNotAList")

        # get the value
        value = obj.ReadProperty(apdu.propertyIdentifier, apdu.propertyArrayIndex)
        if _debug:
            ReadRangeApplication._debug("    - value: %r", value)
        if value is None:
            raise PropertyError(apdu.propertyIdentifier)

        # this is an ack
        resp = ReadRangeACK(context=apdu)
        resp.objectIdentifier = objId
        resp.propertyIdentifier = apdu.propertyIdentifier
        resp.propertyArrayIndex = apdu.propertyArrayIndex

        resp.resultFlags = [1, 1, 0]
        resp.itemCount = len(value)

        # save the result in the item data
        resp.itemData = SequenceOfAny()
        resp.itemData.cast_in(datatype(value))
        if _debug:
            ReadRangeApplication._debug("    - resp: %r", resp)

        # return the result
        self.response(resp)


#
#   __main__
#


def main():
    global this_application

    # parse the command line arguments
    args = ConfigArgumentParser(description=__doc__).parse_args()

    if _debug:
        _log.debug("initialization")
    if _debug:
        _log.debug("    - args: %r", args)

    # make a device object
    this_device = LocalDeviceObject(ini=args.ini)
    if _debug:
        _log.debug("    - this_device: %r", this_device)

    # make a simple application
    this_application = ReadRangeApplication(this_device, args.ini.address)

    timestamp = DateTime(date=Date().now().value, time=Time().now().value)
    # log_status = LogStatus([0,0,0])
    log_record_datum = LogRecordLogDatum(booleanValue=False)
    status_flags = StatusFlags([0, 0, 0, 0])
    log_record = LogRecord(
        timestamp=timestamp, logDatum=log_record_datum, statusFlags=status_flags
    )

    trend_log_object = TrendLogObject(
        objectIdentifier=("trendLog", 1),
        objectName="Trend-Log-1",
        logBuffer=[log_record],
    )
    _log.debug("    - trend_log_object: %r", trend_log_object)
    this_application.add_object(trend_log_object)

    _log.debug("running")

    run()

    _log.debug("fini")


if __name__ == "__main__":
    main()
