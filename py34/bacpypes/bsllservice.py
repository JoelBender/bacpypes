#!/usr/bin/python

"""
BACnet Streaming Link Layer Service
"""

import random

from .debugging import ModuleLogger, DebugContents, bacpypes_debugging

from .comm import Client, bind, ApplicationServiceElement
from .tcp import TCPClientDirector, TCPServerDirector, StreamToPacket

from .pdu import Address, LocalBroadcast, PDU, unpack_ip_addr
from .npdu import NPDU
from .netservice import NetworkAdapter

from .bsll import AUTHENTICATION_FAILURE, AUTHENTICATION_HASH, \
    AUTHENTICATION_NO_SERVICE, AUTHENTICATION_REQUIRED, AccessChallenge, \
    AccessRequest, AccessResponse, BSLCI, BSLPDU, \
    CLIENT_SERVER_SERVICE_ID, DEVICE_TO_DEVICE_SERVICE_ID, DeviceToDeviceAPDU, \
    LANE_SERVICE_ID, NO_DEVICE_TO_DEVICE_SERVICE, \
    NO_LANE_SERVICE, NO_PROXY_SERVICE, NO_ROUTER_TO_ROUTER_SERVICE, \
    PROXY_SERVICE_ID, ProxyToServerBroadcastNPDU, ProxyToServerUnicastNPDU, \
    ROUTER_TO_ROUTER_SERVICE_ID, Result, RouterToRouterNPDU, SUCCESS, \
    ServerToProxyBroadcastNPDU, ServerToProxyUnicastNPDU, ServiceRequest, \
    UNRECOGNIZED_SERVICE, bsl_pdu_types, hash_functions

# some debugging
_debug = 0
_log = ModuleLogger(globals())

#
#   _Packetize
#

@bacpypes_debugging
def _Packetize(data):
    if _debug: _Packetize._debug("_Packetize %r", data)

    # look for the type field
    start_ind = data.find('\x83')
    if start_ind == -1:
        return None

    # chop off everything up to the start, it's garbage
    if start_ind > 0:
        if _debug: _Packetize._debug("    - garbage: %r", data[:start_ind])
        data = data[start_ind:]

    # make sure we have at least a complete header
    if len(data) < 4:
        return None

    # get the length, make sure we have the whole packet
    total_len = (ord(data[2]) << 8) + ord(data[3])
    if len(data) < total_len:
        return None

    packet_slice = (data[:total_len], data[total_len:])
    if _debug: _Packetize._debug("    - packet_slice: %r", packet_slice)

    return packet_slice

#
#   _StreamToPacket
#

@bacpypes_debugging
class _StreamToPacket(StreamToPacket):

    def __init__(self):
        if _debug: _StreamToPacket._debug("__init__")
        StreamToPacket.__init__(self, _Packetize)

    def indication(self, pdu):
        if _debug: _StreamToPacket._debug("indication %r", pdu)
        self.request(pdu)

#
#   UserInformation
#

@bacpypes_debugging
class UserInformation(DebugContents):

    _debug_contents = ('username', 'password*', 'service', 'proxyNetwork')

    def __init__(self, **kwargs):
        if _debug: UserInformation._debug("__init__ %r", kwargs)

        # init from kwargs
        self.username = kwargs.get('username', None)
        self.password = kwargs.get('password', None)

        # init what services are available
        self.service = {}
        allServices = kwargs.get('allServices', False)

        self.service[DEVICE_TO_DEVICE_SERVICE_ID] = kwargs.get('deviceToDeviceService', allServices)
        self.service[ROUTER_TO_ROUTER_SERVICE_ID] = kwargs.get('routerToRouterService', allServices)
        self.service[PROXY_SERVICE_ID] = kwargs.get('proxyService', allServices)
        self.service[LANE_SERVICE_ID] = kwargs.get('laneService', allServices)
        self.service[CLIENT_SERVER_SERVICE_ID] = kwargs.get('clientServerService', allServices)

        # proxy service can map to a network
        self.proxyNetwork = kwargs.get('proxyNetwork', None)

#
#   ConnectionState
#

@bacpypes_debugging
class ConnectionState(DebugContents):

    NOT_AUTHENTICATED   = 0     # no authentication attempted
    REQUESTED           = 1     # access request sent to the server (client only)
    CHALLENGED          = 2     # access challenge sent to the client (server only)
    AUTHENTICATED       = 3     # authentication successful

    _debug_contents = ('address', 'service', 'connected', 'accessState', 'challenge', 'userinfo', 'proxyAdapter')

    def __init__(self, addr):
        if _debug: ConnectionState._debug("__init__ %r", addr)

        # save the address
        self.address = addr

        # this is not associated with a specific service
        self.service = None

        # start out disconnected until the service request is acked
        self.connected = False

        # access information
        self.accessState = ConnectionState.NOT_AUTHENTICATED
        self.challenge = None
        self.userinfo = None

        # reference to adapter used by proxy server service
        self.proxyAdapter = None

#
#   ServiceAdapter
#

