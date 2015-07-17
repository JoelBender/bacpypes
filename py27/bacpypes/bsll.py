#!/usr/bin/python

"""
BACnet Streaming Link Layer Module
"""

import hashlib

from .errors import EncodingError, DecodingError
from .debugging import ModuleLogger, DebugContents, bacpypes_debugging

from .pdu import LocalStation, PCI, PDUData

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# a dictionary of message type values and classes
bsl_pdu_types = {}

def register_bslpdu_type(klass):
    bsl_pdu_types[klass.messageType] = klass

#
#   Service Identifiers
#

DEVICE_TO_DEVICE_SERVICE_ID     = 0x01
ROUTER_TO_ROUTER_SERVICE_ID     = 0x02
PROXY_SERVICE_ID                = 0x03
LANE_SERVICE_ID                 = 0x04
CLIENT_SERVER_SERVICE_ID        = 0x05

#
#   Hash Functions
#

_md5 = lambda x: hashlib.md5(x).digest()
_sha1 = lambda x: hashlib.sha1(x).digest()
_sha224 = lambda x: hashlib.sha224(x).digest()
_sha256 = lambda x: hashlib.sha256(x).digest()
_sha384 = lambda x: hashlib.sha384(x).digest()
_sha512 = lambda x: hashlib.sha512(x).digest()

hash_functions = (_md5, _sha1, _sha224, _sha256, _sha384, _sha512)

#
#   Result Codes
#

SUCCESS                         = 0
NO_DEVICE_TO_DEVICE_SERVICE     = 1
NO_ROUTER_TO_ROUTER_SERVICE     = 2
NO_PROXY_SERVICE                = 3
NO_LANE_SERVICE                 = 4
UNRECOGNIZED_SERVICE            = 5
AUTHENTICATION_REQUIRED         = 10    # authentication required
AUTHENTICATION_FAILURE          = 11    # username and/or username/password failure
AUTHENTICATION_NO_SERVICE       = 12    #
AUTHENTICATION_HASH             = 13    # specified hash function not supported

#
#   BSLCI
#

@bacpypes_debugging
class BSLCI(PCI, DebugContents):

    _debug_contents = ('bslciType', 'bslciFunction', 'bslciLength')

    result                              = 0x00
    serviceRequest                      = 0x01

    accessRequest                       = 0x02
    accessChallenge                     = 0x03
    accessResponse                      = 0x04

    deviceToDeviceAPDU                  = 0x05
    routerToRouterNPDU                  = 0x06

    proxyToServerUnicastNPDU            = 0x07
    proxyToServerBroadcastNPDU          = 0x08
    serverToProxyUnicastNPDU            = 0x09
    serverToProxyBroadcastNPDU          = 0x0A

    clientToLESUnicastNPDU              = 0x0B
    clientToLESBroadcastNPDU            = 0x0C
    lesToClientUnicastNPDU              = 0x0D
    lesToClientBroadcastNPDU            = 0x0E

    clientToServerUnicastAPDU           = 0x0F
    clientToServerBroadcastAPDU         = 0x10
    serverToClientUnicastAPDU           = 0x11
    serverToClientBroadcastAPDU         = 0x12

    def __init__(self, *args, **kwargs):
        super(BSLCI, self).__init__(*args, **kwargs)

        self.bslciType = 0x83
        self.bslciFunction = None
        self.bslciLength = None

    def update(self, bslci):
        PCI.update(self, bslci)
        self.bslciType = bslci.bslciType
        self.bslciFunction = bslci.bslciFunction
        self.bslciLength = bslci.bslciLength

    def encode(self, pdu):
        """encode the contents of the BSLCI into the PDU."""
        if _debug: BSLCI._debug("encode %r", pdu)

        # copy the basics
        PCI.update(pdu, self)

        pdu.put( self.bslciType )               # 0x83
        pdu.put( self.bslciFunction )

        if (self.bslciLength != len(self.pduData) + 4):
            raise EncodingError("invalid BSLCI length")

        pdu.put_short( self.bslciLength )

    def decode(self, pdu):
        """decode the contents of the PDU into the BSLCI."""
        if _debug: BSLCI._debug("decode %r", pdu)

        # copy the basics
        PCI.update(self, pdu)

        self.bslciType = pdu.get()
        if self.bslciType != 0x83:
            raise DecodingError("invalid BSLCI type")

        self.bslciFunction = pdu.get()
        self.bslciLength = pdu.get_short()

        if (self.bslciLength != len(pdu.pduData) + 4):
            raise DecodingError("invalid BSLCI length")

