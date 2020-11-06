#!/usr/bin/python

"""
BACnet Virtual Link Layer Service
"""

import sys
import struct

from .settings import settings
from .debugging import ModuleLogger, DebugContents, bacpypes_debugging

from .udp import UDPDirector
from .task import OneShotFunction, OneShotTask, RecurringTask
from .comm import Client, Server, bind, \
    ServiceAccessPoint, ApplicationServiceElement

from .pdu import Address, LocalBroadcast, PDU, \
    unpack_ip_addr
from .bvll import BVLPDU, DeleteForeignDeviceTableEntry, \
    DistributeBroadcastToNetwork, FDTEntry, ForwardedNPDU, \
    OriginalBroadcastNPDU, OriginalUnicastNPDU, \
    ReadBroadcastDistributionTable, ReadBroadcastDistributionTableAck, \
    ReadForeignDeviceTable, ReadForeignDeviceTableAck, RegisterForeignDevice, \
    Result, WriteBroadcastDistributionTable, bvl_pdu_types

# some debugging
_debug = 0
_log = ModuleLogger(globals())

#
#   _Multiplex Client and Server
#

class _MultiplexClient(Client):

    def __init__(self, mux):
        Client.__init__(self)
        self.multiplexer = mux

    def confirmation(self, pdu):
        self.multiplexer.confirmation(self, pdu)

class _MultiplexServer(Server):

    def __init__(self, mux):
        Server.__init__(self)
        self.multiplexer = mux

    def indication(self, pdu):
        self.multiplexer.indication(self, pdu)

#
#   UDPMultiplexer
#

@bacpypes_debugging
class UDPMultiplexer:

    def __init__(self, addr=None, noBroadcast=False):
        if _debug: UDPMultiplexer._debug("__init__ %r noBroadcast=%r", addr, noBroadcast)

        # check for some options
        specialBroadcast = False
        if addr is None:
            self.address = Address()
            self.addrTuple = ('', 47808)
            self.addrBroadcastTuple = ('255.255.255.255', 47808)
        else:
            # allow the address to be cast
            if isinstance(addr, Address):
                self.address = addr
            else:
                self.address = Address(addr)

            # promote the normal and broadcast tuples
            self.addrTuple = self.address.addrTuple
            self.addrBroadcastTuple = self.address.addrBroadcastTuple

            # check for no broadcasting (loopback interface)
            if not self.addrBroadcastTuple:
                noBroadcast = True
            elif (self.addrTuple == self.addrBroadcastTuple):
                # old school broadcast address
                self.addrBroadcastTuple = ('255.255.255.255', self.addrTuple[1])
            else:
                specialBroadcast = True

        if _debug:
            UDPMultiplexer._debug("    - address: %r", self.address)
            UDPMultiplexer._debug("    - addrTuple: %r", self.addrTuple)
            UDPMultiplexer._debug("    - addrBroadcastTuple: %r", self.addrBroadcastTuple)
            UDPMultiplexer._debug("    - route_aware: %r", settings.route_aware)

        # create and bind the direct address
        self.direct = _MultiplexClient(self)
        self.directPort = UDPDirector(self.addrTuple)
        bind(self.direct, self.directPort)

        # create and bind the broadcast address for non-Windows
        if specialBroadcast and (not noBroadcast) and sys.platform in ('linux2', 'darwin'):
            self.broadcast = _MultiplexClient(self)
            self.broadcastPort = UDPDirector(self.addrBroadcastTuple, reuse=True)
            bind(self.broadcast, self.broadcastPort)
        else:
            self.broadcast = None
            self.broadcastPort = None

        # create and bind the Annex H and J servers
        self.annexH = _MultiplexServer(self)
        self.annexJ = _MultiplexServer(self)

    def close_socket(self):
        if _debug: UDPMultiplexer._debug("close_socket")

        # pass along the close to the director(s)
        self.directPort.close_socket()
        if self.broadcastPort:
            self.broadcastPort.close_socket()

    def indication(self, server, pdu):
        if _debug: UDPMultiplexer._debug("indication %r %r", server, pdu)

        # broadcast message
        if pdu.pduDestination.addrType == Address.localBroadcastAddr:
            dest = self.addrBroadcastTuple
            if _debug: UDPMultiplexer._debug("    - requesting local broadcast: %r", dest)

            # interface might not support broadcasts
            if not dest:
                return

        # unicast message
        elif pdu.pduDestination.addrType == Address.localStationAddr:
            dest = unpack_ip_addr(pdu.pduDestination.addrAddr)
            if _debug: UDPMultiplexer._debug("    - requesting local station: %r", dest)

        else:
            raise RuntimeError("invalid destination address type")

        self.directPort.indication(PDU(pdu, destination=dest))

    def confirmation(self, client, pdu):
        if _debug: UDPMultiplexer._debug("confirmation %r %r", client, pdu)

        # if this came from ourselves, dump it
        if pdu.pduSource == self.addrTuple:
            if _debug: UDPMultiplexer._debug("    - from us!")
            return

        # the PDU source is a tuple, convert it to an Address instance
        src = Address(pdu.pduSource)

        # match the destination in case the stack needs it
        if client is self.direct:
            dest = self.address
        elif client is self.broadcast:
            dest = LocalBroadcast()
        else:
            raise RuntimeError("confirmation mismatch")

        # must have at least one octet
        if not pdu.pduData:
            if _debug: UDPMultiplexer._debug("    - no data")
            return

        # extract the first octet
        msg_type = struct.unpack('B', pdu.pduData[:1])[0]
        if _debug: UDPMultiplexer._debug("    - msg_type: %r", msg_type)

        # check for the message type
        if msg_type == 0x01:
            if self.annexH.serverPeer:
                self.annexH.response(PDU(pdu, source=src, destination=dest))
        elif msg_type == 0x81:
            if self.annexJ.serverPeer:
                self.annexJ.response(PDU(pdu, source=src, destination=dest))
        else:
            UDPMultiplexer._warning("unsupported message")