@bacpypes_debugging
class ServiceAdapter:

    _authentication_required = False

    def __init__(self, mux):
        if _debug: ServiceAdapter._debug("__init__ %r", mux)

        # keep a reference to the multiplexer
        self.multiplexer = mux

        # each multiplex adapter keeps a dict of its connections
        self.connections = {}

        # update the multiplexer to reference this adapter
        if (self.serviceID == DEVICE_TO_DEVICE_SERVICE_ID):
            mux.deviceToDeviceService = self
        elif (self.serviceID == ROUTER_TO_ROUTER_SERVICE_ID):
            mux.routerToRouterService = self
        elif (self.serviceID == PROXY_SERVICE_ID):
            mux.proxyService = self
        elif (self.serviceID == LANE_SERVICE_ID):
            mux.laneService = self
        else:
            raise RuntimeError("invalid service ID: {0}".format(self.serviceID))

    def authentication_required(self, addr):
        """Return True iff authentication is required for connection requests from the address."""
        if _debug: ServiceAdapter._debug("authentication_required %r", addr)

        return self._authentication_required

    def get_default_user_info(self, addr):
        """Return a UserInformation object for trusted address->user authentication."""
        if _debug: ServiceAdapter._debug("get_default_user_info %r", addr)

        # no users
        return None

    def get_user_info(self, username):
        """Return a UserInformation object or None."""
        if _debug: ServiceAdapter._debug("get_user_info %r", username)

        # no users
        return None

    def add_connection(self, conn):
        if _debug: ServiceAdapter._debug("add_connection %r", conn)

        # keep track of this connection
        self.connections[conn.address] = conn

        # assume it is happily connected
        conn.service = self
        conn.connected = True

    def remove_connection(self, conn):
        if _debug: ServiceAdapter._debug("remove_connection %r", conn)

        try:
            del self.connections[conn.address]
        except KeyError:
            ServiceAdapter._warning("remove_connection: %r not a connection", conn)

        # clear out the connection attributes
        conn.service = None
        conn.connected = False

    def service_request(self, pdu):
        if _debug: ServiceAdapter._debug("service_request %r", pdu)

        # direct requests to the multiplexer
        self.multiplexer.indication(self, pdu)

    def service_confirmation(self, conn, pdu):
        raise NotImplementedError("service_confirmation must be overridden")

#
#   NetworkServiceAdapter
#

@bacpypes_debugging
class NetworkServiceAdapter(ServiceAdapter, NetworkAdapter):

    def __init__(self, mux, sap, net, cid=None):
        if _debug: NetworkServiceAdapter._debug("__init__ %r %r %r status=%r cid=%r", mux, sap, net, cid)
        ServiceAdapter.__init__(self, mux)
        NetworkAdapter.__init__(self, sap, net, cid)

#
#   TCPServerMultiplexer
#