#
#   BSLPDU
#

class BSLPDU(BSLCI, PDUData):

    def __init__(self, *args, **kwargs):
        super(BSLPDU, self).__init__(*args, **kwargs)

    def encode(self, pdu):
        BSLCI.encode(self, pdu)
        pdu.put_data(self.pduData)

    def decode(self, pdu):
        BSLCI.decode(self, pdu)
        self.pduData = pdu.get_data(len(pdu.pduData))

#
#   Result
#

class Result(BSLCI):

    _debug_contents = ('bslciResultCode',)

    messageType = BSLCI.result

    def __init__(self, code=None, *args, **kwargs):
        super(Result, self).__init__(*args, **kwargs)

        self.bslciFunction = BSLCI.result
        self.bslciLength = 6
        self.bslciResultCode = code

    def encode(self, bslpdu):
        BSLCI.update(bslpdu, self)
        bslpdu.put_short( self.bslciResultCode )

    def decode(self, bslpdu):
        BSLCI.update(self, bslpdu)
        self.bslciResultCode = bslpdu.get_short()

register_bslpdu_type(Result)

#
#   ServiceRequest
#

class ServiceRequest(BSLCI):

    _debug_contents = ('bslciServiceID',)

    messageType = BSLCI.serviceRequest

    def __init__(self, code=None, *args, **kwargs):
        super(ServiceRequest, self).__init__(*args, **kwargs)

        self.bslciFunction = BSLCI.serviceRequest
        self.bslciLength = 6
        self.bslciServiceID = code

    def encode(self, bslpdu):
        BSLCI.update(bslpdu, self)
        bslpdu.put_short( self.bslciServiceID )

    def decode(self, bslpdu):
        BSLCI.update(self, bslpdu)
        self.bslciServiceID = bslpdu.get_short()

register_bslpdu_type(ServiceRequest)

#
#   AccessRequest
#

class AccessRequest(BSLCI):

    _debug_contents = ('bslciHashFn', 'bslciUsername')

    messageType = BSLCI.accessRequest

    def __init__(self, hashFn=0, username='', *args, **kwargs):
        super(AccessRequest, self).__init__(*args, **kwargs)

        self.bslciFunction = BSLCI.accessRequest
        self.bslciLength = 5
        self.bslciHashFn = hashFn
        self.bslciUsername = username
        if username:
            self.bslciLength += len(username)

    def encode(self, bslpdu):
        BSLCI.update(bslpdu, self)
        bslpdu.put( self.bslciHashFn )
        bslpdu.put_data( self.bslciUsername )

    def decode(self, bslpdu):
        BSLCI.update(self, bslpdu)
        self.bslciHashFn = bslpdu.get()
        self.bslciUsername = bslpdu.get_data(len(bslpdu.pduData))

register_bslpdu_type(AccessRequest)

#
#   AccessChallenge
#

