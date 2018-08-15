#!/usr/bin/python

"""
HTTPServer
"""

import threading
import json

from urlparse import urlparse, parse_qs
import SocketServer
import SimpleHTTPServer

from bacpypes.debugging import class_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser

from bacpypes.core import run
from bacpypes.iocb import IOCB

from bacpypes.pdu import Address, GlobalBroadcast
from bacpypes.apdu import ReadPropertyRequest, WhoIsRequest
from bacpypes.primitivedata import ObjectIdentifier

from bacpypes.app import BIPSimpleApplication
from bacpypes.object import get_object_class, get_datatype
from bacpypes.local.device import LocalDeviceObject

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# reference a simple application
this_application = None
server = None

#
#   ThreadedHTTPRequestHandler
#

@class_debugging
class ThreadedHTTPRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    def do_GET(self):
        if _debug: ThreadedHTTPRequestHandler._debug("do_GET")

        # get the thread
        cur_thread = threading.current_thread()
        if _debug: ThreadedHTTPRequestHandler._debug("    - cur_thread: %r", cur_thread)

        # parse query data and params to find out what was passed
        parsed_params = urlparse(self.path)
        if _debug: ThreadedHTTPRequestHandler._debug("    - parsed_params: %r", parsed_params)
        parsed_query = parse_qs(parsed_params.query)
        if _debug: ThreadedHTTPRequestHandler._debug("    - parsed_query: %r", parsed_query)

        # find the pieces
        args = parsed_params.path.split('/')
        if _debug: ThreadedHTTPRequestHandler._debug("    - args: %r", args)

        if (args[1] == 'read'):
            self.do_read(args[2:])
        elif (args[1] == 'whois'):
            self.do_whois(args[2:])

    def do_read(self, args):
        if _debug: ThreadedHTTPRequestHandler._debug("do_read %r", args)

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
                objectIdentifier=obj_id,
                propertyIdentifier=prop_id,
                )
            request.pduDestination = Address(addr)

            # look for an optional array index
            if len(args) == 5:
                request.propertyArrayIndex = int(args[4])
            if _debug: ThreadedHTTPRequestHandler._debug("    - request: %r", request)

            # make an IOCB
            iocb = IOCB(request)
            if _debug: ThreadedHTTPRequestHandler._debug("    - iocb: %r", iocb)

            # give it to the application
            this_application.request_io(iocb)

            # wait for it to complete
            iocb.wait()

            # filter out errors and aborts
            if iocb.ioError:
                if _debug: ThreadedHTTPRequestHandler._debug("    - error: %r", iocb.ioError)
                result = { "error": str(iocb.ioError) }
            else:
                if _debug: ThreadedHTTPRequestHandler._debug("    - response: %r", iocb.ioResponse)
                result = { "value": iocb.ioResponse }

        except Exception as err:
            ThreadedHTTPRequestHandler._exception("exception: %r", err)
            result = { "exception": str(err) }

        # write the result
        json.dump(result, self.wfile)

    def do_whois(self, args):
        if _debug: ThreadedHTTPRequestHandler._debug("do_whois %r", args)

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
            if _debug: ThreadedHTTPRequestHandler._debug("    - request: %r", request)

            # make an IOCB
            iocb = IOCB(request)
            if _debug: ThreadedHTTPRequestHandler._debug("    - iocb: %r", iocb)

            # give it to the application
            this_application.request_io(iocb)

            # no result -- it would be nice if these were the matching I-Am's
            result = {}

        except Exception as err:
            ThreadedHTTPRequestHandler._exception("exception: %r", err)
            result = { "exception": str(err) }

        # write the result
        json.dump(result, self.wfile)

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass

#
#   __main__
#

try:
    # parse the command line arguments
    parser = ConfigArgumentParser(description=__doc__)

    # add an option to override the port in the config file
    parser.add_argument('--port', type=int,
        help="override the port in the config file to PORT",
        default=9000,
        )
    args = parser.parse_args()

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("    - args: %r", args)

    # make a device object
    this_device = LocalDeviceObject(ini=args.ini)
    if _debug: _log.debug("    - this_device: %r", this_device)

    # make a simple application
    this_application = BIPSimpleApplication(this_device, args.ini.address)

    # local host, special port
    HOST, PORT = "", int(args.port)
    server = ThreadedTCPServer((HOST, PORT), ThreadedHTTPRequestHandler)
    if _debug: _log.debug("    - server: %r", server)

    # Start a thread with the server -- that thread will then start a thread for each request
    server_thread = threading.Thread(target=server.serve_forever)
    if _debug: _log.debug("    - server_thread: %r", server_thread)

    # exit the server thread when the main thread terminates
    server_thread.daemon = True
    server_thread.start()

    if _debug: _log.debug("running")

    run()

except Exception as err:
    _log.exception("an error has occurred: %s", err)

finally:
    if server:
        server.shutdown()

    if _debug: _log.debug("finally")