@bacpypes_debugging
class TCPServerMultiplexer(Client):

    def __init__(self, addr=None):
        if _debug: TCPServerMultiplexer._debug("__init__ %r", addr)
        Client.__init__(self)

        # check for some options
        if addr is None:
            self.address = Address()
            self.addrTuple = ('', 47808)
        else:
            # allow the address to be cast
            if isinstance(addr, Address):
                self.address = addr
            else:
                self.address = Address(addr)

            # extract the tuple for binding
            self.addrTuple = self.address.addrTuple

        if _debug:
            TCPServerMultiplexer._debug("    - address: %r", self.address)
            TCPServerMultiplexer._debug("    - addrTuple: %r", self.addrTuple)

        # create and bind
        self.director = TCPServerDirector(self.addrTuple)
        bind(self, _StreamToPacket(), self.director)

        # create an application service element and bind
        self.ase = TCPMultiplexerASE(self)
        bind(self.ase, self.director)

        # keep a dictionary of connections
        self.connections = {}

        # no services available until they are created, they are
        # instances of ServiceAdapter
        self.deviceToDeviceService = None
        self.routerToRouterService = None
        self.proxyService = None
        self.laneService = None

    def request(self, pdu):
        if _debug: TCPServerMultiplexer._debug("request %r", pdu)

        # encode it as a BSLPDU
        xpdu = BSLPDU()
        pdu.encode(xpdu)
        if _debug: TCPServerMultiplexer._debug("    - xpdu: %r", xpdu)

        # encode it as a raw PDU
        ypdu = PDU()
        xpdu.encode(ypdu)
        ypdu.pduDestination = unpack_ip_addr(pdu.pduDestination.addrAddr)
        if _debug: TCPServerMultiplexer._debug("    - ypdu: %r", ypdu)

        # continue along
        Client.request(self, ypdu)

    def indication(self, server, pdu):
        if _debug: TCPServerMultiplexer._debug("indication %r %r", server, pdu)

        # pass through, it will be encoded
        self.request(pdu)

    def confirmation(self, pdu):
        if _debug: TCPServerMultiplexer._debug("confirmation %r", pdu)

        # recast from a comm.PDU to a BACpypes PDU
        pdu = PDU(pdu, source=Address(pdu.pduSource))
        if _debug: TCPServerMultiplexer._debug("    - pdu: %r", pdu)

        # interpret as a BSLL PDU
        bslpdu = BSLPDU()
        bslpdu.decode(pdu)
        if _debug: TCPServerMultiplexer._debug("    - bslpdu: %r", bslpdu)

        # get the connection
        conn = self.connections.get(pdu.pduSource, None)
        if not conn:
            TCPServerMultiplexer._warning("no connection: %r", pdu.pduSource)
            return

        # extract the function for easy access
        fn = bslpdu.bslciFunction

        # get the class related to the function
        rpdu = bsl_pdu_types[fn]()
        rpdu.decode(bslpdu)
        if _debug: TCPServerMultiplexer._debug("    - rpdu: %r", rpdu)

        # redirect
        if (fn == BSLCI.result):
            TCPServerMultiplexer._warning("unexpected Result")

        # client is asking for a particular service
        elif (fn == BSLCI.serviceRequest):
            # if it is already connected, disconnect it
            if conn.service and conn.connected:
                conn.service.remove_connection(conn)

            newSAP = None
            resultCode = SUCCESS
            if rpdu.bslciServiceID == DEVICE_TO_DEVICE_SERVICE_ID:
                if self.deviceToDeviceService:
                    newSAP = self.deviceToDeviceService
                else:
                    resultCode = NO_DEVICE_TO_DEVICE_SERVICE
            elif rpdu.bslciServiceID == ROUTER_TO_ROUTER_SERVICE_ID:
                if self.routerToRouterService:
                    newSAP = self.routerToRouterService
                else:
                    resultCode = NO_ROUTER_TO_ROUTER_SERVICE
            elif rpdu.bslciServiceID == PROXY_SERVICE_ID:
                if self.proxyService:
                    newSAP = self.proxyService
                else:
                    resultCode = NO_PROXY_SERVICE
            elif rpdu.bslciServiceID == LANE_SERVICE_ID:
                if self.laneService:
                    newSAP = self.laneService
                else:
                    resultCode = NO_LANE_SERVICE
            else:
                resultCode = UNRECOGNIZED_SERVICE

            # success means the service requested is supported
            if resultCode:
                response = Result(resultCode)
                response.pduDestination = rpdu.pduSource
                self.request(response)
                return

            # check to see if authentication is required
            if not newSAP.authentication_required(conn.address):
                newSAP.add_connection(conn)
            else:
                # if there is no userinfo, try to get default userinfo
                if not conn.userinfo:
                    conn.userinfo = newSAP.get_default_user_info(conn.address)
                    if conn.userinfo:
                        conn.accessState = ConnectionState.AUTHENTICATED
                        if _debug: TCPServerMultiplexer._debug("    - authenticated to default user info: %r", conn.userinfo)
                    else:
                        if _debug: TCPServerMultiplexer._debug("    - no default user info")

                # check if authentication has occurred
                if not conn.accessState == ConnectionState.AUTHENTICATED:
                    resultCode = AUTHENTICATION_REQUIRED

                    # save a reference to the service to use when authenticated
                    conn.service = newSAP

                # make sure the user can use the service
                elif not conn.userinfo.service[newSAP.serviceID]:
                    resultCode = AUTHENTICATION_NO_SERVICE

                # all's well
                else:
                    newSAP.add_connection(conn)

            response = Result(resultCode)
            response.pduDestination = rpdu.pduSource
            self.request(response)

        elif (fn == BSLCI.deviceToDeviceAPDU) and self.deviceToDeviceService:
            if conn.service is not self.deviceToDeviceService:
                TCPServerMultiplexer._warning("not connected to appropriate service")
                return

            self.deviceToDeviceService.service_confirmation(conn, rpdu)

        elif (fn == BSLCI.routerToRouterNPDU) and self.routerToRouterService:
            if conn.service is not self.routerToRouterService:
                TCPServerMultiplexer._warning("not connected to appropriate service")
                return

            self.routerToRouterService.service_confirmation(conn, rpdu)

        elif (fn == BSLCI.proxyToServerUnicastNPDU) and self.proxyService:
            if conn.service is not self.proxyService:
                TCPServerMultiplexer._warning("not connected to appropriate service")
                return

            self.proxyService.service_confirmation(conn, rpdu)

        elif (fn == BSLCI.proxyToServerBroadcastNPDU) and self.proxyService:
            if conn.service is not self.proxyService:
                TCPServerMultiplexer._warning("not connected to appropriate service")
                return

            self.proxyService.service_confirmation(conn, rpdu)

        elif (fn == BSLCI.serverToProxyUnicastNPDU) and self.proxyService:
            TCPServerMultiplexer._warning("unexpected Server-To-Proxy-Unicast-NPDU")

        elif (fn == BSLCI.serverToProxyBroadcastNPDU) and self.proxyService:
            TCPServerMultiplexer._warning("unexpected Server-To-Proxy-Broadcast-NPDU")

        elif (fn == BSLCI.clientToLESUnicastNPDU) and self.laneService:
            if conn.service is not self.laneService:
                TCPServerMultiplexer._warning("not connected to appropriate service")
                return

            self.laneService.service_confirmation(conn, rpdu)

        elif (fn == BSLCI.clientToLESBroadcastNPDU) and self.laneService:
            if conn.service is not self.laneService:
                TCPServerMultiplexer._warning("not connected to appropriate service")
                return

            self.laneService.service_confirmation(conn, rpdu)

        elif (fn == BSLCI.lesToClientUnicastNPDU) and self.laneService:
            TCPServerMultiplexer._warning("unexpected LES-to-Client-Unicast-NPDU")

        elif (fn == BSLCI.lesToClientBroadcastNPDU) and self.laneService:
            TCPServerMultiplexer._warning("unexpected LES-to-Client-Broadcast-NPDU")

        elif (fn == BSLCI.accessRequest):
            self.do_AccessRequest(conn, rpdu)

        elif (fn == BSLCI.accessChallenge):
            TCPServerMultiplexer._warning("unexpected Access-Challenge")

        elif (fn == BSLCI.accessResponse):
            self.do_AccessResponse(conn, rpdu)

        else:
            TCPServerMultiplexer._warning("unsupported message")

    def do_AccessRequest(self, conn, bslpdu):
        if _debug: TCPServerMultiplexer._debug("do_AccessRequest %r %r", conn, bslpdu)

        # make sure this connection has requested a service first
        if not conn.service:
            if _debug: TCPServerMultiplexer._debug("    - request a service first")

            response = Result(AUTHENTICATION_NO_SERVICE)
            response.pduDestination = bslpdu.pduSource
            self.request(response)
            return

        # make sure this process isn't being repeated more than once for the connection
        if conn.accessState != ConnectionState.NOT_AUTHENTICATED:
            if _debug: TCPServerMultiplexer._debug("    - connection in the wrong state: %r", conn.accessState)

            response = Result(AUTHENTICATION_FAILURE)
            response.pduDestination = bslpdu.pduSource
            self.request(response)
            return

        # get the hash function
        try:
            hashFn = hash_functions[bslpdu.bslciHashFn]
        except:
            if _debug: TCPServerMultiplexer._debug("    - no hash function: %r", bslpdu.bslciHashFn)

            response = Result(AUTHENTICATION_HASH)
            response.pduDestination = bslpdu.pduSource
            self.request(response)
            return

        # get the userinfo from the service
        conn.userinfo = conn.service.get_user_info(bslpdu.bslciUsername)
        if not conn.userinfo:
            if _debug: TCPServerMultiplexer._debug("    - no user info: %r", bslpdu.bslciUsername)

            response = Result(AUTHENTICATION_FAILURE)
            response.pduDestination = bslpdu.pduSource
            self.request(response)
            return

        # build a challenge string, save it in the connection
        challenge = hashFn(''.join(chr(random.randrange(256)) for i in range(128)))
        conn.challenge = challenge

        # save that we have issued a challenge
        conn.accessState = ConnectionState.CHALLENGED

        # conn.userinfo is authentication information, build a challenge response and send it back
        response = AccessChallenge(bslpdu.bslciHashFn, challenge)
        response.pduDestination = conn.address
        self.request(response)

    def do_AccessResponse(self, conn, bslpdu):
        if _debug: TCPServerMultiplexer._debug("do_AccessResponse %r %r", conn, bslpdu)

        # start out happy
        resultCode = SUCCESS

        # if there's no user, fail
        if not conn.userinfo:
            if _debug: TCPServerMultiplexer._debug("    - connection has no user info")
            resultCode = AUTHENTICATION_FAILURE

        # make sure a challenge has been issued
        elif conn.accessState != ConnectionState.CHALLENGED:
            if _debug: TCPServerMultiplexer._debug("    - connection in the wrong state: %r", conn.accessState)
            resultCode = AUTHENTICATION_FAILURE

        else:
            # get the hash function
            try:
                hashFn = hash_functions[bslpdu.bslciHashFn]
            except:
                if _debug: TCPServerMultiplexer._debug("    - no hash function: %r", bslpdu.bslciHashFn)

                response = Result(AUTHENTICATION_HASH)
                response.pduDestination = bslpdu.pduSource
                self.request(response)
                return

            # take the password, the challenge, and hash them
            challengeResponse = hashFn(conn.userinfo.password + conn.challenge)

            # see if the response matches what we think it should be
            if challengeResponse == bslpdu.bslciResponse:
                if _debug: TCPServerMultiplexer._debug("    - success")

                # connection is now authenticated
                conn.accessState = ConnectionState.AUTHENTICATED

                # we may have gone through authentication without requesting a service
                if not conn.service:
                    if _debug: TCPServerMultiplexer._debug("    - no service")

                # make sure the user can use the service
                elif not conn.userinfo.service[conn.service.serviceID]:
                    # break the reference to the service
                    resultCode = AUTHENTICATION_NO_SERVICE
                    conn.service = None

                else:
                    # all's well
                    conn.service.add_connection(conn)

            else:
                if _debug: TCPServerMultiplexer._debug("    - challenge/response mismatch")
                resultCode = AUTHENTICATION_FAILURE

        response = Result(resultCode)
        response.pduDestination = bslpdu.pduSource
        self.request(response)

