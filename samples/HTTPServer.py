#!/usr/bin/python

"""
HTTPServer
"""

import os
import threading
import json
import zlib

from collections import OrderedDict

try:
    from urlparse import urlparse, parse_qs
    from SocketServer import ThreadingMixIn, TCPServer
    from SimpleHTTPServer import SimpleHTTPRequestHandler
except ImportError:
    from urllib.parse import urlparse, parse_qs
    from socketserver import ThreadingMixIn, TCPServer
    from http.server import SimpleHTTPRequestHandler

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser

from bacpypes.core import run, deferred
from bacpypes.iocb import IOCB

from bacpypes.pdu import Address, GlobalBroadcast
from bacpypes.apdu import ReadPropertyRequest, WhoIsRequest
from bacpypes.primitivedata import Unsigned, ObjectIdentifier
from bacpypes.constructeddata import Array

from bacpypes.app import BIPSimpleApplication
from bacpypes.object import get_object_class, get_datatype
from bacpypes.local.device import LocalDeviceObject

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# settings
HOST = os.getenv("HOST", "")
PORT = int(os.getenv("PORT", 8080))

# reference a simple application
this_application = None
server = None

# favorite icon
favicon = zlib.decompress(
    b"x\x9c\xb5\x93\xcdN\xdb@\x14\x85\x07\x95\x07\xc8\x8amYv\xc9#\xe4\x11x\x04\x96}"
    b'\x8c\x88\x1dl\xa0\x9b\xb6A\xa2)\x0bVTB\xa9"\xa5?*I\x16\xad"\x84d\x84DE\x93'
    b"\x14;v\xc01M\xe2$\x988\xb1l\x9d\xde;v\\\x03\x89TU\xea\xb5N\xe4\xb9\x9a\xef"
    b"\x1c\xcfO\x84X\xa0'\x95\x12\xf4\xbb,\x9e/\n\xb1$\x84xF\xa2\x16u\xc2>WzQ\xfc"
    b"\xf7\xca\xad\xafo\x91T\xd2\x1ai\xe5\x1fx[\xf9\xf4\x01\xc57\xbb\xd8\xdf\xd8"
    b"\x00\x8d\x11\xf9\x95\x12\xda\x9a\xc3\xae\xe5_\xbdDpk\x03\xc3\xaeT\xd0\xb3\xd0"
    b">?\x83Z\xfd\x86Z\xa5\x84\x1fG_\xa4\xe7\x1c^\xa9W\xbfJ\xfe\xb4\xf0\x0e^\xdb"
    b"\x88}0 \xafA\x0f\xa3+c&O\xbd\xf4\xc1\xf6\xb6d\x9d\xc6\x05\xdcVSz\xb0x\x1c\x10"
    b"\x0fo\x02\xc7\xd0\xe7\xf1%\xe5\xf3\xc78\xdb\xf9Y\x93\x1eI\x1f\xf8>\xfa\xb5"
    b"\x8bG<\x8dW\x0f^\x84\xd9\xee\xb5~\x8f\xe1w\xaf{\x83\x80\xb2\xbd\xe1\x10\x83"
    b"\x88'\xa5\x12\xbcZ?9\x8e\xb3%\xd3\xeb`\xd4\xd2\xffdS\xb9\x96\x89!}W!\xfb\x9a"
    b"\xf9t\xc4f\x8aos\x92\x9dtn\xe0\xe8Z\xcc\xc8=\xec\xf7d6\x97\xa3]\xc2Q\x1b(\xec"
    b"d\x99_\x8dx\xd4\x15%\xce\x96\xf9\xbf\xacP\xd1:\xfc\xf1\x18\xbe\xeb\xe2\xaey"
    b"\x89;]\xc5\xf1\xfb<\xf3\x99\xe9\x99\xefon\xa2\xdb6\xe5\x1c\xbb^\x8b}FV\x1b"
    b"\x9es+\xb3\xbd\x81M\xeb\xd1\xe0^5\xf1\xbd|\xc4\xfca\xf2\xde\xf0w\x9cW\xabr."
    b"\xe7\xd9\x8dFx\x0e\xa6){\x93\x8e\x85\xf1\xb5\x81\x89\xd9\x82\xa1\x9c\xc8;\xf9"
    b"\xe0\x0cV\xb8W\xdc\xdb\x83\xa9i\xb1O@g\xa6T*\xd3=O\xeaP\xcc(^\x17\xfb\xe4\xb3"
    b"Y\xc9\xb1\x17{N\xf7\xfbo\x8b\xf7\x97\x94\xe3;\xcd\xff)\xd2\xf2\xacy\xa0\x9b"
    b"\xd4g=\x11B\x8bT\x8e\x94Y\x08%\x12\xe2q\x99\xd4\x7f*\x84O\xfa\r\xb5\x916R"
)

