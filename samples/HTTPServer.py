#!/usr/bin/python

"""
This application is an HTTP server and a BACnet client.  It receives requests
in the form 'http://server:port/address/objectType/objectInstance' and may be
optionally followed by '/propertyIdentifier'.  It starts a thread for each
request, sends the ReadPropertyRequest to the device, and waits for the
response.  It then packages the value (or an error) as a JSON object and
returns it.
"""

import threading
import simplejson
import urlparse

import SocketServer
import SimpleHTTPServer

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser

from bacpypes.core import run, deferred

from bacpypes.pdu import Address
from bacpypes.app import LocalDeviceObject, BIPSimpleApplication
from bacpypes.object import get_object_class, get_datatype

from bacpypes.apdu import ReadPropertyRequest, Error, AbortPDU, ReadPropertyACK
from bacpypes.primitivedata import Unsigned
from bacpypes.constructeddata import Array
from bacpypes.basetypes import ServicesSupported

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# reference a simple application
this_application = None
http_server = None

#
#   IOCB
#

class IOCB:

    def __init__(self):
        # requests and responses
        self.ioRequest = None
        self.ioResponse = None

        # each block gets a completion event
        self.ioComplete = threading.Event()
        self.ioComplete.clear()

#
#   WebServerApplication
#

@bacpypes_debugging
class WebServerApplication(BIPSimpleApplication):

    def __init__(self, *args):
        if _debug: WebServerApplication._debug("__init__ %r", args)
        BIPSimpleApplication.__init__(self, *args)

        # assigning invoke identifiers
        self.nextInvokeID = 1

        # keep track of requests to line up responses
        self.iocb = {}

    def get_next_invoke_id(self, addr):
        """Called to get an unused invoke ID."""
        if _debug: WebServerApplication._debug("get_next_invoke_id %r", addr)

        initialID = self.nextInvokeID
        while 1:
            invokeID = self.nextInvokeID
            self.nextInvokeID = (self.nextInvokeID + 1) % 256

            # see if we've checked for them all
            if initialID == self.nextInvokeID:
                raise RuntimeError("no available invoke ID")

            # see if this one is used
            if (addr, invokeID) not in self.iocb:
                break

        if _debug: WebServerApplication._debug("    - invokeID: %r", invokeID)
        return invokeID

    def request(self, apdu, iocb):
        if _debug: WebServerApplication._debug("request %r", apdu)

        # assign an invoke identifier
        apdu.apduInvokeID = self.get_next_invoke_id(apdu.pduDestination)

        # build a key to reference the IOCB when the response comes back
        invoke_key = (apdu.pduDestination, apdu.apduInvokeID)
        if _debug: WebServerApplication._debug("    - invoke_key: %r", invoke_key)

        # keep track of the request
        self.iocb[invoke_key] = iocb

        # forward it along, apduInvokeID set by stack
        BIPSimpleApplication.request(self, apdu)

    def confirmation(self, apdu):
        if _debug: WebServerApplication._debug("confirmation %r", apdu)

        # build a key to look for the IOCB
        invoke_key = (apdu.pduSource, apdu.apduInvokeID)
        if _debug: WebServerApplication._debug("    - invoke_key: %r", invoke_key)

        # find the request
        iocb = self.iocb.get(invoke_key, None)
        if not iocb:
            raise RuntimeError("no matching request")
        del self.iocb[invoke_key]

        if isinstance(apdu, Error):
            if _debug: WebServerApplication._debug("    - error")
            iocb.ioResponse = apdu

        elif isinstance(apdu, AbortPDU):
            if _debug: WebServerApplication._debug("    - abort")
            iocb.ioResponse = apdu

        elif (isinstance(iocb.ioRequest, ReadPropertyRequest)) and (isinstance(apdu, ReadPropertyACK)):
            # find the datatype
            datatype = get_datatype(apdu.objectIdentifier[0], apdu.propertyIdentifier)
            if _debug: WebServerApplication._debug("    - datatype: %r", datatype)
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
            if _debug: WebServerApplication._debug("    - value: %r", value)

            # assume primitive values for now, JSON would be better
            iocb.ioResponse = value

        # trigger the completion event
        iocb.ioComplete.set()