class AccessChallenge(BSLCI):

    _debug_contents = ('bslciHashFn', 'bslciChallenge*')

    messageType = BSLCI.accessChallenge

    def __init__(self, hashFn=0, challenge='', *args, **kwargs):
        super(AccessChallenge, self).__init__(*args, **kwargs)

        self.bslciFunction = BSLCI.accessChallenge
        self.bslciLength = 5
        self.bslciHashFn = hashFn
        self.bslciChallenge = challenge
        if challenge:
            self.bslciLength += len(challenge)

    def encode(self, bslpdu):
        BSLCI.update(bslpdu, self)
        bslpdu.put( self.bslciHashFn )
        bslpdu.put_data( self.bslciChallenge )

    def decode(self, bslpdu):
        BSLCI.update(self, bslpdu)
        self.bslciHashFn = bslpdu.get()
        self.bslciChallenge = bslpdu.get_data(len(bslpdu.pduData))

register_bslpdu_type(AccessChallenge)

#
#   AccessResponse
#

class AccessResponse(BSLCI):

    _debug_contents = ('bslciHashFn', 'bslciResponse*')

    messageType = BSLCI.accessResponse

    def __init__(self, hashFn=0, response='', *args, **kwargs):
        super(AccessResponse, self).__init__(*args, **kwargs)

        self.bslciFunction = BSLCI.accessResponse
        self.bslciLength = 5
        self.bslciHashFn = hashFn
        self.bslciResponse = response
        if response:
            self.bslciLength += len(response)

    def encode(self, bslpdu):
        BSLCI.update(bslpdu, self)
        bslpdu.put( self.bslciHashFn )
        bslpdu.put_data( self.bslciResponse )

    def decode(self, bslpdu):
        BSLCI.update(self, bslpdu)
        self.bslciHashFn = bslpdu.get()
        self.bslciResponse = bslpdu.get_data(len(bslpdu.pduData))

register_bslpdu_type(AccessResponse)

#------------------------------

#
#   DeviceToDeviceAPDU
#

class DeviceToDeviceAPDU(BSLPDU):

    messageType = BSLCI.deviceToDeviceAPDU

    def __init__(self, *args, **kwargs):
        super(DeviceToDeviceAPDU, self).__init__(*args, **kwargs)

        self.bslciFunction = BSLCI.deviceToDeviceAPDU
        self.bslciLength = 4 + len(self.pduData)

    def encode(self, bslpdu):
        # make sure the length is correct
        self.bslciLength = 4 + len(self.pduData)

        BSLCI.update(bslpdu, self)

        # encode the rest of the data
        bslpdu.put_data( self.pduData )

    def decode(self, bslpdu):
        BSLCI.update(self, bslpdu)

        # get the rest of the data
        self.pduData = bslpdu.get_data(len(bslpdu.pduData))

register_bslpdu_type(DeviceToDeviceAPDU)

#
#   RouterToRouterNPDU
#

class RouterToRouterNPDU(BSLPDU):

    messageType = BSLCI.routerToRouterNPDU

    def __init__(self, *args, **kwargs):
        super(RouterToRouterNPDU, self).__init__(*args, **kwargs)

        self.bslciFunction = BSLCI.routerToRouterNPDU
        self.bslciLength = 4 + len(self.pduData)

    def encode(self, bslpdu):
        # make sure the length is correct
        self.bslciLength = 4 + len(self.pduData)

        BSLCI.update(bslpdu, self)

        # encode the rest of the data
        bslpdu.put_data( self.pduData )

    def decode(self, bslpdu):
        BSLCI.update(self, bslpdu)

        # get the rest of the data
        self.pduData = bslpdu.get_data(len(bslpdu.pduData))

register_bslpdu_type(RouterToRouterNPDU)

#
#   ProxyToServerUnicastNPDU
#

