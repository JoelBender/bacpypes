#!/usr/bin/env python

"""
This simple TCP server application listens for one or more client connections
and parses the incoming lines for the parameters to a Write Property request
and sends the result back to the client.
"""

import os

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser

from bacpypes.core import run
from bacpypes.comm import PDU, Client, bind, ApplicationServiceElement
from bacpypes.tcp import TCPServerDirector
from bacpypes.iocb import IOCB

from bacpypes.pdu import Address
from bacpypes.object import get_datatype

from bacpypes.apdu import WritePropertyRequest, SimpleAckPDU
from bacpypes.primitivedata import Null, Atomic, Integer, Unsigned, Real, ObjectIdentifier
from bacpypes.constructeddata import Array, Any

from bacpypes.app import BIPSimpleApplication
from bacpypes.service.device import LocalDeviceObject

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# settings
SERVER_HOST = os.getenv('SERVER_HOST', 'any')
SERVER_PORT = int(os.getenv('SERVER_PORT', 9000))
IDLE_TIMEOUT = int(os.getenv('IDLE_TIMEOUT', 0)) or None

# globals
args = None
this_application = None

#
#   WritePropertyClient
#

@bacpypes_debugging
class WritePropertyClient(Client):

    def confirmation(self, pdu):
        if _debug: WritePropertyClient._debug('confirmation %r', pdu)
        global this_application

        # decode the bytes into a string and strip off the end-of-line
        args = pdu.pduData.decode('utf-8').strip().split()
        if _debug: WritePropertyClient._debug("    - args: %r", args)

        try:
            addr, obj_id, prop_id = args[:3]
            obj_id = ObjectIdentifier(obj_id).value
            value = args[3]

            indx = None
            if len(args) >= 5:
                if args[4] != "-":
                    indx = int(args[4])
            if _debug: WritePropertyClient._debug("    - indx: %r", indx)

            priority = None
            if len(args) >= 6:
                priority = int(args[5])
            if _debug: WritePropertyClient._debug("    - priority: %r", priority)

            # get the datatype
            datatype = get_datatype(obj_id[0], prop_id)
            if _debug: WritePropertyClient._debug("    - datatype: %r", datatype)

            # change atomic values into something encodeable, null is a special case
            if (value == 'null'):
                value = Null()
            elif issubclass(datatype, Atomic):
                if datatype is Integer:
                    value = int(value)
                elif datatype is Real:
                    value = float(value)
                elif datatype is Unsigned:
                    value = int(value)
                value = datatype(value)
            elif issubclass(datatype, Array) and (indx is not None):
                if indx == 0:
                    value = Integer(value)
                elif issubclass(datatype.subtype, Atomic):
                    value = datatype.subtype(value)
                elif not isinstance(value, datatype.subtype):
                    raise TypeError("invalid result datatype, expecting %s" % (datatype.subtype.__name__,))
            elif not isinstance(value, datatype):
                raise TypeError("invalid result datatype, expecting %s" % (datatype.__name__,))
            if _debug: WritePropertyClient._debug("    - encodeable value: %r %s", value, type(value))

            # build a request
            request = WritePropertyRequest(
                objectIdentifier=obj_id,
                propertyIdentifier=prop_id
                )
            request.pduDestination = Address(addr)

            # save the value
            request.propertyValue = Any()
            try:
                request.propertyValue.cast_in(value)
            except Exception as error:
                WritePropertyClient._exception("WriteProperty cast error: %r", error)

            # optional array index
            if indx is not None:
                request.propertyArrayIndex = indx

            # optional priority
            if priority is not None:
                request.priority = priority

            if _debug: WritePropertyClient._debug("    - request: %r", request)

            # make an IOCB
            iocb = IOCB(request)
            if _debug: WritePropertyClient._debug("    - iocb: %r", iocb)

            # reference the original request so the response goes back to the
            # correct client
            iocb.request_pdu = pdu

            # add ourselves to be called back for the response
            iocb.add_callback(self.complete)

            # give it to the application
            this_application.request_io(iocb)
        except Exception as error:
            WritePropertyClient._exception("exception: %r", error)

            # send it back to the client
            error_str = "exception: " + str(error) + '\r\n'
            self.request(PDU(error_str.encode('utf-8'), destination=pdu.pduSource))

    def complete(self, iocb):
        if _debug: WritePropertyClient._debug('complete %r', iocb)

        # pull out the original request pdu
        pdu = iocb.request_pdu

        # do something for success
        if iocb.ioResponse:
            # should be an ack
            if not isinstance(iocb.ioResponse, SimpleAckPDU):
                response_str = "not an ack: " + repr(iocb.ioResponse) + '\r\n'
            else:
                response_str = "ack" + '\r\n'

        # do something for error/reject/abort
        if iocb.ioError:
            response_str = "error: " + repr(iocb.ioError) + '\r\n'

        # send it back to the client
        self.request(PDU(response_str.encode('utf-8'), destination=pdu.pduSource))

#
#   WritePropertyASE
#

@bacpypes_debugging
class WritePropertyASE(ApplicationServiceElement):
    """
    An instance of this class is bound to the director, which is a
    ServiceAccessPoint.  It receives notifications of new actors connected
    from a client, actors that are going away when the connections are closed,
    and socket errors.
    """
    def indication(self, add_actor=None, del_actor=None, actor_error=None, error=None):
        global args

        if add_actor:
            if _debug: WritePropertyASE._debug("indication add_actor=%r", add_actor)

            # it's connected, maybe say hello
            if args.hello:
                self.elementService.indication(PDU(b'hello\n', destination=add_actor.peer))

        if del_actor:
            if _debug: WritePropertyASE._debug("indication del_actor=%r", del_actor)

        if actor_error:
            if _debug: WritePropertyASE._debug("indication actor_error=%r error=%r", actor_error, error)

#
#   __main__
#

def main():
    global args, this_application

    # parse the command line arguments
    parser = ConfigArgumentParser(description=__doc__)
    parser.add_argument(
        "host", nargs='?',
        help="listening address of server or 'any' (default %r)" % (SERVER_HOST,),
        default=SERVER_HOST,
        )
    parser.add_argument(
        "port", nargs='?', type=int,
        help="server port (default %r)" % (SERVER_PORT,),
        default=SERVER_PORT,
        )
    parser.add_argument(
        "--idle-timeout", nargs='?', type=int,
        help="idle connection timeout",
        default=IDLE_TIMEOUT,
        )
    parser.add_argument(
        "--hello", action="store_true",
        default=False,
        help="send a hello message to a client when it connects",
        )
    args = parser.parse_args()

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("    - args: %r", args)

    # make a device object
    this_device = LocalDeviceObject(ini=args.ini)
    if _debug: _log.debug("    - this_device: %r", this_device)

    # make a simple application
    this_application = BIPSimpleApplication(this_device, args.ini.address)

    # extract the server address and port
    host = args.host
    if host == "any":
        host = ''
    server_address = (host, args.port)
    if _debug: _log.debug("    - server_address: %r", server_address)

    # create a director listening to the address
    this_director = TCPServerDirector(server_address, idle_timeout=args.idle_timeout)
    if _debug: _log.debug("    - this_director: %r", this_director)

    # create a client
    write_property_client = WritePropertyClient()
    if _debug: _log.debug("    - write_property_client: %r", write_property_client)

    # bind everything together
    bind(write_property_client, this_director)
    bind(WritePropertyASE(), this_director)

    _log.debug("running")

    run()

    _log.debug("fini")


if __name__ == "__main__":
    main()