#
#   TCPClientMultiplexer
#

@bacpypes_debugging
class TCPClientMultiplexer(Client):

    def __init__(self):
        if _debug: TCPClientMultiplexer._debug("__init__")
        Client.__init__(self)

        # create and bind
        self.director = TCPClientDirector()
        bind(self, _StreamToPacket(), self.director)

        # create an application service element and bind
        self.ase = TCPMultiplexerASE(self)
        bind(self.ase, self.director)

        # keep a dictionary of connections
        self.connections = {}

        # no services available until they are created, they are
        # instances of ServiceAdapter
        self.deviceToDeviceService = None
        self.routerToRouterService = None
        self.proxyService = None
        self.laneService = None

    def request(self, pdu):
        if _debug: TCPClientMultiplexer._debug("request %r", pdu)

        # encode it as a BSLPDU
        xpdu = BSLPDU()
        pdu.encode(xpdu)
        if _debug: TCPClientMultiplexer._debug("    - xpdu: %r", xpdu)

        # encode it as a raw PDU
        ypdu = PDU()
        xpdu.encode(ypdu)
        ypdu.pduDestination = unpack_ip_addr(pdu.pduDestination.addrAddr)
        if _debug: TCPClientMultiplexer._debug("    - ypdu: %r", ypdu)

        # continue along
        Client.request(self, ypdu)

    def indication(self, server, pdu):
        if _debug: TCPClientMultiplexer._debug("indication %r %r", server, pdu)

        # pass through, it will be encoded
        self.request(pdu)

    def confirmation(self, pdu):
        if _debug: TCPClientMultiplexer._debug("confirmation %r", pdu)

        # recast from a comm.PDU to a BACpypes PDU
        pdu = PDU(pdu, source=Address(pdu.pduSource))

        # interpret as a BSLL PDU
        bslpdu = BSLPDU()
        bslpdu.decode(pdu)
        if _debug: TCPClientMultiplexer._debug("    - bslpdu: %r", bslpdu)

        # get the connection
        conn = self.connections.get(pdu.pduSource, None)
        if not conn:
            TCPClientMultiplexer._warning("no connection: %r", pdu.pduSource)
            return

        # extract the function for easy access
        fn = bslpdu.bslciFunction

        # get the class related to the function
        rpdu = bsl_pdu_types[fn]()
        rpdu.decode(bslpdu)
        if _debug: TCPClientMultiplexer._debug("    - rpdu: %r", rpdu)

        # redirect
        if (fn == BSLCI.result):
            # if the connection is not associated with a service, toss it
            if not conn.service:
                TCPClientMultiplexer._warning("unexpected result")
                return

            # if it is already connected, stop
            if conn.connected:
                TCPClientMultiplexer._warning("unexpected result, already connected")
                return

            # if this is successful, add it to the service
            if rpdu.bslciResultCode == SUCCESS:
                # if authentication was required, change to authenticate when this ack comes back
                if conn.accessState == ConnectionState.REQUESTED:
                    if _debug: TCPClientMultiplexer._debug("    - authentication successful")
                    conn.accessState = ConnectionState.AUTHENTICATED

                # add the connection to the service
                conn.service.add_connection(conn)

                # let the service process the ack
                conn.service.connect_ack(conn, rpdu)

            # if authentication is required, start the process
            elif rpdu.bslciResultCode == AUTHENTICATION_REQUIRED:
                # make sure this process isn't being repeated more than once for the connection
                if conn.accessState != ConnectionState.NOT_AUTHENTICATED:
                    TCPClientMultiplexer._warning("unexpected authentication required")
                    return

                conn.userinfo = conn.service.get_default_user_info(conn.address)
                if not conn.userinfo:
                    TCPClientMultiplexer._warning("authentication required, no user information")
                    return

                # set the connection state
                conn.accessState = ConnectionState.REQUESTED

                # send the username
                response = AccessRequest(0, conn.userinfo.username)
                response.pduDestination = rpdu.pduSource
                self.request(response)

            else:
                TCPClientMultiplexer._warning("result code: %r", rpdu.bslciResultCode)

        elif (fn == BSLCI.serviceRequest):
            TCPClientMultiplexer._warning("unexpected service request")

        elif (fn == BSLCI.deviceToDeviceAPDU) and self.deviceToDeviceService:
            if conn.service is not self.deviceToDeviceService:
                TCPClientMultiplexer._warning("not connected to appropriate service")
                return

            self.deviceToDeviceService.service_confirmation(conn, rpdu)

        elif (fn == BSLCI.routerToRouterNPDU) and self.routerToRouterService:
            if conn.service is not self.routerToRouterService:
                TCPClientMultiplexer._warning("not connected to appropriate service")
                return

            self.routerToRouterService.service_confirmation(conn, rpdu)

        elif (fn == BSLCI.proxyToServerUnicastNPDU) and self.proxyService:
            TCPClientMultiplexer._warning("unexpected Proxy-To-Server-Unicast-NPDU")

        elif (fn == BSLCI.proxyToServerBroadcastNPDU) and self.proxyService:
            TCPClientMultiplexer._warning("unexpected Proxy-To-Broadcast-Unicast-NPDU")

        elif (fn == BSLCI.serverToProxyUnicastNPDU) and self.proxyService:
            if conn.service is not self.proxyService:
                TCPClientMultiplexer._warning("not connected to appropriate service")
                return

            self.proxyService.service_confirmation(conn, rpdu)

        elif (fn == BSLCI.serverToProxyBroadcastNPDU) and self.proxyService:
            if conn.service is not self.proxyService:
                TCPClientMultiplexer._warning("not connected to appropriate service")
                return

            self.proxyService.service_confirmation(conn, rpdu)

        elif (fn == BSLCI.clientToLESUnicastNPDU) and self.laneService:
            TCPClientMultiplexer._warning("unexpected Client-to-LES-Unicast-NPDU")

        elif (fn == BSLCI.clientToLESBroadcastNPDU) and self.laneService:
            TCPClientMultiplexer._warning("unexpected Client-to-LES-Broadcast-NPDU")

        elif (fn == BSLCI.lesToClientUnicastNPDU) and self.laneService:
            if conn.service is not self.laneService:
                TCPClientMultiplexer._warning("not connected to appropriate service")
                return

            self.laneService.service_confirmation(conn, rpdu)

        elif (fn == BSLCI.lesToClientBroadcastNPDU) and self.laneService:
            if conn.service is not self.laneService:
                TCPClientMultiplexer._warning("not connected to appropriate service")
                return

            self.laneService.service_confirmation(conn, rpdu)

        elif (fn == BSLCI.accessRequest):
            TCPClientMultiplexer._warning("unexpected Access-request")

        elif (fn == BSLCI.accessChallenge):
            self.do_AccessChallenge(conn, rpdu)

        elif (fn == BSLCI.accessResponse):
            TCPClientMultiplexer._warning("unexpected Access-response")

        else:
            TCPClientMultiplexer._warning("unsupported message: %s", rpdu.__class__.__name__)

    def do_AccessChallenge(self, conn, bslpdu):
        if _debug: TCPClientMultiplexer._debug("do_AccessRequest %r %r", conn, bslpdu)

        # make sure this process isn't being repeated more than once for the connection
        if conn.accessState != ConnectionState.REQUESTED:
            TCPClientMultiplexer._warning("unexpected access challenge")
            return

        # get the hash function
        try:
            hashFn = hash_functions[bslpdu.bslciHashFn]
        except:
            TCPClientMultiplexer._warning("no hash function: %r", bslpdu.bslciHashFn)
            return

        # take the password, the challenge, and hash them
        challengeResponse = hashFn(conn.userinfo.password + bslpdu.bslciChallenge)

        # conn.userinfo is authentication information, build a challenge response and send it back
        response = AccessResponse(bslpdu.bslciHashFn, challengeResponse)
        response.pduDestination = conn.address
        if _debug: TCPClientMultiplexer._debug("    - response: %r", response)
        self.request(response)