#
#   BTR
#

@bacpypes_debugging
class BTR(Client, Server, DebugContents):

    _debug_contents = ('peers+',)

    def __init__(self, cid=None, sid=None):
        """An Annex-H BACnet Tunneling Router node."""
        if _debug: BTR._debug("__init__ cid=%r sid=%r", cid, sid)
        Client.__init__(self, cid)
        Server.__init__(self, sid)

        # initialize a dicitonary of peers
        self.peers = {}

    def indication(self, pdu):
        if _debug: BTR._debug("indication %r", pdu)

        # check for local stations
        if pdu.pduDestination.addrType == Address.localStationAddr:
            # make sure it is going to a peer
            if pdu.pduDestination not in self.peers:
                ### log this
                return

            # send it downstream
            self.request(pdu)

        # check for broadcasts
        elif pdu.pduDestination.addrType == Address.localBroadcastAddr:
            # loop through the peers
            for peerAddr in self.peers.keys():
                xpdu = PDU(pdu.pduData, destination=peerAddr)

                # send it downstream
                self.request(xpdu)

        else:
            raise RuntimeError("invalid destination address type (2)")

    def confirmation(self, pdu):
        if _debug: BTR._debug("confirmation %r", pdu)

        # make sure it came from a peer
        if pdu.pduSource not in self.peers:
            BTR._warning("not a peer: %r", pdu.pduSource)
            return

        # send it upstream
        self.response(pdu)

    def add_peer(self, peerAddr, networks=None):
        """Add a peer and optionally provide a list of the reachable networks."""
        if _debug: BTR._debug("add_peer %r networks=%r", peerAddr, networks)

        # see if this is already a peer
        if peerAddr in self.peers:
            # add the (new?) reachable networks
            if not networks:
                networks = []
            else:
                self.peers[peerAddr].extend(networks)
        else:
            if not networks:
                networks = []

            # save the networks
            self.peers[peerAddr] = networks

        ### send a control message upstream that these are reachable

    def delete_peer(self, peerAddr):
        """Delete a peer."""
        if _debug: BTR._debug("delete_peer %r", peerAddr)

        # get the peer networks
        # networks = self.peers[peerAddr]

        ### send a control message upstream that these are no longer reachable

        # now delete the peer
        del self.peers[peerAddr]

#
#   AnnexJCodec
#

@bacpypes_debugging
class AnnexJCodec(Client, Server):

    def __init__(self, cid=None, sid=None):
        if _debug: AnnexJCodec._debug("__init__ cid=%r sid=%r", cid, sid)
        Client.__init__(self, cid)
        Server.__init__(self, sid)

    def indication(self, rpdu):
        if _debug: AnnexJCodec._debug("indication %r", rpdu)

        # encode it as a generic BVLL PDU
        bvlpdu = BVLPDU()
        rpdu.encode(bvlpdu)

        # encode it as a PDU
        pdu = PDU()
        bvlpdu.encode(pdu)

        # send it downstream
        self.request(pdu)

    def confirmation(self, pdu):
        if _debug: AnnexJCodec._debug("confirmation %r", pdu)

        # interpret as a BVLL PDU
        bvlpdu = BVLPDU()
        bvlpdu.decode(pdu)

        # get the class related to the function
        rpdu = bvl_pdu_types[bvlpdu.bvlciFunction]()
        rpdu.decode(bvlpdu)

        # send it upstream
        self.response(rpdu)

#
#   BIPSAP
#

@bacpypes_debugging
class BIPSAP(ServiceAccessPoint):

    def __init__(self, sap=None):
        """A BIP service access point."""
        if _debug: BIPSAP._debug("__init__ sap=%r", sap)
        ServiceAccessPoint.__init__(self, sap)

    def sap_indication(self, pdu):
        if _debug: BIPSAP._debug("sap_indication %r", pdu)

        # this is a request initiated by the ASE, send this downstream
        self.request(pdu)

    def sap_confirmation(self, pdu):
        if _debug: BIPSAP._debug("sap_confirmation %r", pdu)

        # this is a response from the ASE, send this downstream
        self.request(pdu)

#
#   BIPSimple
#