class ProxyToServerUnicastNPDU(BSLPDU):

    _debug_contents = ('bslciAddress',)

    messageType = BSLCI.proxyToServerUnicastNPDU

    def __init__(self, addr=None, *args, **kwargs):
        super(ProxyToServerUnicastNPDU, self).__init__(*args, **kwargs)

        self.bslciFunction = BSLCI.proxyToServerUnicastNPDU
        self.bslciLength = 5 + len(self.pduData)
        self.bslciAddress = addr
        if addr is not None:
            self.bslciLength += addr.addrLen

    def encode(self, bslpdu):
        addrLen = self.bslciAddress.addrLen

        # make sure the length is correct
        self.bslciLength = 5 + addrLen + len(self.pduData)

        BSLCI.update(bslpdu, self)

        # encode the address
        bslpdu.put(addrLen)
        bslpdu.put_data( self.bslciAddress.addrAddr )

        # encode the rest of the data
        bslpdu.put_data( self.pduData )

    def decode(self, bslpdu):
        BSLCI.update(self, bslpdu)

        # get the address
        addrLen = bslpdu.get()
        self.bslciAddress = LocalStation(bslpdu.get_data(addrLen))

        # get the rest of the data
        self.pduData = bslpdu.get_data(len(bslpdu.pduData))

register_bslpdu_type(ProxyToServerUnicastNPDU)

#
#   ProxyToServerBroadcastNPDU
#

class ProxyToServerBroadcastNPDU(BSLPDU):

    _debug_contents = ('bslciAddress',)

    messageType = BSLCI.proxyToServerBroadcastNPDU

    def __init__(self, addr=None, *args, **kwargs):
        super(ProxyToServerBroadcastNPDU, self).__init__(*args, **kwargs)

        self.bslciFunction = BSLCI.proxyToServerBroadcastNPDU
        self.bslciLength = 5 + len(self.pduData)
        self.bslciAddress = addr
        if addr is not None:
            self.bslciLength += addr.addrLen

    def encode(self, bslpdu):
        addrLen = self.bslciAddress.addrLen

        # make sure the length is correct
        self.bslciLength = 5 + addrLen + len(self.pduData)

        BSLCI.update(bslpdu, self)

        # encode the address
        bslpdu.put(addrLen)
        bslpdu.put_data( self.bslciAddress.addrAddr )

        # encode the rest of the data
        bslpdu.put_data( self.pduData )

    def decode(self, bslpdu):
        BSLCI.update(self, bslpdu)

        # get the address
        addrLen = bslpdu.get()
        self.bslciAddress = LocalStation(bslpdu.get_data(addrLen))

        # get the rest of the data
        self.pduData = bslpdu.get_data(len(bslpdu.pduData))

register_bslpdu_type(ProxyToServerBroadcastNPDU)

#
#   ServerToProxyUnicastNPDU
#

class ServerToProxyUnicastNPDU(BSLPDU):

    _debug_contents = ('bslciAddress',)

    messageType = BSLCI.serverToProxyUnicastNPDU

    def __init__(self, addr=None, *args, **kwargs):
        super(ServerToProxyUnicastNPDU, self).__init__(*args, **kwargs)

        self.bslciFunction = BSLCI.serverToProxyUnicastNPDU
        self.bslciLength = 5 + len(self.pduData)
        self.bslciAddress = addr
        if addr is not None:
            self.bslciLength += addr.addrLen

    def encode(self, bslpdu):
        addrLen = self.bslciAddress.addrLen

        # make sure the length is correct
        self.bslciLength = 5 + addrLen + len(self.pduData)

        BSLCI.update(bslpdu, self)

        # encode the address
        bslpdu.put(addrLen)
        bslpdu.put_data( self.bslciAddress.addrAddr )

        # encode the rest of the data
        bslpdu.put_data( self.pduData )

    def decode(self, bslpdu):
        BSLCI.update(self, bslpdu)

        # get the address
        addrLen = bslpdu.get()
        self.bslciAddress = LocalStation(bslpdu.get_data(addrLen))

        # get the rest of the data
        self.pduData = bslpdu.get_data(len(bslpdu.pduData))

register_bslpdu_type(ServerToProxyUnicastNPDU)

#
#   ServerToProxyBroadcastNPDU
#

