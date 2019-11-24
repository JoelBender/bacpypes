#!/usr/bin/env python

"""
Read some BACnet point values, save them as key/value JSON blobs in Redis,
and publish them to stream.
"""

import json
import redis
from time import time as _time

from collections import deque

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import JSONArgumentParser

from bacpypes.core import run, stop, deferred
from bacpypes.iocb import IOCB

from bacpypes.pdu import Address
from bacpypes.object import get_datatype

from bacpypes.apdu import ReadPropertyRequest
from bacpypes.primitivedata import Unsigned, ObjectIdentifier
from bacpypes.constructeddata import Array

from bacpypes.app import BIPSimpleApplication
from bacpypes.local.device import LocalDeviceObject

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
this_application = None
redis_connection = None
redis_stream = None


@bacpypes_debugging
class ReadPointListApplication(BIPSimpleApplication):
    def __init__(self, point_list, *args):
        if _debug:
            ReadPointListApplication._debug("__init__ %r, %r", point_list, args)
        BIPSimpleApplication.__init__(self, *args)

        # turn the point list into a queue
        self.point_queue = deque(point_list)

    def next_request(self):
        if _debug:
            ReadPointListApplication._debug("next_request")

        # check to see if we're done
        if not self.point_queue:
            if _debug:
                ReadPointListApplication._debug("    - done")
            stop()
            return

        # get the next request
        point_info = self.point_queue.popleft()
        if _debug:
            ReadPointListApplication._debug("    - point_info: %r", point_info)

        # build a request
        request = ReadPropertyRequest(
            destination=Address(point_info["address"]),
            objectIdentifier=ObjectIdentifier(point_info["objectIdentifier"]).value,
            propertyIdentifier=point_info.get("propertyIdentifier", "presentValue"),
        )
        if _debug:
            ReadPointListApplication._debug("    - request: %r", request)

        # make an IOCB
        iocb = IOCB(request)
        iocb.point_info = point_info

        # set a callback for the response
        iocb.add_callback(self.complete_request)
        if _debug:
            ReadPointListApplication._debug("    - iocb: %r", iocb)

        # send the request
        this_application.request_io(iocb)

    def complete_request(self, iocb):
        if _debug:
            ReadPointListApplication._debug("complete_request %r", iocb)
        global redis_connection, redis_stream

        # point information has the key
        point_info = iocb.point_info
        if _debug:
            ReadPointListApplication._debug("    - point_info: %r", point_info)

        if iocb.ioResponse:
            apdu = iocb.ioResponse

            # find the datatype
            datatype = get_datatype(apdu.objectIdentifier[0], apdu.propertyIdentifier)
            if _debug:
                ReadPointListApplication._debug("    - datatype: %r", datatype)
            if not datatype:
                raise TypeError("unknown datatype")

            # special case for array parts, others are managed by cast_out
            if issubclass(datatype, Array) and (apdu.propertyArrayIndex is not None):
                if apdu.propertyArrayIndex == 0:
                    value = apdu.propertyValue.cast_out(Unsigned)
                else:
                    value = apdu.propertyValue.cast_out(datatype.subtype)
            else:
                value = apdu.propertyValue.cast_out(datatype)
            if _debug:
                ReadPointListApplication._debug("    - value: %r", value)

            # create a blob for the data
            point_data = {"timestamp": _time(), "value": value}

        if iocb.ioError:
            if _debug:
                ReadPointListApplication._debug("    - error: %r", iocb.ioError)

            # create a blob for the data
            point_data = {"timestamp": _time(), "error": iocb.ioError}

        # save the content as a JSON
        redis_connection.set(point_info["key"], json.dumps(point_data))

        # update the point info to add the key, save it in the stream
        point_data["key"] = point_info["key"]
        redis_connection.xadd(redis_stream, point_data)

        # fire off another request
        deferred(self.next_request)


def main():
    global this_application, redis_connection, redis_stream

    # parse the command line arguments
    parser = JSONArgumentParser(description=__doc__)

    if _debug:
        _log.debug("initialization")

    args = parser.parse_args()
    if _debug:
        _log.debug("    - args: %r", args)

    # settings for connecting to the redis server
    redis_settings = args.json["redis"]
    if _debug:
        _log.debug("    - redis_settings: %r", redis_settings)

    # addtional settings for this application
    redis_stream = args.json["redis-stream"]
    if _debug:
        _log.debug("    - redis_stream: %r", redis_stream)

    # connect to Redis
    redis_connection = redis.Redis(**redis_settings)
    if _debug:
        _log.debug("    - redis_connection: %r", redis_connection)

    # make a device object
    local_device = args.json["local-device"]
    this_device = LocalDeviceObject(**local_device)
    if _debug:
        _log.debug("    - this_device: %r", this_device)

    # get the point list
    point_list = args.json["point-list"]
    if _debug:
        _log.debug("    - point_list: %r", point_list)

    # make a simple application
    this_application = ReadPointListApplication(
        point_list, this_device, local_device.address
    )

    # fire off a request when the core has a chance
    deferred(this_application.next_request)

    _log.debug("running")

    run()

    _log.debug("fini")


if __name__ == "__main__":
    main()