@bacpypes_debugging
class BIPSimple(BIPSAP, Client, Server):

    def __init__(self, sapID=None, cid=None, sid=None):
        """A BIP node."""
        if _debug: BIPSimple._debug("__init__ sapID=%r cid=%r sid=%r", sapID, cid, sid)
        BIPSAP.__init__(self, sapID)
        Client.__init__(self, cid)
        Server.__init__(self, sid)

    def indication(self, pdu):
        if _debug: BIPSimple._debug("indication %r", pdu)

        # check for local stations
        if pdu.pduDestination.addrType == Address.localStationAddr:
            # make an original unicast PDU
            xpdu = OriginalUnicastNPDU(pdu, destination=pdu.pduDestination, user_data=pdu.pduUserData)
            if _debug: BIPSimple._debug("    - xpdu: %r", xpdu)

            # send it downstream
            self.request(xpdu)

        # check for broadcasts
        elif pdu.pduDestination.addrType == Address.localBroadcastAddr:
            # make an original broadcast PDU
            xpdu = OriginalBroadcastNPDU(pdu, destination=pdu.pduDestination, user_data=pdu.pduUserData)
            if _debug: BIPSimple._debug("    - xpdu: %r", xpdu)

            # send it downstream
            self.request(xpdu)

        else:
            BIPSimple._warning("invalid destination address: %r", pdu.pduDestination)

    def confirmation(self, pdu):
        if _debug: BIPSimple._debug("confirmation %r", pdu)

        # some kind of response to a request
        if isinstance(pdu, Result):
            # send this to the service access point
            self.sap_response(pdu)

        elif isinstance(pdu, ReadBroadcastDistributionTableAck):
            # send this to the service access point
            self.sap_response(pdu)

        elif isinstance(pdu, ReadForeignDeviceTableAck):
            # send this to the service access point
            self.sap_response(pdu)

        elif isinstance(pdu, OriginalUnicastNPDU):
            # build a vanilla PDU
            xpdu = PDU(pdu.pduData, source=pdu.pduSource, destination=pdu.pduDestination, user_data=pdu.pduUserData)
            if _debug: BIPSimple._debug("    - xpdu: %r", xpdu)

            # send it upstream
            self.response(xpdu)

        elif isinstance(pdu, OriginalBroadcastNPDU):
            # build a PDU with a local broadcast address
            xpdu = PDU(pdu.pduData, source=pdu.pduSource, destination=LocalBroadcast(), user_data=pdu.pduUserData)
            if _debug: BIPSimple._debug("    - xpdu: %r", xpdu)

            # send it upstream
            self.response(xpdu)

        elif isinstance(pdu, ForwardedNPDU):
            # build a PDU with the source from the real source
            xpdu = PDU(pdu.pduData, source=pdu.bvlciAddress, destination=LocalBroadcast(), user_data=pdu.pduUserData)
            if _debug: BIPSimple._debug("    - xpdu: %r", xpdu)

            # send it upstream
            self.response(xpdu)

        elif isinstance(pdu, WriteBroadcastDistributionTable):
            # build a response
            xpdu = Result(code=0x0010, user_data=pdu.pduUserData)
            xpdu.pduDestination = pdu.pduSource

            # send it downstream
            self.request(xpdu)

        elif isinstance(pdu, ReadBroadcastDistributionTable):
            # build a response
            xpdu = Result(code=0x0020, user_data=pdu.pduUserData)
            xpdu.pduDestination = pdu.pduSource

            # send it downstream
            self.request(xpdu)

        elif isinstance(pdu, RegisterForeignDevice):
            # build a response
            xpdu = Result(code=0x0030, user_data=pdu.pduUserData)
            xpdu.pduDestination = pdu.pduSource

            # send it downstream
            self.request(xpdu)

        elif isinstance(pdu, ReadForeignDeviceTable):
            # build a response
            xpdu = Result(code=0x0040, user_data=pdu.pduUserData)
            xpdu.pduDestination = pdu.pduSource

            # send it downstream
            self.request(xpdu)

        elif isinstance(pdu, DeleteForeignDeviceTableEntry):
            # build a response
            xpdu = Result(code=0x0050, user_data=pdu.pduUserData)
            xpdu.pduDestination = pdu.pduSource

            # send it downstream
            self.request(xpdu)

        elif isinstance(pdu, DistributeBroadcastToNetwork):
            # build a response
            xpdu = Result(code=0x0060, user_data=pdu.pduUserData)
            xpdu.pduDestination = pdu.pduSource

            # send it downstream
            self.request(xpdu)

        else:
            BIPSimple._warning("invalid pdu type: %s", type(pdu))

#
#   BIPForeign
#