class ServerToProxyBroadcastNPDU(BSLPDU):

    messageType = BSLCI.serverToProxyBroadcastNPDU

    def __init__(self, *args, **kwargs):
        super(ServerToProxyBroadcastNPDU, self).__init__(*args, **kwargs)

        self.bslciFunction = BSLCI.serverToProxyBroadcastNPDU
        self.bslciLength = 4 + len(self.pduData)

    def encode(self, bslpdu):
        BSLCI.update(bslpdu, self)

        # encode the rest of the data
        bslpdu.put_data( self.pduData )

    def decode(self, bslpdu):
        BSLCI.update(self, bslpdu)

        # get the rest of the data
        self.pduData = bslpdu.get_data(len(bslpdu.pduData))

register_bslpdu_type(ServerToProxyBroadcastNPDU)

#
#   ClientToLESUnicastNPDU
#

class ClientToLESUnicastNPDU(BSLPDU):

    _debug_contents = ('bslciAddress',)

    messageType = BSLCI.clientToLESUnicastNPDU

    def __init__(self, addr=None, *args, **kwargs):
        super(ClientToLESUnicastNPDU, self).__init__(*args, **kwargs)

        self.bslciFunction = BSLCI.clientToLESUnicastNPDU
        self.bslciLength = 5 + len(self.pduData)
        self.bslciAddress = addr
        if addr is not None:
            self.bslciLength += addr.addrLen

    def encode(self, bslpdu):
        addrLen = self.bslciAddress.addrLen

        # make sure the length is correct
        self.bslciLength = 5 + addrLen + len(self.pduData)

        BSLCI.update(bslpdu, self)

        # encode the address
        bslpdu.put(addrLen)
        bslpdu.put_data( self.bslciAddress.addrAddr )

        # encode the rest of the data
        bslpdu.put_data( self.pduData )

    def decode(self, bslpdu):
        BSLCI.update(self, bslpdu)

        # get the address
        addrLen = bslpdu.get()
        self.bslciAddress = LocalStation(bslpdu.get_data(addrLen))

        # get the rest of the data
        self.pduData = bslpdu.get_data(len(bslpdu.pduData))

register_bslpdu_type(ClientToLESUnicastNPDU)

#
#   ClientToLESBroadcastNPDU
#

class ClientToLESBroadcastNPDU(BSLPDU):

    _debug_contents = ('bslciAddress',)

    messageType = BSLCI.clientToLESBroadcastNPDU

    def __init__(self, addr=None, *args, **kwargs):
        super(ClientToLESBroadcastNPDU, self).__init__(*args, **kwargs)

        self.bslciFunction = BSLCI.clientToLESBroadcastNPDU
        self.bslciLength = 5 + len(self.pduData)
        self.bslciAddress = addr
        if addr is not None:
            self.bslciLength += addr.addrLen

    def encode(self, bslpdu):
        addrLen = self.bslciAddress.addrLen

        # make sure the length is correct
        self.bslciLength = 5 + addrLen + len(self.pduData)

        BSLCI.update(bslpdu, self)

        # encode the address
        bslpdu.put(addrLen)
        bslpdu.put_data( self.bslciAddress.addrAddr )

        # encode the rest of the data
        bslpdu.put_data( self.pduData )

    def decode(self, bslpdu):
        BSLCI.update(self, bslpdu)

        # get the address
        addrLen = bslpdu.get()
        self.bslciAddress = LocalStation(bslpdu.get_data(addrLen))

        # get the rest of the data
        self.pduData = bslpdu.get_data(len(bslpdu.pduData))

register_bslpdu_type(ClientToLESBroadcastNPDU)

#
#   LESToClientUnicastNPDU
#