#
#   TCPMultiplexerASE
#

@bacpypes_debugging
class TCPMultiplexerASE(ApplicationServiceElement):

    def __init__(self, mux):
        if _debug: TCPMultiplexerASE._debug("__init__ %r", mux)

        # keep track of the multiplexer
        self.multiplexer = mux

    def indication(self, *args, **kwargs):
        if _debug: TCPMultiplexerASE._debug('TCPMultiplexerASE %r %r', args, kwargs)

        if 'addPeer' in kwargs:
            addr = Address(kwargs['addPeer'])
            if _debug: TCPMultiplexerASE._debug("    - add peer: %r", addr)

            if addr in self.multiplexer.connections:
                if _debug: TCPMultiplexerASE._debug("    - already a connection")
                return

            conn = ConnectionState(addr)
            if _debug: TCPMultiplexerASE._debug("    - conn: %r", conn)

            # add it to the multiplexer connections
            self.multiplexer.connections[addr] = conn

        if 'delPeer' in kwargs:
            addr = Address(kwargs['delPeer'])
            if _debug: TCPMultiplexerASE._info("    - delete peer: %r", addr)

            if addr not in self.multiplexer.connections:
                if _debug: TCPMultiplexerASE._debug("    - not a connection")
                return

            # get the connection
            conn = self.multiplexer.connections.get(addr)
            if _debug: TCPMultiplexerASE._debug("    - conn: %r", conn)

            # if it is associated and connected, disconnect it
            if conn.service and conn.connected:
                conn.service.remove_connection(conn)

            # remove it from the multiplexer
            del self.multiplexer.connections[addr]