@bacpypes_debugging
class BIPForeign(BIPSAP, Client, Server, OneShotTask, DebugContents):

    _debug_contents = ('registrationStatus', 'bbmdAddress', 'bbmdTimeToLive')

    def __init__(self, addr=None, ttl=None, sapID=None, cid=None, sid=None):
        """A BIP node."""
        if _debug: BIPForeign._debug("__init__ addr=%r ttl=%r sapID=%r cid=%r sid=%r", addr, ttl, sapID, cid, sid)
        BIPSAP.__init__(self, sapID)
        Client.__init__(self, cid)
        Server.__init__(self, sid)
        OneShotTask.__init__(self)

        # -2=unregistered, -1=not attempted or no ack, 0=OK, >0 error
        self.registrationStatus = -1

        # clear the BBMD address and time-to-live
        self.bbmdAddress = None
        self.bbmdTimeToLive = None

        # used in tracking active registration timeouts
        self._registration_timeout_task = OneShotFunction(self._registration_expired)

        # registration provided
        if addr:
            # a little error checking
            if ttl is None:
                raise RuntimeError("BBMD address and time-to-live must both be specified")

            self.register(addr, ttl)

    def indication(self, pdu):
        if _debug: BIPForeign._debug("indication %r", pdu)

        # check for local stations
        if pdu.pduDestination.addrType == Address.localStationAddr:
            # make an original unicast PDU
            xpdu = OriginalUnicastNPDU(pdu, user_data=pdu.pduUserData)
            xpdu.pduDestination = pdu.pduDestination

            # send it downstream
            self.request(xpdu)

        # check for broadcasts
        elif pdu.pduDestination.addrType == Address.localBroadcastAddr:
            # check the BBMD registration status, we may not be registered
            if self.registrationStatus != 0:
                if _debug: BIPForeign._debug("    - packet dropped, unregistered")
                return

            # make an original broadcast PDU
            xpdu = DistributeBroadcastToNetwork(pdu, user_data=pdu.pduUserData)
            xpdu.pduDestination = self.bbmdAddress

            # send it downstream
            self.request(xpdu)

        else:
            BIPForeign._warning("invalid destination address: %r", pdu.pduDestination)

    def confirmation(self, pdu):
        if _debug: BIPForeign._debug("confirmation %r", pdu)

        # check for a registration request result
        if isinstance(pdu, Result):
            # if we are unbinding, do nothing
            if self.registrationStatus == -2:
                return

            ### make sure we have a bind request in process

            # make sure the result is from the bbmd
            if pdu.pduSource != self.bbmdAddress:
                if _debug: BIPForeign._debug("    - packet dropped, not from the BBMD")
                return

            # save the result code as the status
            self.registrationStatus = pdu.bvlciResultCode

            # If successful, track registration timeout
            if self.registrationStatus == 0:
                self._start_track_registration()

            return

        if isinstance(pdu, OriginalUnicastNPDU):
            # build a vanilla PDU
            xpdu = PDU(pdu.pduData, source=pdu.pduSource, destination=pdu.pduDestination, user_data=pdu.pduUserData)

            # send it upstream
            self.response(xpdu)

        elif isinstance(pdu, ForwardedNPDU):
            # check the BBMD registration status, we may not be registered
            if self.registrationStatus != 0:
                if _debug: BIPForeign._debug("    - packet dropped, unregistered")
                return

            # make sure the forwarded PDU from the bbmd
            if pdu.pduSource != self.bbmdAddress:
                if _debug: BIPForeign._debug("    - packet dropped, not from the BBMD")
                return

            # build a PDU with the source from the real source
            xpdu = PDU(pdu.pduData, source=pdu.bvlciAddress, destination=LocalBroadcast(), user_data=pdu.pduUserData)

            # send it upstream
            self.response(xpdu)

        elif isinstance(pdu, ReadBroadcastDistributionTableAck):
            # send this to the service access point
            self.sap_response(pdu)

        elif isinstance(pdu, ReadForeignDeviceTableAck):
            # send this to the service access point
            self.sap_response(pdu)

        elif isinstance(pdu, WriteBroadcastDistributionTable):
            # build a response
            xpdu = Result(code=0x0010, user_data=pdu.pduUserData)
            xpdu.pduDestination = pdu.pduSource

            # send it downstream
            self.request(xpdu)

        elif isinstance(pdu, ReadBroadcastDistributionTable):
            # build a response
            xpdu = Result(code=0x0020, user_data=pdu.pduUserData)
            xpdu.pduDestination = pdu.pduSource

            # send it downstream
            self.request(xpdu)

        elif isinstance(pdu, RegisterForeignDevice):
            # build a response
            xpdu = Result(code=0x0030, user_data=pdu.pduUserData)
            xpdu.pduDestination = pdu.pduSource

            # send it downstream
            self.request(xpdu)

        elif isinstance(pdu, ReadForeignDeviceTable):
            # build a response
            xpdu = Result(code=0x0040, user_data=pdu.pduUserData)
            xpdu.pduDestination = pdu.pduSource

            # send it downstream
            self.request(xpdu)

        elif isinstance(pdu, DeleteForeignDeviceTableEntry):
            # build a response
            xpdu = Result(code=0x0050, user_data=pdu.pduUserData)
            xpdu.pduDestination = pdu.pduSource

            # send it downstream
            self.request(xpdu)

        elif isinstance(pdu, DistributeBroadcastToNetwork):
            # build a response
            xpdu = Result(code=0x0060, user_data=pdu.pduUserData)
            xpdu.pduDestination = pdu.pduSource

            # send it downstream
            self.request(xpdu)

        elif isinstance(pdu, OriginalBroadcastNPDU):
            if _debug: BIPForeign._debug("    - packet dropped")

        else:
            BIPForeign._warning("invalid pdu type: %s", type(pdu))

    def register(self, addr, ttl):
        """Start the foreign device registration process with the given BBMD.

        Registration will be renewed periodically according to the ttl value
        until explicitly stopped by a call to `unregister`.
        """
        # a little error checking
        if ttl <= 0:
            raise ValueError("time-to-live must be greater than zero")

        # save the BBMD address and time-to-live
        if isinstance(addr, Address):
            self.bbmdAddress = addr
        else:
            self.bbmdAddress = Address(addr)
        self.bbmdTimeToLive = ttl

        # install this task to do registration renewal according to the TTL
        # and stop tracking any active registration timeouts
        self.install_task(when=0)
        self._stop_track_registration()

    def unregister(self):
        """Stop the foreign device registration process.

        Immediately drops active foreign device registration and stops further
        registration renewals.
        """

        pdu = RegisterForeignDevice(0)
        pdu.pduDestination = self.bbmdAddress

        # send it downstream
        self.request(pdu)

        # change the status to unregistered
        self.registrationStatus = -2

        # clear the BBMD address and time-to-live
        self.bbmdAddress = None
        self.bbmdTimeToLive = None

        # unschedule registration renewal & timeout tracking if previously
        # scheduled
        self.suspend_task()
        self._stop_track_registration()

    def process_task(self):
        """Called when the registration request should be sent to the BBMD."""
        pdu = RegisterForeignDevice(self.bbmdTimeToLive)
        pdu.pduDestination = self.bbmdAddress

        # send it downstream
        self.request(pdu)

        # schedule the next registration renewal
        self.install_task(delta=self.bbmdTimeToLive)

    def _start_track_registration(self):
        # From J.5.2.3 Foreign Device Table Operation (paraphrasing): if a
        # foreign device does not renew its registration 30 seconds after its
        # TTL expired then it will be removed from the BBMD's FDT.
        #
        # Thus, if we're registered and don't get a response to a subsequent
        # renewal request 30 seconds after our TTL expired then we're
        # definitely not registered anymore.
        self._registration_timeout_task.install_task(delta=self.bbmdTimeToLive + 30)

    def _stop_track_registration(self):
        self._registration_timeout_task.suspend_task()

    def _registration_expired(self):
        """Called when detecting that foreign device registration has
        definitely expired.
        """
        self.registrationStatus = -2  # Unregistered
        self._stop_track_registration()

#
#   BIPBBMD
#