class LESToClientUnicastNPDU(BSLPDU):

    _debug_contents = ('bslciAddress',)

    messageType = BSLCI.lesToClientUnicastNPDU

    def __init__(self, addr=None, *args, **kwargs):
        super(LESToClientUnicastNPDU, self).__init__(*args, **kwargs)

        self.bslciFunction = BSLCI.lesToClientUnicastNPDU
        self.bslciLength = 5 + len(self.pduData)
        self.bslciAddress = addr
        if addr is not None:
            self.bslciLength += addr.addrLen

    def encode(self, bslpdu):
        addrLen = self.bslciAddress.addrLen

        # make sure the length is correct
        self.bslciLength = 5 + addrLen + len(self.pduData)

        BSLCI.update(bslpdu, self)

        # encode the address
        bslpdu.put(addrLen)
        bslpdu.put_data( self.bslciAddress.addrAddr )

        # encode the rest of the data
        bslpdu.put_data( self.pduData )

    def decode(self, bslpdu):
        BSLCI.update(self, bslpdu)

        # get the address
        addrLen = bslpdu.get()
        self.bslciAddress = LocalStation(bslpdu.get_data(addrLen))

        # get the rest of the data
        self.pduData = bslpdu.get_data(len(bslpdu.pduData))

register_bslpdu_type(LESToClientUnicastNPDU)

#
#   LESToClientBroadcastNPDU
#

class LESToClientBroadcastNPDU(BSLPDU):

    _debug_contents = ('bslciAddress',)

    messageType = BSLCI.lesToClientBroadcastNPDU

    def __init__(self, addr=None, *args, **kwargs):
        super(LESToClientBroadcastNPDU, self).__init__(*args, **kwargs)

        self.bslciFunction = BSLCI.lesToClientBroadcastNPDU
        self.bslciLength = 5 + len(self.pduData)
        self.bslciAddress = addr
        if addr is not None:
            self.bslciLength += addr.addrLen

    def encode(self, bslpdu):
        addrLen = self.bslciAddress.addrLen

        # make sure the length is correct
        self.bslciLength = 5 + addrLen + len(self.pduData)

        BSLCI.update(bslpdu, self)

        # encode the address
        bslpdu.put(addrLen)
        bslpdu.put_data( self.bslciAddress.addrAddr )

        # encode the rest of the data
        bslpdu.put_data( self.pduData )

    def decode(self, bslpdu):
        BSLCI.update(self, bslpdu)

        # get the address
        addrLen = bslpdu.get()
        self.bslciAddress = LocalStation(bslpdu.get_data(addrLen))

        # get the rest of the data
        self.pduData = bslpdu.get_data(len(bslpdu.pduData))

register_bslpdu_type(LESToClientBroadcastNPDU)

#
#   ClientToServerUnicastAPDU
#

class ClientToServerUnicastAPDU(BSLPDU):

    _debug_contents = ('bslciAddress',)

    messageType = BSLCI.clientToServerUnicastAPDU

    def __init__(self, addr=None, *args, **kwargs):
        super(ClientToServerUnicastAPDU, self).__init__(*args, **kwargs)

        self.bslciFunction = BSLCI.clientToServerUnicastAPDU
        self.bslciLength = 5 + len(self.pduData)
        self.bslciAddress = addr
        if addr is not None:
            self.bslciLength += addr.addrLen

    def encode(self, bslpdu):
        addrLen = self.bslciAddress.addrLen

        # make sure the length is correct
        self.bslciLength = 5 + addrLen + len(self.pduData)

        BSLCI.update(bslpdu, self)

        # encode the address
        bslpdu.put(addrLen)
        bslpdu.put_data( self.bslciAddress.addrAddr )

        # encode the rest of the data
        bslpdu.put_data( self.pduData )

    def decode(self, bslpdu):
        BSLCI.update(self, bslpdu)

        # get the address
        addrLen = bslpdu.get()
        self.bslciAddress = LocalStation(bslpdu.get_data(addrLen))

        # get the rest of the data
        self.pduData = bslpdu.get_data(len(bslpdu.pduData))

register_bslpdu_type(ClientToServerUnicastAPDU)

#
#   ClientToServerBroadcastAPDU
#