#
#   ThreadedHTTPRequestHandler
#

@bacpypes_debugging
class ThreadedHTTPRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    def do_GET(self):
        if _debug: ThreadedHTTPRequestHandler._debug("do_GET")

        # get the thread
        cur_thread = threading.current_thread()
        if _debug: ThreadedHTTPRequestHandler._debug("    - cur_thread: %r", cur_thread)

        # parse query data and params to find out what was passed
        parsed_params = urlparse.urlparse(self.path)
        if _debug: ThreadedHTTPRequestHandler._debug("    - parsed_params: %r", parsed_params)
        parsed_query = urlparse.parse_qs(parsed_params.query)
        if _debug: ThreadedHTTPRequestHandler._debug("    - parsed_query: %r", parsed_query)

        # find the pieces
        args = parsed_params.path.split('/')
        if _debug: ThreadedHTTPRequestHandler._debug("    - args: %r", args)

        try:
            _, addr, obj_type, obj_inst = args[:4]

            if not get_object_class(obj_type):
                raise ValueError("unknown object type")

            obj_inst = int(obj_inst)

            # implement a default property, the bain of committee meetings
            if len(args) == 5:
                prop_id = args[4]
            else:
                prop_id = "presentValue"

            # look for its datatype, an easy way to see if the property is
            # appropriate for the object
            datatype = get_datatype(obj_type, prop_id)
            if not datatype:
                raise ValueError("invalid property for object type")

            # build a request
            request = ReadPropertyRequest(
                objectIdentifier=(obj_type, obj_inst),
                propertyIdentifier=prop_id,
                )
            request.pduDestination = Address(addr)

            if len(args) == 6:
                request.propertyArrayIndex = int(args[5])
            if _debug: ThreadedHTTPRequestHandler._debug("    - request: %r", request)

            # build an IOCB, save the request
            iocb = IOCB()
            iocb.ioRequest = request

            # give it to the application to send
            deferred(this_application.request, request, iocb)

            # wait for the response
            iocb.ioComplete.wait()

            # filter out errors and aborts
            if isinstance(iocb.ioResponse, Error):
                result = { "error": str(iocb.ioResponse) }
            elif isinstance(iocb.ioResponse, AbortPDU):
                result = { "abort": str(iocb.ioResponse) }
            else:
                result = { "value": iocb.ioResponse }

        except Exception as err:
            ThreadedHTTPRequestHandler._exception("exception: %r", err)
            result = { "exception": str(err) }

        # write the result
        simplejson.dump(result, self.wfile)

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass

#
#   __main__
#

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
this_device = LocalDeviceObject(
    objectName=args.ini.objectname,
    objectIdentifier=int(args.ini.objectidentifier),
    maxApduLengthAccepted=int(args.ini.maxapdulengthaccepted),
    segmentationSupported=args.ini.segmentationsupported,
    vendorIdentifier=int(args.ini.vendoridentifier),
    )

# build a bit string that knows about the bit names
pss = ServicesSupported()
pss['whoIs'] = 1
pss['iAm'] = 1
pss['readProperty'] = 1
pss['writeProperty'] = 1

# set the property value to be just the bits
this_device.protocolServicesSupported = pss.value

# make a simple application
this_application = WebServerApplication(this_device, args.ini.address)

# local host, special port
HOST, PORT = "", int(args.port)
http_server = ThreadedTCPServer((HOST, args.port), ThreadedHTTPRequestHandler)
if _debug: _log.debug("    - http_server: %r", http_server)

# Start a thread with the server -- that thread will then start a thread for each request
http_server_thread = threading.Thread(target=http_server.serve_forever)
if _debug: _log.debug("    - http_server_thread: %r", http_server_thread)

# exit the server thread when the main thread terminates
http_server_thread.daemon = True
http_server_thread.start()

if _debug: _log.debug("running")

run()

# shutdown the server
http_server.shutdown()

if _debug: _log.debug("fini")