#
#   DeviceToDeviceServerService
#

@bacpypes_debugging
class DeviceToDeviceServerService(NetworkServiceAdapter):

    serviceID = DEVICE_TO_DEVICE_SERVICE_ID

    def process_npdu(self, npdu):
        """encode NPDUs from the service access point and send them downstream."""
        if _debug: DeviceToDeviceServerService._debug("process_npdu %r", npdu)

        # broadcast messages go to peers
        if npdu.pduDestination.addrType == Address.localBroadcastAddr:
            destList = self.connections.keys()
        else:
            if npdu.pduDestination not in self.connections:
                if _debug: DeviceToDeviceServerService._debug("    - not a connected client")
                return
            destList = [npdu.pduDestination]
        if _debug: DeviceToDeviceServerService._debug("    - destList: %r", destList)

        for dest in destList:
            # make device-to-device APDU
            xpdu = DeviceToDeviceAPDU(npdu)
            xpdu.pduDestination = dest

            # send it down to the multiplexer
            self.service_request(xpdu)

    def service_confirmation(self, conn, pdu):
        if _debug: DeviceToDeviceServerService._debug("service_confirmation %r %r", conn, pdu)

        # build an NPDU
        npdu = NPDU(pdu.pduData)
        npdu.pduSource = pdu.pduSource
        if _debug: DeviceToDeviceServerService._debug("    - npdu: %r", npdu)

        # send it to the service access point for processing
        self.adapterSAP.process_npdu(self, npdu)

#
#   DeviceToDeviceClientService
#

@bacpypes_debugging
class DeviceToDeviceClientService(NetworkServiceAdapter):

    serviceID = DEVICE_TO_DEVICE_SERVICE_ID

    def process_npdu(self, npdu):
        """encode NPDUs from the service access point and send them downstream."""
        if _debug: DeviceToDeviceClientService._debug("process_npdu %r", npdu)

        # broadcast messages go to everyone
        if npdu.pduDestination.addrType == Address.localBroadcastAddr:
            destList = self.connections.keys()
        else:
            conn = self.connections.get(npdu.pduDestination, None)
            if not conn:
                if _debug: DeviceToDeviceClientService._debug("    - not a connected client")

                # start a connection attempt
                conn = self.connect(npdu.pduDestination)
            if not conn.connected:
                # keep a reference to this npdu to send after the ack comes back
                conn.pendingNPDU.append(npdu)
                return

            destList = [npdu.pduDestination]
        if _debug: DeviceToDeviceClientService._debug("    - destList: %r", destList)

        for dest in destList:
            # make device-to-device APDU
            xpdu = DeviceToDeviceAPDU(npdu)
            xpdu.pduDestination = dest

            # send it down to the multiplexer
            self.service_request(xpdu)

    def connect(self, addr):
        """Initiate a connection request to the device."""
        if _debug: DeviceToDeviceClientService._debug("connect %r", addr)

        # make a connection
        conn = ConnectionState(addr)
        self.multiplexer.connections[addr] = conn

        # associate with this service, but it is not connected until the ack comes back
        conn.service = self

        # keep a list of pending NPDU objects until the ack comes back
        conn.pendingNPDU = []

        # build a service request
        request = ServiceRequest(DEVICE_TO_DEVICE_SERVICE_ID)
        request.pduDestination = addr

        # send it
        self.service_request(request)

        # return the connection object
        return conn

    def connect_ack(self, conn, pdu):
        if _debug: DeviceToDeviceClientService._debug("connect_ack %r %r", conn, pdu)

        # if the response is good, consider it connected
        if pdu.bslciResultCode == 0:
            # send the pending NPDU if there is one
            if conn.pendingNPDU:
                for npdu in conn.pendingNPDU:
                    # make device-to-device APDU
                    xpdu = DeviceToDeviceAPDU(npdu)
                    xpdu.pduDestination = npdu.pduDestination

                    # send it down to the multiplexer
                    self.service_request(xpdu)
                conn.pendingNPDU = []
        else:
            pass

    def service_confirmation(self, conn, pdu):
        if _debug: DeviceToDeviceClientService._debug("service_confirmation %r %r", conn, pdu)

        # build an NPDU
        npdu = NPDU(pdu.pduData)
        npdu.pduSource = pdu.pduSource
        if _debug: DeviceToDeviceClientService._debug("    - npdu: %r", npdu)

        # send it to the service access point for processing
        self.adapterSAP.process_npdu(self, npdu)