class ClientToServerBroadcastAPDU(BSLPDU):

    _debug_contents = ('bslciAddress',)

    messageType = BSLCI.clientToServerBroadcastAPDU

    def __init__(self, addr=None, *args, **kwargs):
        super(ClientToServerBroadcastAPDU, self).__init__(*args, **kwargs)

        self.bslciFunction = BSLCI.clientToServerBroadcastAPDU
        self.bslciLength = 5 + len(self.pduData)
        self.bslciAddress = addr
        if addr is not None:
            self.bslciLength += addr.addrLen

    def encode(self, bslpdu):
        addrLen = self.bslciAddress.addrLen

        # make sure the length is correct
        self.bslciLength = 5 + addrLen + len(self.pduData)

        BSLCI.update(bslpdu, self)

        # encode the address
        bslpdu.put(addrLen)
        bslpdu.put_data( self.bslciAddress.addrAddr )

        # encode the rest of the data
        bslpdu.put_data( self.pduData )

    def decode(self, bslpdu):
        BSLCI.update(self, bslpdu)

        # get the address
        addrLen = bslpdu.get()
        self.bslciAddress = LocalStation(bslpdu.get_data(addrLen))

        # get the rest of the data
        self.pduData = bslpdu.get_data(len(bslpdu.pduData))

register_bslpdu_type(ClientToServerBroadcastAPDU)

#
#   ServerToClientUnicastAPDU
#

class ServerToClientUnicastAPDU(BSLPDU):

    _debug_contents = ('bslciAddress',)

    messageType = BSLCI.serverToClientUnicastAPDU

    def __init__(self, addr=None, *args, **kwargs):
        super(ServerToClientUnicastAPDU, self).__init__(*args, **kwargs)

        self.bslciFunction = BSLCI.serverToClientUnicastAPDU
        self.bslciLength = 5 + len(self.pduData)
        self.bslciAddress = addr
        if addr is not None:
            self.bslciLength += addr.addrLen

    def encode(self, bslpdu):
        addrLen = self.bslciAddress.addrLen

        # make sure the length is correct
        self.bslciLength = 5 + addrLen + len(self.pduData)

        BSLCI.update(bslpdu, self)

        # encode the address
        bslpdu.put(addrLen)
        bslpdu.put_data( self.bslciAddress.addrAddr )

        # encode the rest of the data
        bslpdu.put_data( self.pduData )

    def decode(self, bslpdu):
        BSLCI.update(self, bslpdu)

        # get the address
        addrLen = bslpdu.get()
        self.bslciAddress = LocalStation(bslpdu.get_data(addrLen))

        # get the rest of the data
        self.pduData = bslpdu.get_data(len(bslpdu.pduData))

register_bslpdu_type(ServerToClientUnicastAPDU)

#
#   ServerToClientBroadcastAPDU
#

class ServerToClientBroadcastAPDU(BSLPDU):

    _debug_contents = ('bslciAddress',)

    messageType = BSLCI.serverToClientBroadcastAPDU

    def __init__(self, addr=None, *args, **kwargs):
        super(ServerToClientBroadcastAPDU, self).__init__(*args, **kwargs)

        self.bslciFunction = BSLCI.serverToClientBroadcastAPDU
        self.bslciLength = 5 + len(self.pduData)
        self.bslciAddress = addr
        if addr is not None:
            self.bslciLength += addr.addrLen

    def encode(self, bslpdu):
        addrLen = self.bslciAddress.addrLen

        # make sure the length is correct
        self.bslciLength = 5 + addrLen + len(self.pduData)

        BSLCI.update(bslpdu, self)

        # encode the address
        bslpdu.put(addrLen)
        bslpdu.put_data( self.bslciAddress.addrAddr )

        # encode the rest of the data
        bslpdu.put_data( self.pduData )

    def decode(self, bslpdu):
        BSLCI.update(self, bslpdu)

        # get the address
        addrLen = bslpdu.get()
        self.bslciAddress = LocalStation(bslpdu.get_data(addrLen))

        # get the rest of the data
        self.pduData = bslpdu.get_data(len(bslpdu.pduData))

register_bslpdu_type(ServerToClientBroadcastAPDU)