@bacpypes_debugging
class BIPBBMD(BIPSAP, Client, Server, RecurringTask, DebugContents):

    _debug_contents = ('bbmdAddress', 'bbmdBDT+', 'bbmdFDT+')

    def __init__(self, addr, sapID=None, cid=None, sid=None):
        """A BBMD node."""
        if _debug: BIPBBMD._debug("__init__ %r sapID=%r cid=%r sid=%r", addr, sapID, cid, sid)
        BIPSAP.__init__(self, sapID)
        Client.__init__(self, cid)
        Server.__init__(self, sid)
        RecurringTask.__init__(self, 1000.0)

        self.bbmdAddress = addr
        self.bbmdBDT = []
        self.bbmdFDT = []

        # install so process_task runs
        self.install_task()

    def indication(self, pdu):
        if _debug: BIPBBMD._debug("indication %r", pdu)

        # check for local stations
        if pdu.pduDestination.addrType == Address.localStationAddr:
            # make an original unicast PDU
            xpdu = OriginalUnicastNPDU(pdu, user_data=pdu.pduUserData)
            xpdu.pduDestination = pdu.pduDestination
            if _debug: BIPBBMD._debug("    - original unicast xpdu: %r", xpdu)

            # send it downstream
            self.request(xpdu)

        # check for broadcasts
        elif pdu.pduDestination.addrType == Address.localBroadcastAddr:
            # make an original broadcast PDU
            xpdu = OriginalBroadcastNPDU(pdu, user_data=pdu.pduUserData)
            xpdu.pduDestination = pdu.pduDestination
            if _debug: BIPBBMD._debug("    - original broadcast xpdu: %r", xpdu)

            # send it downstream
            self.request(xpdu)

            # make a forwarded PDU
            xpdu = ForwardedNPDU(self.bbmdAddress, pdu, user_data=pdu.pduUserData)
            if _debug: BIPBBMD._debug("    - forwarded xpdu: %r", xpdu)

            # send it to the peers
            for bdte in self.bbmdBDT:
                if bdte != self.bbmdAddress:
                    xpdu.pduDestination = Address( ((bdte.addrIP|~bdte.addrMask), bdte.addrPort) )
                    BIPBBMD._debug("    - sending to peer: %r", xpdu.pduDestination)
                    self.request(xpdu)

            # send it to the registered foreign devices
            for fdte in self.bbmdFDT:
                xpdu.pduDestination = fdte.fdAddress
                if _debug: BIPBBMD._debug("    - sending to foreign device: %r", xpdu.pduDestination)
                self.request(xpdu)

        else:
            BIPBBMD._warning("invalid destination address: %r", pdu.pduDestination)

    def confirmation(self, pdu):
        if _debug: BIPBBMD._debug("confirmation %r",  pdu)

        # some kind of response to a request
        if isinstance(pdu, Result):
            # send this to the service access point
            self.sap_response(pdu)

        elif isinstance(pdu, WriteBroadcastDistributionTable):
            # build a response
            xpdu = Result(code=0x0010, user_data=pdu.pduUserData)
            xpdu.pduDestination = pdu.pduSource
            if _debug: BIPBBMD._debug("    - xpdu: %r", xpdu)

            # send it downstream
            self.request(xpdu)

        elif isinstance(pdu, ReadBroadcastDistributionTable):
            # build a response
            xpdu = ReadBroadcastDistributionTableAck(self.bbmdBDT, user_data=pdu.pduUserData)
            xpdu.pduDestination = pdu.pduSource
            if _debug: BIPBBMD._debug("    - xpdu: %r", xpdu)

            # send it downstream
            self.request(xpdu)

        elif isinstance(pdu, ReadBroadcastDistributionTableAck):
            # send this to the service access point
            self.sap_response(pdu)

        elif isinstance(pdu, ForwardedNPDU):
            # send it upstream if there is a network layer
            if self.serverPeer:
                # build a PDU with a local broadcast address
                xpdu = PDU(pdu.pduData, source=pdu.bvlciAddress, destination=LocalBroadcast(), user_data=pdu.pduUserData)
                if _debug: BIPBBMD._debug("    - upstream xpdu: %r", xpdu)

                self.response(xpdu)

            # build a forwarded NPDU to send out
            xpdu = ForwardedNPDU(pdu.bvlciAddress, pdu, destination=None, user_data=pdu.pduUserData)
            if _debug: BIPBBMD._debug("    - forwarded xpdu: %r", xpdu)

            # if this was unicast to us, do next hop
            if pdu.pduDestination.addrType == Address.localStationAddr:
                if _debug: BIPBBMD._debug("    - unicast message")

                # if this BBMD is listed in its BDT, send a local broadcast
                if self.bbmdAddress in self.bbmdBDT:
                    xpdu.pduDestination = LocalBroadcast()
                    if _debug: BIPBBMD._debug("    - local broadcast")
                    self.request(xpdu)

            elif pdu.pduDestination.addrType == Address.localBroadcastAddr:
                if _debug: BIPBBMD._debug("    - directed broadcast message")

            else:
                BIPBBMD._warning("invalid destination address: %r", pdu.pduDestination)

            # send it to the registered foreign devices
            for fdte in self.bbmdFDT:
                xpdu.pduDestination = fdte.fdAddress
                if _debug: BIPBBMD._debug("    - sending to foreign device: %r", xpdu.pduDestination)
                self.request(xpdu)

        elif isinstance(pdu, RegisterForeignDevice):
            # process the request
            stat = self.register_foreign_device(pdu.pduSource, pdu.bvlciTimeToLive)

            # build a response
            xpdu = Result(code=stat, destination=pdu.pduSource, user_data=pdu.pduUserData)
            if _debug: BIPBBMD._debug("    - xpdu: %r", xpdu)

            # send it downstream
            self.request(xpdu)

        elif isinstance(pdu, ReadForeignDeviceTable):
            # build a response
            xpdu = ReadForeignDeviceTableAck(self.bbmdFDT, destination=pdu.pduSource, user_data=pdu.pduUserData)
            if _debug: BIPBBMD._debug("    - xpdu: %r", xpdu)

            # send it downstream
            self.request(xpdu)

        elif isinstance(pdu, ReadForeignDeviceTableAck):
            # send this to the service access point
            self.sap_response(pdu)

        elif isinstance(pdu, DeleteForeignDeviceTableEntry):
            # process the request
            stat = self.delete_foreign_device_table_entry(pdu.bvlciAddress)

            # build a response
            xpdu = Result(code=stat, user_data=pdu.pduUserData)
            xpdu.pduDestination = pdu.pduSource
            if _debug: BIPBBMD._debug("    - xpdu: %r", xpdu)

            # send it downstream
            self.request(xpdu)

        elif isinstance(pdu, DistributeBroadcastToNetwork):
            # send it upstream if there is a network layer
            if self.serverPeer:
                # build a PDU with a local broadcast address
                xpdu = PDU(pdu.pduData, source=pdu.pduSource, destination=LocalBroadcast(), user_data=pdu.pduUserData)
                if _debug: BIPBBMD._debug("    - upstream xpdu: %r", xpdu)

                self.response(xpdu)

            # build a forwarded NPDU to send out
            xpdu = ForwardedNPDU(pdu.pduSource, pdu, user_data=pdu.pduUserData)
            if _debug: BIPBBMD._debug("    - forwarded xpdu: %r", xpdu)

            # send it to the peers
            for bdte in self.bbmdBDT:
                if bdte == self.bbmdAddress:
                    xpdu.pduDestination = LocalBroadcast()
                    if _debug: BIPBBMD._debug("    - local broadcast")
                    self.request(xpdu)
                else:
                    xpdu.pduDestination = Address( ((bdte.addrIP|~bdte.addrMask), bdte.addrPort) )
                    if _debug: BIPBBMD._debug("    - sending to peer: %r", xpdu.pduDestination)
                    self.request(xpdu)

            # send it to the other registered foreign devices
            for fdte in self.bbmdFDT:
                if fdte.fdAddress != pdu.pduSource:
                    xpdu.pduDestination = fdte.fdAddress
                    if _debug: BIPBBMD._debug("    - sending to foreign device: %r", xpdu.pduDestination)
                    self.request(xpdu)

        elif isinstance(pdu, OriginalUnicastNPDU):
            # send it upstream if there is a network layer
            if self.serverPeer:
                # build a PDU with a local broadcast address
                xpdu = PDU(pdu.pduData, source=pdu.pduSource, destination=pdu.pduDestination, user_data=pdu.pduUserData)
                if _debug: BIPBBMD._debug("    - upstream xpdu: %r", xpdu)

                self.response(xpdu)

        elif isinstance(pdu, OriginalBroadcastNPDU):
            # send it upstream if there is a network layer
            if self.serverPeer:
                # build a PDU with a local broadcast address
                xpdu = PDU(pdu.pduData, source=pdu.pduSource, destination=LocalBroadcast(), user_data=pdu.pduUserData)
                if _debug: BIPBBMD._debug("    - upstream xpdu: %r", xpdu)

                self.response(xpdu)

            # make a forwarded PDU
            xpdu = ForwardedNPDU(pdu.pduSource, pdu, user_data=pdu.pduUserData)
            if _debug: BIPBBMD._debug("    - forwarded xpdu: %r", xpdu)

            # send it to the peers
            for bdte in self.bbmdBDT:
                if bdte != self.bbmdAddress:
                    xpdu.pduDestination = Address( ((bdte.addrIP|~bdte.addrMask), bdte.addrPort) )
                    if _debug: BIPBBMD._debug("    - sending to peer: %r", xpdu.pduDestination)
                    self.request(xpdu)

            # send it to the registered foreign devices
            for fdte in self.bbmdFDT:
                xpdu.pduDestination = fdte.fdAddress
                if _debug: BIPBBMD._debug("    - sending to foreign device: %r", xpdu.pduDestination)
                self.request(xpdu)

        else:
            BIPBBMD._warning("invalid pdu type: %s", type(pdu))

    def register_foreign_device(self, addr, ttl):
        """Add a foreign device to the FDT."""
        if _debug: BIPBBMD._debug("register_foreign_device %r %r", addr, ttl)

        # see if it is an address or make it one
        if isinstance(addr, Address):
            pass
        elif isinstance(addr, str):
            addr = Address(addr)
        else:
            raise TypeError("addr must be a string or an Address")

        for fdte in self.bbmdFDT:
            if addr == fdte.fdAddress:
                break
        else:
            fdte = FDTEntry()
            fdte.fdAddress = addr
            self.bbmdFDT.append( fdte )

        fdte.fdTTL = ttl
        fdte.fdRemain = ttl + 5

        # return success
        return 0

    def delete_foreign_device_table_entry(self, addr):
        if _debug: BIPBBMD._debug("delete_foreign_device_table_entry %r", addr)

        # see if it is an address or make it one
        if isinstance(addr, Address):
            pass
        elif isinstance(addr, str):
            addr = Address(addr)
        else:
            raise TypeError("addr must be a string or an Address")

        # find it and delete it
        stat = 0
        for i in range(len(self.bbmdFDT)-1, -1, -1):
            if addr == self.bbmdFDT[i].fdAddress:
                del self.bbmdFDT[i]
                break
        else:
            stat = 0x0050 ### entry not found

        # return status
        return stat

    def process_task(self):
        # look for foreign device registrations that have expired
        for i in range(len(self.bbmdFDT)-1, -1, -1):
            fdte = self.bbmdFDT[i]
            fdte.fdRemain -= 1

            # delete it if it expired
            if fdte.fdRemain <= 0:
                if _debug: BIPBBMD._debug("foreign device expired: %r", fdte.fdAddress)
                del self.bbmdFDT[i]

    def add_peer(self, addr):
        if _debug: BIPBBMD._debug("add_peer %r", addr)

        # see if it is an address or make it one
        if isinstance(addr, Address):
            pass
        elif isinstance(addr, str):
            addr = Address(addr)
        else:
            raise TypeError("addr must be a string or an Address")

        # see if it's already there
        for bdte in self.bbmdBDT:
            if addr == bdte:
                break
        else:
            self.bbmdBDT.append(addr)

    def delete_peer(self, addr):
        if _debug: BIPBBMD._debug("delete_peer %r", addr)

        # see if it is an address or make it one
        if isinstance(addr, Address):
            pass
        elif isinstance(addr, str):
            addr = Address(addr)
        else:
            raise TypeError("addr must be a string or an Address")

        # look for the peer address
        for i in range(len(self.bbmdBDT)-1, -1, -1):
            if addr == self.bbmdBDT[i]:
                del self.bbmdBDT[i]
                break
        else:
            pass