#
#   RouterToRouterService
#

@bacpypes_debugging
class RouterToRouterService(NetworkServiceAdapter):

    serviceID = ROUTER_TO_ROUTER_SERVICE_ID

    def process_npdu(self, npdu):
        """encode NPDUs from the service access point and send them downstream."""
        if _debug: RouterToRouterService._debug("process_npdu %r", npdu)

        # encode the npdu as if it was about to be delivered to the network
        pdu = PDU()
        npdu.encode(pdu)
        if _debug: RouterToRouterService._debug("    - pdu: %r", pdu)

        # broadcast messages go to everyone
        if pdu.pduDestination.addrType == Address.localBroadcastAddr:
            destList = self.connections.keys()
        else:
            conn = self.connections.get(pdu.pduDestination, None)
            if not conn:
                if _debug: RouterToRouterService._debug("    - not a connected client")

                # start a connection attempt
                conn = self.connect(pdu.pduDestination)
            if not conn.connected:
                # keep a reference to this pdu to send after the ack comes back
                conn.pendingNPDU.append(pdu)
                return

            destList = [pdu.pduDestination]
        if _debug: RouterToRouterService._debug("    - destList: %r", destList)

        for dest in destList:
            # make a router-to-router NPDU
            xpdu = RouterToRouterNPDU(pdu)
            xpdu.pduDestination = dest

            # send it to the multiplexer
            self.service_request(xpdu)

    def connect(self, addr):
        """Initiate a connection request to the peer router."""
        if _debug: RouterToRouterService._debug("connect %r", addr)

        # make a connection
        conn = ConnectionState(addr)
        self.multiplexer.connections[addr] = conn

        # associate with this service, but it is not connected until the ack comes back
        conn.service = self

        # keep a list of pending NPDU objects until the ack comes back
        conn.pendingNPDU = []

        # build a service request
        request = ServiceRequest(ROUTER_TO_ROUTER_SERVICE_ID)
        request.pduDestination = addr

        # send it
        self.service_request(request)

        # return the connection object
        return conn

    def connect_ack(self, conn, pdu):
        if _debug: RouterToRouterService._debug("connect_ack %r %r", conn, pdu)

        # if the response is good, consider it connected
        if pdu.bslciResultCode == 0:
            # send the pending NPDU if there is one
            if conn.pendingNPDU:
                for npdu in conn.pendingNPDU:
                    # make router-to-router NPDU
                    xpdu = RouterToRouterNPDU(npdu)
                    xpdu.pduDestination = npdu.pduDestination

                    # send it down to the multiplexer
                    self.service_request(xpdu)
                conn.pendingNPDU = []
        else:
            pass

    def add_connection(self, conn):
        if _debug: RouterToRouterService._debug("add_connection %r", conn)

        # first do the usual things
        NetworkServiceAdapter.add_connection(self, conn)

        # generate a Who-Is-Router-To-Network, all networks

        # send it to the client

    def remove_connection(self, conn):
        if _debug: RouterToRouterService._debug("remove_connection %r", conn)

        # first to the usual thing
        NetworkServiceAdapter.remove_connection(self, conn)

        # the NSAP needs routing table information related to this connection flushed
        self.adapterSAP.remove_router_references(self, conn.address)

    def service_confirmation(self, conn, pdu):
        if _debug: RouterToRouterService._debug("service_confirmation %r %r", conn, pdu)

        # decode it, the nework layer needs NPDUs
        npdu = NPDU()
        npdu.decode(pdu)
        npdu.pduSource = pdu.pduSource
        if _debug: ProxyServiceNetworkAdapter._debug("    - npdu: %r", npdu)

        # send it to the service access point for processing
        self.adapterSAP.process_npdu(self, npdu)

#
#   ProxyServiceNetworkAdapter
#

@bacpypes_debugging
class ProxyServiceNetworkAdapter(NetworkAdapter):

    def __init__(self, conn, sap, net, cid=None):
        if _debug: ProxyServiceNetworkAdapter._debug("__init__ %r %r %r status=0 cid=%r", conn, sap, net, cid)
        NetworkAdapter.__init__(self, sap, net, cid)

        # save the connection
        self.conn = conn

    def process_npdu(self, npdu):
        """encode NPDUs from the network service access point and send them to the proxy."""
        if _debug: ProxyServiceNetworkAdapter._debug("process_npdu %r", npdu)

        # encode the npdu as if it was about to be delivered to the network
        pdu = PDU()
        npdu.encode(pdu)
        if _debug: ProxyServiceNetworkAdapter._debug("    - pdu: %r", pdu)

        # broadcast messages go to peers
        if pdu.pduDestination.addrType == Address.localBroadcastAddr:
            xpdu = ServerToProxyBroadcastNPDU(pdu)
        else:
            xpdu = ServerToProxyUnicastNPDU(pdu.pduDestination, pdu)

        # the connection has the correct address
        xpdu.pduDestination = self.conn.address

        # send it down to the multiplexer
        self.conn.service.service_request(xpdu)

    def service_confirmation(self, bslpdu):
        """Receive packets forwarded by the proxy and send them upstream to the network service access point."""
        if _debug: ProxyServiceNetworkAdapter._debug("service_confirmation %r", bslpdu)

        # build a PDU
        pdu = NPDU(bslpdu.pduData)

        # the source is from the original source, not the proxy itself
        pdu.pduSource = bslpdu.bslciAddress

        # if the proxy received a broadcast, send it upstream as a broadcast
        if isinstance(bslpdu, ProxyToServerBroadcastNPDU):
            pdu.pduDestination = LocalBroadcast()
        if _debug: ProxyServiceNetworkAdapter._debug("    - pdu: %r", pdu)

        # decode it, the nework layer needs NPDUs
        npdu = NPDU()
        npdu.decode(pdu)
        if _debug: ProxyServiceNetworkAdapter._debug("    - npdu: %r", npdu)

        # send it to the service access point for processing
        self.adapterSAP.process_npdu(self, npdu)