#
#   ThreadedHTTPRequestHandler
#


@bacpypes_debugging
class ThreadedHTTPRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if _debug:
            ThreadedHTTPRequestHandler._debug("do_GET")
        global favicon

        # get the thread
        cur_thread = threading.current_thread()
        if _debug:
            ThreadedHTTPRequestHandler._debug("    - cur_thread: %r", cur_thread)

        # parse query data and params to find out what was passed
        parsed_params = urlparse(self.path)
        if _debug:
            ThreadedHTTPRequestHandler._debug("    - parsed_params: %r", parsed_params)
        parsed_query = parse_qs(parsed_params.query)
        if _debug:
            ThreadedHTTPRequestHandler._debug("    - parsed_query: %r", parsed_query)

        # find the pieces
        args = parsed_params.path.split("/")
        if _debug:
            ThreadedHTTPRequestHandler._debug("    - args: %r", args)

        if args[1] == "read":
            self.do_read(args[2:])
        elif args[1] == "whois":
            self.do_whois(args[2:])
        elif args[1] == "favicon.ico":
            self.send_response(200)
            self.send_header("Content-type", "image/x-icon")
            self.send_header("Content-Length", len(favicon))
            self.end_headers()
            self.wfile.write(favicon)
        else:
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"'read' or 'whois' expected")

    def do_read(self, args):
        if _debug:
            ThreadedHTTPRequestHandler._debug("do_read %r", args)

        try:
            addr, obj_id = args[:2]
            obj_id = ObjectIdentifier(obj_id).value

            # get the object type
            if not get_object_class(obj_id[0]):
                raise ValueError("unknown object type")

            # implement a default property, the bain of committee meetings
            if len(args) == 3:
                prop_id = args[2]
            else:
                prop_id = "presentValue"

            # look for its datatype, an easy way to see if the property is
            # appropriate for the object
            datatype = get_datatype(obj_id[0], prop_id)
            if not datatype:
                raise ValueError("invalid property for object type")

            # build a request
            request = ReadPropertyRequest(
                objectIdentifier=obj_id, propertyIdentifier=prop_id
            )
            request.pduDestination = Address(addr)

            # look for an optional array index
            if len(args) == 5:
                request.propertyArrayIndex = int(args[4])
            if _debug:
                ThreadedHTTPRequestHandler._debug("    - request: %r", request)

            # make an IOCB
            iocb = IOCB(request)
            if _debug:
                ThreadedHTTPRequestHandler._debug("    - iocb: %r", iocb)

            # give it to the application
            deferred(this_application.request_io, iocb)

            # wait for it to complete
            iocb.wait()

            # filter out errors and aborts
            if iocb.ioError:
                if _debug:
                    ThreadedHTTPRequestHandler._debug("    - error: %r", iocb.ioError)
                result = {"error": str(iocb.ioError)}
            else:
                if _debug:
                    ThreadedHTTPRequestHandler._debug(
                        "    - response: %r", iocb.ioResponse
                    )
                apdu = iocb.ioResponse

                # find the datatype
                datatype = get_datatype(
                    apdu.objectIdentifier[0], apdu.propertyIdentifier
                )
                if _debug:
                    ThreadedHTTPRequestHandler._debug("    - datatype: %r", datatype)
                if not datatype:
                    raise TypeError("unknown datatype")

                # special case for array parts, others are managed by cast_out
                if issubclass(datatype, Array) and (
                    apdu.propertyArrayIndex is not None
                ):
                    if apdu.propertyArrayIndex == 0:
                        datatype = Unsigned
                    else:
                        datatype = datatype.subtype
                    if _debug:
                        ThreadedHTTPRequestHandler._debug(
                            "    - datatype: %r", datatype
                        )

                # convert the value to a dict if possible
                value = apdu.propertyValue.cast_out(datatype)
                if hasattr(value, "dict_contents"):
                    value = value.dict_contents(as_class=OrderedDict)
                if _debug:
                    ThreadedHTTPRequestHandler._debug("    - value: %r", value)

                result = {"value": value}

        except Exception as err:
            ThreadedHTTPRequestHandler._exception("exception: %r", err)
            result = {"exception": str(err)}

        # encode the results as JSON, convert to bytes
        result_bytes = json.dumps(result).encode("utf-8")

        # write the result
        self.wfile.write(result_bytes)

    def do_whois(self, args):
        if _debug:
            ThreadedHTTPRequestHandler._debug("do_whois %r", args)

        try:
            # build a request
            request = WhoIsRequest()
            if (len(args) == 1) or (len(args) == 3):
                request.pduDestination = Address(args[0])
                del args[0]
            else:
                request.pduDestination = GlobalBroadcast()

            if len(args) == 2:
                request.deviceInstanceRangeLowLimit = int(args[0])
                request.deviceInstanceRangeHighLimit = int(args[1])
            if _debug:
                ThreadedHTTPRequestHandler._debug("    - request: %r", request)

            # make an IOCB
            iocb = IOCB(request)
            if _debug:
                ThreadedHTTPRequestHandler._debug("    - iocb: %r", iocb)

            # give it to the application
            this_application.request_io(iocb)

            # no result -- it would be nice if these were the matching I-Am's
            result = {}

        except Exception as err:
            ThreadedHTTPRequestHandler._exception("exception: %r", err)
            result = {"exception": str(err)}

        # encode the results as JSON, convert to bytes
        result_bytes = json.dumps(result).encode("utf-8")

        # write the result
        self.wfile.write(result_bytes)