#
#   BIPNAT
#

@bacpypes_debugging
class BIPNAT(BIPSAP, Client, Server, RecurringTask, DebugContents):

    _debug_contents = ('bbmdAddress', 'bbmdBDT+', 'bbmdFDT+')

    def __init__(self, addr, sapID=None, cid=None, sid=None):
        """A BBMD node that is the destination for NATed traffic."""
        if _debug: BIPNAT._debug("__init__ %r sapID=%r cid=%r sid=%r", addr, sapID, cid, sid)
        BIPSAP.__init__(self, sapID)
        Client.__init__(self, cid)
        Server.__init__(self, sid)
        RecurringTask.__init__(self, 1000.0)

        self.bbmdAddress = addr
        self.bbmdBDT = []
        self.bbmdFDT = []

        # install so process_task runs
        self.install_task()

    def indication(self, pdu):
        if _debug: BIPNAT._debug("indication %r", pdu)

        # check for local stations
        if pdu.pduDestination.addrType == Address.localStationAddr:
            ###TODO the destination should be a peer or a registered foreign device

            # make an original unicast PDU
            xpdu = OriginalUnicastNPDU(pdu, user_data=pdu.pduUserData)
            xpdu.pduDestination = pdu.pduDestination
            if _debug: BIPNAT._debug("    - xpdu: %r", xpdu)

            # send it downstream
            self.request(xpdu)

        # check for broadcasts
        elif pdu.pduDestination.addrType == Address.localBroadcastAddr:
            # make a forwarded PDU
            xpdu = ForwardedNPDU(self.bbmdAddress, pdu, user_data=pdu.pduUserData)
            if _debug: BIPNAT._debug("    - forwarded xpdu: %r", xpdu)

            # send it to the peers, all of them have all F's mask
            for bdte in self.bbmdBDT:
                if bdte != self.bbmdAddress:
                    xpdu.pduDestination = Address((bdte.addrIP, bdte.addrPort))
                    BIPNAT._debug("        - sending to peer: %r", xpdu.pduDestination)
                    self.request(xpdu)

            # send it to the registered foreign devices
            for fdte in self.bbmdFDT:
                xpdu.pduDestination = fdte.fdAddress
                if _debug: BIPNAT._debug("        - sending to foreign device: %r", xpdu.pduDestination)
                self.request(xpdu)

        else:
            BIPNAT._warning("invalid destination address: %r", pdu.pduDestination)

    def confirmation(self, pdu):
        if _debug: BIPNAT._debug("confirmation %r",  pdu)

        # some kind of response to a request
        if isinstance(pdu, Result):
            # send this to the service access point
            self.sap_response(pdu)

        elif isinstance(pdu, WriteBroadcastDistributionTable):
            ###TODO verify this is from a management network/address

            # build a response
            xpdu = Result(code=99, user_data=pdu.pduUserData)
            xpdu.pduDestination = pdu.pduSource

            # send it downstream
            self.request(xpdu)

        elif isinstance(pdu, ReadBroadcastDistributionTable):
            ###TODO verify this is from a management network/address

            # build a response
            xpdu = ReadBroadcastDistributionTableAck(self.bbmdBDT, user_data=pdu.pduUserData)
            xpdu.pduDestination = pdu.pduSource
            if _debug: BIPNAT._debug("    - xpdu: %r", xpdu)

            # send it downstream
            self.request(xpdu)

        elif isinstance(pdu, ReadBroadcastDistributionTableAck):
            # send this to the service access point
            self.sap_response(pdu)

        elif isinstance(pdu, ForwardedNPDU):
            ###TODO verify this is from a peer

            # build a PDU with the source from the real source
            xpdu = PDU(pdu.pduData, source=pdu.bvlciAddress, destination=LocalBroadcast(), user_data=pdu.pduUserData)
            if _debug: BIPNAT._debug("    - upstream xpdu: %r", xpdu)

            # send it upstream
            self.response(xpdu)

            # build a forwarded NPDU to send out
            xpdu = ForwardedNPDU(pdu.bvlciAddress, pdu, destination=None, user_data=pdu.pduUserData)
            if _debug: BIPNAT._debug("    - forwarded xpdu: %r", xpdu)

            # send it to the registered foreign devices
            for fdte in self.bbmdFDT:
                xpdu.pduDestination = fdte.fdAddress
                if _debug: BIPNAT._debug("        - sending to foreign device: %r", xpdu.pduDestination)
                self.request(xpdu)

        elif isinstance(pdu, RegisterForeignDevice):
            ###TODO verify this is from an acceptable address

            # process the request
            stat = self.register_foreign_device(pdu.pduSource, pdu.bvlciTimeToLive)

            # build a response
            xpdu = Result(code=stat, destination=pdu.pduSource, user_data=pdu.pduUserData)
            if _debug: BIPNAT._debug("    - xpdu: %r", xpdu)

            # send it downstream
            self.request(xpdu)

        elif isinstance(pdu, ReadForeignDeviceTable):
            ###TODO verify this is from a management network/address

            # build a response
            xpdu = ReadForeignDeviceTableAck(self.bbmdFDT, destination=pdu.pduSource, user_data=pdu.pduUserData)
            if _debug: BIPNAT._debug("    - xpdu: %r", xpdu)

            # send it downstream
            self.request(xpdu)

        elif isinstance(pdu, ReadForeignDeviceTableAck):
            # send this to the service access point
            self.sap_response(pdu)

        elif isinstance(pdu, DeleteForeignDeviceTableEntry):
            ###TODO verify this is from a management network/address

            # process the request
            stat = self.delete_foreign_device_table_entry(pdu.bvlciAddress)

            # build a response
            xpdu = Result(code=stat, user_data=pdu.pduUserData)
            xpdu.pduDestination = pdu.pduSource
            if _debug: BIPNAT._debug("    - xpdu: %r", xpdu)

            # send it downstream
            self.request(xpdu)

        elif isinstance(pdu, DistributeBroadcastToNetwork):
            ###TODO verify this is from a registered foreign device

            # build a PDU with a local broadcast address
            xpdu = PDU(pdu.pduData, source=pdu.pduSource, destination=LocalBroadcast(), user_data=pdu.pduUserData)
            if _debug: BIPNAT._debug("    - upstream xpdu: %r", xpdu)

            # send it upstream
            self.response(xpdu)

            # build a forwarded NPDU to send out
            xpdu = ForwardedNPDU(pdu.pduSource, pdu, user_data=pdu.pduUserData)
            if _debug: BIPNAT._debug("    - forwarded xpdu: %r", xpdu)

            # send it to the peers
            for bdte in self.bbmdBDT:
                if bdte == self.bbmdAddress:
                    if _debug: BIPNAT._debug("        - no local broadcast")
                else:
                    xpdu.pduDestination = Address((bdte.addrIP, bdte.addrPort))
                    if _debug: BIPNAT._debug("        - sending to peer: %r", xpdu.pduDestination)
                    self.request(xpdu)

            # send it to the other registered foreign devices
            for fdte in self.bbmdFDT:
                if fdte.fdAddress != pdu.pduSource:
                    xpdu.pduDestination = fdte.fdAddress
                    if _debug: BIPNAT._debug("        - sending to foreign device: %r", xpdu.pduDestination)
                    self.request(xpdu)

        elif isinstance(pdu, OriginalUnicastNPDU):
            ###TODO verify this is from a peer

            # build a vanilla PDU
            xpdu = PDU(pdu.pduData, source=pdu.pduSource, destination=pdu.pduDestination, user_data=pdu.pduUserData)
            if _debug: BIPNAT._debug("    - upstream xpdu: %r", xpdu)

            # send it upstream
            self.response(xpdu)

        elif isinstance(pdu, OriginalBroadcastNPDU):
            if _debug: BIPNAT._debug("    - original broadcast dropped")

        else:
            BIPNAT._warning("invalid pdu type: %s", type(pdu))

    def register_foreign_device(self, addr, ttl):
        """Add a foreign device to the FDT."""
        if _debug: BIPNAT._debug("register_foreign_device %r %r", addr, ttl)

        # see if it is an address or make it one
        if isinstance(addr, Address):
            pass
        elif isinstance(addr, str):
            addr = Address(addr)
        else:
            raise TypeError("addr must be a string or an Address")

        for fdte in self.bbmdFDT:
            if addr == fdte.fdAddress:
                break
        else:
            fdte = FDTEntry()
            fdte.fdAddress = addr
            self.bbmdFDT.append( fdte )

        fdte.fdTTL = ttl
        fdte.fdRemain = ttl + 5

        # return success
        return 0

    def delete_foreign_device_table_entry(self, addr):
        if _debug: BIPNAT._debug("delete_foreign_device_table_entry %r", addr)

        # see if it is an address or make it one
        if isinstance(addr, Address):
            pass
        elif isinstance(addr, str):
            addr = Address(addr)
        else:
            raise TypeError("addr must be a string or an Address")

        # find it and delete it
        stat = 0
        for i in range(len(self.bbmdFDT)-1, -1, -1):
            if addr == self.bbmdFDT[i].fdAddress:
                del self.bbmdFDT[i]
                break
        else:
            stat = 99 ### entry not found

        # return status
        return stat

    def process_task(self):
        # look for foreign device registrations that have expired
        for i in range(len(self.bbmdFDT)-1, -1, -1):
            fdte = self.bbmdFDT[i]
            fdte.fdRemain -= 1

            # delete it if it expired
            if fdte.fdRemain <= 0:
                if _debug: BIPNAT._debug("foreign device expired: %r", fdte.fdAddress)
                del self.bbmdFDT[i]

    def add_peer(self, addr):
        if _debug: BIPNAT._debug("add_peer %r", addr)

        # see if it is an address or make it one
        if isinstance(addr, Address):
            pass
        elif isinstance(addr, str):
            addr = Address(addr)
        else:
            raise TypeError("addr must be a string or an Address")

        # if it's this BBMD, make it the first one
        if self.bbmdBDT and (addr == self.bbmdAddress):
            raise RuntimeError("add self to BDT as first address")

        # see if it's already there
        for bdte in self.bbmdBDT:
            if addr == bdte:
                break
        else:
            self.bbmdBDT.append(addr)

    def delete_peer(self, addr):
        if _debug: BIPNAT._debug("delete_peer %r", addr)

        # see if it is an address or make it one
        if isinstance(addr, Address):
            pass
        elif isinstance(addr, str):
            addr = Address(addr)
        else:
            raise TypeError("addr must be a string or an Address")

        # look for the peer address
        for i in range(len(self.bbmdBDT)-1, -1, -1):
            if addr == self.bbmdBDT[i]:
                del self.bbmdBDT[i]
                break
        else:
            pass

#
#   BVLLServiceElement
#

@bacpypes_debugging
class BVLLServiceElement(ApplicationServiceElement):

    def __init__(self, aseID=None):
        if _debug: BVLLServiceElement._debug("__init__ aseID=%r", aseID)
        ApplicationServiceElement.__init__(self, aseID)

    def indication(self, npdu):
        if _debug: BVLLServiceElement._debug("indication %r %r", npdu)

        # redirect
        fn = npdu.__class__.__name__
        if hasattr(self, fn):
            getattr(self, fn)(npdu)
        else:
            BVLLServiceElement._warning("no handler for %s", fn)

    def confirmation(self, npdu):
        if _debug: BVLLServiceElement._debug("confirmation %r %r", npdu)

        # redirect
        fn = npdu.__class__.__name__
        if hasattr(self, fn):
            getattr(self, fn)(npdu)
        else:
            BVLLServiceElement._warning("no handler for %s", fn)