#
#   ProxyServerService
#

@bacpypes_debugging
class ProxyServerService(ServiceAdapter):

    serviceID = PROXY_SERVICE_ID

    def __init__(self, mux, nsap):
        if _debug: ProxyServerService._debug("__init__ %r %r", mux, nsap)
        ServiceAdapter.__init__(self, mux)

        # save a reference to the network service access point
        self.nsap = nsap

    def add_connection(self, conn):
        if _debug: ProxyServerService._debug("add_connection %r", conn)

        # add as usual
        ServiceAdapter.add_connection(self, conn)

        # create a proxy adapter
        conn.proxyAdapter = ProxyServiceNetworkAdapter(conn, self.nsap, conn.userinfo.proxyNetwork)
        if _debug: ProxyServerService._debug("    - proxyAdapter: %r", conn.proxyAdapter)

    def remove_connection(self, conn):
        if _debug: ProxyServerService._debug("remove_connection %r", conn)

        # remove as usual
        ServiceAdapter.remove_connection(self, conn)

        # remove the adapter from the list of adapters for the nsap
        self.nsap.adapters.remove(conn.proxyAdapter)

    def service_confirmation(self, conn, bslpdu):
        """Receive packets forwarded by the proxy and redirect them to the proxy network adapter."""
        if _debug: ProxyServerService._debug("service_confirmation %r %r", conn, bslpdu)

        # make sure there is an adapter for it - or something went wrong
        if not getattr(conn, 'proxyAdapter', None):
            raise RuntimeError("service confirmation received but no adapter for it")

        # forward along
        conn.proxyAdapter.service_confirmation(bslpdu)

#
#   ProxyClientService
#

@bacpypes_debugging
class ProxyClientService(ServiceAdapter, Client):

    serviceID = PROXY_SERVICE_ID

    def __init__(self, mux, addr=None, userinfo=None, cid=None):
        if _debug: ProxyClientService._debug("__init__ %r %r userinfo=%r cid=%r", mux, addr, userinfo, cid)
        ServiceAdapter.__init__(self, mux)
        Client.__init__(self, cid)

        # save the address of the server and the userinfo
        self.address = addr
        self.userinfo = userinfo

    def get_default_user_info(self, addr):
        """get the user information to authenticate."""
        if _debug: ProxyClientService._debug("get_default_user_info %r", addr)
        return self.userinfo

    def connect(self, addr=None, userinfo=None):
        """Initiate a connection request to the device."""
        if _debug: ProxyClientService._debug("connect addr=%r", addr)

        # if the address was provided, use it
        if addr:
            self.address = addr
        else:
            addr = self.address

        # if the user was provided, save it
        if userinfo:
            self.userinfo = userinfo

        # make a connection
        conn = ConnectionState(addr)
        self.multiplexer.connections[addr] = conn
        if _debug: ProxyClientService._debug("    - conn: %r", conn)

        # associate with this service, but it is not connected until the ack comes back
        conn.service = self

        # keep a list of pending BSLPDU objects until the ack comes back
        conn.pendingBSLPDU = []

        # build a service request
        request = ServiceRequest(PROXY_SERVICE_ID)
        request.pduDestination = addr

        # send it
        self.service_request(request)

        # return the connection object
        return conn

    def connect_ack(self, conn, bslpdu):
        if _debug: ProxyClientService._debug("connect_ack %r %r", conn, bslpdu)

        # if the response is good, consider it connected
        if bslpdu.bslciResultCode == 0:
            # send the pending NPDU if there is one
            if conn.pendingBSLPDU:
                for pdu in conn.pendingBSLPDU:
                    # send it down to the multiplexer
                    self.service_request(pdu)
                conn.pendingBSLPDU = []
        else:
            ProxyClientService._warning("connection nack: %r", bslpdu.bslciResultCode)

    def service_confirmation(self, conn, bslpdu):
        if _debug: ProxyClientService._debug("service_confirmation %r %r", conn, bslpdu)

        # build a PDU
        pdu = PDU(bslpdu)
        if isinstance(bslpdu, ServerToProxyUnicastNPDU):
            pdu.pduDestination = bslpdu.bslciAddress
        elif isinstance(bslpdu, ServerToProxyBroadcastNPDU):
            pdu.pduDestination = LocalBroadcast()
        if _debug: ProxyClientService._debug("    - pdu: %r", pdu)

        # send it downstream
        self.request(pdu)

    def confirmation(self, pdu):
        if _debug: ProxyClientService._debug("confirmation %r ", pdu)

        # we should at least have an address
        if not self.address:
            raise RuntimeError("no connection address")

        # build a bslpdu
        if pdu.pduDestination.addrType == Address.localBroadcastAddr:
            request = ProxyToServerBroadcastNPDU(pdu.pduSource, pdu)
        else:
            request = ProxyToServerUnicastNPDU(pdu.pduSource, pdu)
        request.pduDestination = self.address

        # make sure there is a connection
        conn = self.connections.get(self.address, None)
        if not conn:
            if _debug: ProxyClientService._debug("    - not a connected client")

            # start a connection attempt
            conn = self.connect()

        # if the connection is not connected, queue it, othersize send it
        if not conn.connected:
            # keep a reference to this npdu to send after the ack comes back
            conn.pendingBSLPDU.append(request)
        else:
            # send it
            self.service_request(request)