class ThreadedTCPServer(ThreadingMixIn, TCPServer):
    pass


#
#   __main__
#

try:
    # parse the command line arguments
    parser = ConfigArgumentParser(description=__doc__)

    # add an option for the server host
    parser.add_argument("--host", type=str, help="server host", default=HOST)
    # add an option for the server port
    parser.add_argument("--port", type=int, help="server port", default=PORT)
    args = parser.parse_args()

    if _debug:
        _log.debug("initialization")
    if _debug:
        _log.debug("    - args: %r", args)

    # make a device object
    this_device = LocalDeviceObject(ini=args.ini)
    if _debug:
        _log.debug("    - this_device: %r", this_device)

    # make a simple application
    this_application = BIPSimpleApplication(this_device, args.ini.address)

    # local host, special port
    server = ThreadedTCPServer((args.host, args.port), ThreadedHTTPRequestHandler)
    if _debug:
        _log.debug("    - server: %r", server)

    # Start a thread with the server -- that thread will then start a thread for each request
    server_thread = threading.Thread(target=server.serve_forever)
    if _debug:
        _log.debug("    - server_thread: %r", server_thread)

    # exit the server thread when the main thread terminates
    server_thread.daemon = True
    server_thread.start()

    if _debug:
        _log.debug("running")

    run()

except Exception as err:
    _log.exception("an error has occurred: %s", err)

finally:
    if server:
        server.shutdown()

    if _debug:
        _log.debug("finally")
