#!/usr/bin/python

"""
Network Service
"""

from copy import copy as _copy

from .debugging import ModuleLogger, DebugContents, bacpypes_debugging
from .errors import ConfigurationError

from .comm import Client, Server, bind, \
    ServiceAccessPoint, ApplicationServiceElement

from .pdu import Address, LocalBroadcast, LocalStation, PDU, RemoteStation
from .npdu import IAmRouterToNetwork, NPDU, WhoIsRouterToNetwork, npdu_types
from .apdu import APDU as _APDU

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# router status values
ROUTER_AVAILABLE = 0            # normal
ROUTER_BUSY = 1                 # router is busy
ROUTER_DISCONNECTED = 2         # could make a connection, but hasn't
ROUTER_UNREACHABLE = 3          # cannot route

#
#   NetworkReference
#

class NetworkReference:
    """These objects map a network to a router."""

    def __init__(self, net, router, status):
        self.network = net
        self.router = router
        self.status = status

#
#   RouterReference
#

class RouterReference(DebugContents):
    """These objects map a router; the adapter to talk to it,
    its address, and a list of networks that it routes to."""

    _debug_contents = ('adapter-', 'address', 'networks', 'status')

    def __init__(self, adapter, addr, nets, status):
        self.adapter = adapter
        self.address = addr     # local station relative to the adapter
        self.networks = nets    # list of remote networks
        self.status = status    # status as presented by the router

#
#   NetworkAdapter
#

@bacpypes_debugging
class NetworkAdapter(Client, DebugContents):

    _debug_contents = ('adapterSAP-', 'adapterNet')

    def __init__(self, sap, net, cid=None):
        if _debug: NetworkAdapter._debug("__init__ %r (net=%r) cid=%r", sap, net, cid)
        Client.__init__(self, cid)
        self.adapterSAP = sap
        self.adapterNet = net

        # add this to the list of adapters for the network
        sap.adapters.append(self)

    def confirmation(self, pdu):
        """Decode upstream PDUs and pass them up to the service access point."""
        if _debug: NetworkAdapter._debug("confirmation %r (net=%r)", pdu, self.adapterNet)

        npdu = NPDU(user_data=pdu.pduUserData)
        npdu.decode(pdu)
        self.adapterSAP.process_npdu(self, npdu)

    def process_npdu(self, npdu):
        """Encode NPDUs from the service access point and send them downstream."""
        if _debug: NetworkAdapter._debug("process_npdu %r (net=%r)", npdu, self.adapterNet)

        pdu = PDU(user_data=npdu.pduUserData)
        npdu.encode(pdu)
        self.request(pdu)

    def EstablishConnectionToNetwork(self, net):
        pass

    def DisconnectConnectionToNetwork(self, net):
        pass

#
#   NetworkServiceAccessPoint
#

@bacpypes_debugging
class NetworkServiceAccessPoint(ServiceAccessPoint, Server, DebugContents):

    _debug_contents = ('adapters++', 'routers++', 'networks+'
        , 'localAdapter-', 'localAddress'
        )

    def __init__(self, sap=None, sid=None):
        if _debug: NetworkServiceAccessPoint._debug("__init__ sap=%r sid=%r", sap, sid)
        ServiceAccessPoint.__init__(self, sap)
        Server.__init__(self, sid)

        self.adapters = []          # list of adapters
        self.routers = {}           # (adapter, address) -> RouterReference
        self.networks = {}          # network -> RouterReference

        self.localAdapter = None    # which one is local
        self.localAddress = None    # what is the local address

    def bind(self, server, net=None, address=None):
        """Create a network adapter object and bind."""
        if _debug: NetworkServiceAccessPoint._debug("bind %r net=%r address=%r", server, net, address)

        if (net is None) and self.adapters:
            raise RuntimeError("already bound")

        # create an adapter object
        adapter = NetworkAdapter(self, net)

        # if the address was given, make it the "local" one
        if address:
            self.localAdapter = adapter
            self.localAddress = address

        # bind to the server
        bind(adapter, server)

    #-----

    def add_router_references(self, adapter, address, netlist):
        """Add/update references to routers."""
        if _debug: NetworkServiceAccessPoint._debug("add_router_references %r %r %r", adapter, address, netlist)

        # make a key for the router reference
        rkey = (adapter, address)

        for snet in netlist:
            # see if this is spoofing an existing routing table entry
            if snet in self.networks:
                rref = self.networks[snet]

                if rref.adapter == adapter and rref.address == address:
                    pass        # matches current entry
                else:
                    ### check to see if this source could be a router to the new network

                    # remove the network from the rref
                    i = rref.networks.index(snet)
                    del rref.networks[i]

                    # remove the network
                    del self.networks[snet]

            ### check to see if it is OK to add the new entry

            # get the router reference for this router
            rref = self.routers.get(rkey, None)
            if rref:
                if snet not in rref.networks:
                    # add the network
                    rref.networks.append(snet)

                    # reference the snet
                    self.networks[snet] = rref
            else:
                # new reference
                rref = RouterReference( adapter, address, [snet], 0)
                self.routers[rkey] = rref

                # reference the snet
                self.networks[snet] = rref

    def remove_router_references(self, adapter, address=None):
        """Add/update references to routers."""
        if _debug: NetworkServiceAccessPoint._debug("remove_router_references %r %r", adapter, address)

        delrlist = []
        delnlist = []
        # scan through the dictionary of router references
        for rkey in self.routers.keys():
            # rip apart the key
            radapter, raddress = rkey

            # pick all references on the adapter, optionally limited to a specific address
            match = radapter is adapter
            if match and address is not None:
                match = (raddress == address)
            if not match:
                continue

            # save it for deletion
            delrlist.append(rkey)
            delnlist.extend(self.routers[rkey].networks)
        if _debug:
            NetworkServiceAccessPoint._debug("    - delrlist: %r", delrlist)
            NetworkServiceAccessPoint._debug("    - delnlist: %r", delnlist)

        # delete the entries
        for rkey in delrlist:
            try:
                del self.routers[rkey]
            except KeyError:
                if _debug: NetworkServiceAccessPoint._debug("    - rkey not in self.routers: %r", rkey)
        for nkey in delnlist:
            try:
                del self.networks[nkey]
            except KeyError:
                if _debug: NetworkServiceAccessPoint._debug("    - nkey not in self.networks: %r", rkey)

    #-----

    def indication(self, pdu):
        if _debug: NetworkServiceAccessPoint._debug("indication %r", pdu)

        # make sure our configuration is OK
        if (not self.adapters):
            raise ConfigurationError("no adapters")

        # might be able to relax this restriction
        if (len(self.adapters) > 1) and (not self.localAdapter):
            raise ConfigurationError("local adapter must be set")

        # get the local adapter
        adapter = self.localAdapter or self.adapters[0]

        # build a generic APDU
        apdu = _APDU(user_data=pdu.pduUserData)
        pdu.encode(apdu)
        if _debug: NetworkServiceAccessPoint._debug("    - apdu: %r", apdu)

        # build an NPDU specific to where it is going
        npdu = NPDU(user_data=pdu.pduUserData)
        apdu.encode(npdu)
        if _debug: NetworkServiceAccessPoint._debug("    - npdu: %r", npdu)

        # the hop count always starts out big
        npdu.npduHopCount = 255

        # local stations given to local adapter
        if (npdu.pduDestination.addrType == Address.localStationAddr):
            adapter.process_npdu(npdu)
            return

        # local broadcast given to local adapter
        if (npdu.pduDestination.addrType == Address.localBroadcastAddr):
            adapter.process_npdu(npdu)
            return

        # global broadcast
        if (npdu.pduDestination.addrType == Address.globalBroadcastAddr):
            # set the destination
            npdu.pduDestination = LocalBroadcast()
            npdu.npduDADR = apdu.pduDestination

            # send it to all of connected adapters
            for xadapter in self.adapters:
                xadapter.process_npdu(npdu)
            return

        # remote broadcast
        if (npdu.pduDestination.addrType != Address.remoteBroadcastAddr) and (npdu.pduDestination.addrType != Address.remoteStationAddr):
            raise RuntimeError("invalid destination address type: %s" % (npdu.pduDestination.addrType,))

        dnet = npdu.pduDestination.addrNet

        # if the network matches the local adapter it's local
        if (dnet == adapter.adapterNet):
            ### log this, the application shouldn't be sending to a remote station address
            ### when it's a directly connected network
            raise RuntimeError("addressing problem")

        # check for an available path
        if dnet in self.networks:
            rref = self.networks[dnet]
            adapter = rref.adapter

            ### make sure the direct connect is OK, may need to connect

            ### make sure the peer router is OK, may need to connect

            # fix the destination
            npdu.pduDestination = rref.address
            npdu.npduDADR = apdu.pduDestination

            # send it along
            adapter.process_npdu(npdu)
            return

        if _debug: NetworkServiceAccessPoint._debug("    - no known path to network, broadcast to discover it")

        # set the destination
        npdu.pduDestination = LocalBroadcast()
        npdu.npduDADR = apdu.pduDestination

        # send it to all of the connected adapters
        for xadapter in self.adapters:
            xadapter.process_npdu(npdu)

    def process_npdu(self, adapter, npdu):
        if _debug: NetworkServiceAccessPoint._debug("process_npdu %r %r", adapter, npdu)

        # make sure our configuration is OK
        if (not self.adapters):
            raise ConfigurationError("no adapters")
        if (len(self.adapters) > 1) and (not self.localAdapter):
            raise ConfigurationError("local adapter must be set")

        # check for source routing
        if npdu.npduSADR and (npdu.npduSADR.addrType != Address.nullAddr):
            # see if this is attempting to spoof a directly connected network
            snet = npdu.npduSADR.addrNet
            for xadapter in self.adapters:
                if (xadapter is not adapter) and (snet == xadapter.adapterNet):
                    NetworkServiceAccessPoint._warning("spoof?")
                    ### log this
                    return

            # make a key for the router reference
            rkey = (adapter, npdu.pduSource)

            # see if this is spoofing an existing routing table entry
            if snet in self.networks:
                rref = self.networks[snet]
                if rref.adapter == adapter and rref.address == npdu.pduSource:
                    pass        # matches current entry
                else:
                    if _debug: NetworkServiceAccessPoint._debug("    - replaces entry")

                    ### check to see if this source could be a router to the new network

                    # remove the network from the rref
                    i = rref.networks.index(snet)
                    del rref.networks[i]

                    # remove the network
                    del self.networks[snet]

            # get the router reference for this router
            rref = self.routers.get(rkey)
            if rref:
                if snet not in rref.networks:
                    # add the network
                    rref.networks.append(snet)

                    # reference the snet
                    self.networks[snet] = rref
            else:
                # new reference
                rref = RouterReference( adapter, npdu.pduSource, [snet], 0)
                self.routers[rkey] = rref

                # reference the snet
                self.networks[snet] = rref

        # check for destination routing
        if (not npdu.npduDADR) or (npdu.npduDADR.addrType == Address.nullAddr):
            processLocally = (not self.localAdapter) or (adapter is self.localAdapter) or (npdu.npduNetMessage is not None)
            forwardMessage = False

        elif npdu.npduDADR.addrType == Address.remoteBroadcastAddr:
            if not self.localAdapter:
                return
            if (npdu.npduDADR.addrNet == adapter.adapterNet):
                ### log this, attempt to route to a network the device is already on
                return

            processLocally = (npdu.npduDADR.addrNet == self.localAdapter.adapterNet)
            forwardMessage = True

        elif npdu.npduDADR.addrType == Address.remoteStationAddr:
            if not self.localAdapter:
                return
            if (npdu.npduDADR.addrNet == adapter.adapterNet):
                ### log this, attempt to route to a network the device is already on
                return

            processLocally = (npdu.npduDADR.addrNet == self.localAdapter.adapterNet) \
                and (npdu.npduDADR.addrAddr == self.localAddress.addrAddr)
            forwardMessage = not processLocally

        elif npdu.npduDADR.addrType == Address.globalBroadcastAddr:
            processLocally = True
            forwardMessage = True

        else:
            NetworkServiceAccessPoint._warning("invalid destination address type: %s", npdu.npduDADR.addrType)
            return

        if _debug:
            NetworkServiceAccessPoint._debug("    - processLocally: %r", processLocally)
            NetworkServiceAccessPoint._debug("    - forwardMessage: %r", forwardMessage)

        # application or network layer message
        if npdu.npduNetMessage is None:
            if processLocally and self.serverPeer:
                # decode as a generic APDU
                apdu = _APDU(user_data=npdu.pduUserData)
                apdu.decode(_copy(npdu))
                if _debug: NetworkServiceAccessPoint._debug("    - apdu: %r", apdu)

                # see if it needs to look routed
                if (len(self.adapters) > 1) and (adapter != self.localAdapter):
                    # combine the source address
                    if not npdu.npduSADR:
                        apdu.pduSource = RemoteStation( adapter.adapterNet, npdu.pduSource.addrAddr )
                    else:
                        apdu.pduSource = npdu.npduSADR

                    # map the destination
                    if not npdu.npduDADR:
                        apdu.pduDestination = self.localAddress
                    elif npdu.npduDADR.addrType == Address.globalBroadcastAddr:
                        apdu.pduDestination = npdu.npduDADR
                    elif npdu.npduDADR.addrType == Address.remoteBroadcastAddr:
                        apdu.pduDestination = LocalBroadcast()
                    else:
                        apdu.pduDestination = self.localAddress
                else:
                    # combine the source address
                    if npdu.npduSADR:
                        apdu.pduSource = npdu.npduSADR
                    else:
                        apdu.pduSource = npdu.pduSource

                    # pass along global broadcast
                    if npdu.npduDADR and npdu.npduDADR.addrType == Address.globalBroadcastAddr:
                        apdu.pduDestination = npdu.npduDADR
                    else:
                        apdu.pduDestination = npdu.pduDestination
                if _debug:
                    NetworkServiceAccessPoint._debug("    - apdu.pduSource: %r", apdu.pduSource)
                    NetworkServiceAccessPoint._debug("    - apdu.pduDestination: %r", apdu.pduDestination)

                # pass upstream to the application layer
                self.response(apdu)

            if not forwardMessage:
                return
        else:
            if processLocally:
                if npdu.npduNetMessage not in npdu_types:
                    if _debug: NetworkServiceAccessPoint._debug("    - unknown npdu type: %r", npdu.npduNetMessage)
                    return

                # do a deeper decode of the NPDU
                xpdu = npdu_types[npdu.npduNetMessage](user_data=npdu.pduUserData)
                xpdu.decode(_copy(npdu))

                # pass to the service element
                self.sap_request(adapter, xpdu)

            if not forwardMessage:
                return

        # make sure we're really a router
        if (len(self.adapters) == 1):
            return

        # make sure it hasn't looped
        if (npdu.npduHopCount == 0):
            return

        # build a new NPDU to send to other adapters
        newpdu = _copy(npdu)

        # clear out the source and destination
        newpdu.pduSource = None
        newpdu.pduDestination = None

        # decrease the hop count
        newpdu.npduHopCount -= 1

        # set the source address
        if not npdu.npduSADR:
            newpdu.npduSADR = RemoteStation( adapter.adapterNet, npdu.pduSource.addrAddr )
        else:
            newpdu.npduSADR = npdu.npduSADR

        # if this is a broadcast it goes everywhere
        if npdu.npduDADR.addrType == Address.globalBroadcastAddr:
            newpdu.pduDestination = LocalBroadcast()

            for xadapter in self.adapters:
                if (xadapter is not adapter):
                    xadapter.process_npdu(newpdu)
            return

        if (npdu.npduDADR.addrType == Address.remoteBroadcastAddr) \
                or (npdu.npduDADR.addrType == Address.remoteStationAddr):
            dnet = npdu.npduDADR.addrNet

            # see if this should go to one of our directly connected adapters
            for xadapter in self.adapters:
                if dnet == xadapter.adapterNet:
                    if _debug: NetworkServiceAccessPoint._debug("    - found direct connect via %r", xadapter)
                    if (npdu.npduDADR.addrType == Address.remoteBroadcastAddr):
                        newpdu.pduDestination = LocalBroadcast()
                    else:
                        newpdu.pduDestination = LocalStation(npdu.npduDADR.addrAddr)

                    # last leg in routing
                    newpdu.npduDADR = None

                    # send the packet downstream
                    xadapter.process_npdu(newpdu)
                    return

            # see if we know how to get there
            if dnet in self.networks:
                rref = self.networks[dnet]
                newpdu.pduDestination = rref.address

                ### check to make sure the router is OK

                ### check to make sure the network is OK, may need to connect

                if _debug: NetworkServiceAccessPoint._debug("    - newpdu: %r", newpdu)

                # send the packet downstream
                rref.adapter.process_npdu(newpdu)
                return

            ### queue this message for reprocessing when the response comes back

            # try to find a path to the network
            xnpdu = WhoIsRouterToNetwork(dnet)
            xnpdu.pduDestination = LocalBroadcast()

            # send it to all of the connected adapters
            for xadapter in self.adapters:
                # skip the horse it rode in on
                if (xadapter is adapter):
                    continue

                ### make sure the adapter is OK
                self.sap_indication(xadapter, xnpdu)

        ### log this, what to do?
        return

    def sap_indication(self, adapter, npdu):
        if _debug: NetworkServiceAccessPoint._debug("sap_indication %r %r", adapter, npdu)

        # encode it as a generic NPDU
        xpdu = NPDU(user_data=npdu.pduUserData)
        npdu.encode(xpdu)
        npdu._xpdu = xpdu

        # tell the adapter to process the NPDU
        adapter.process_npdu(xpdu)

    def sap_confirmation(self, adapter, npdu):
        if _debug: NetworkServiceAccessPoint._debug("sap_confirmation %r %r", adapter, npdu)

        # encode it as a generic NPDU
        xpdu = NPDU(user_data=npdu.pduUserData)
        npdu.encode(xpdu)
        npdu._xpdu = xpdu

        # tell the adapter to process the NPDU
        adapter.process_npdu(xpdu)

#
#   NetworkServiceElement
#

@bacpypes_debugging
class NetworkServiceElement(ApplicationServiceElement):

    def __init__(self, eid=None):
        if _debug: NetworkServiceElement._debug("__init__ eid=%r", eid)
        ApplicationServiceElement.__init__(self, eid)

    def indication(self, adapter, npdu):
        if _debug: NetworkServiceElement._debug("indication %r %r", adapter, npdu)

        # redirect
        fn = npdu.__class__.__name__
        if hasattr(self, fn):
            getattr(self, fn)(adapter, npdu)

    def confirmation(self, adapter, npdu):
        if _debug: NetworkServiceElement._debug("confirmation %r %r", adapter, npdu)

        # redirect
        fn = npdu.__class__.__name__
        if hasattr(self, fn):
            getattr(self, fn)(adapter, npdu)

    #-----

    def WhoIsRouterToNetwork(self, adapter, npdu):
        if _debug: NetworkServiceElement._debug("WhoIsRouterToNetwork %r %r", adapter, npdu)

        # reference the service access point
        sap = self.elementService
        if _debug: NetworkServiceElement._debug("    - sap: %r", sap)

        # if we're not a router, skip it
        if len(sap.adapters) == 1:
            if _debug: NetworkServiceElement._debug("    - not a router")
            return

        if npdu.wirtnNetwork is None:
            # requesting all networks
            if _debug: NetworkServiceElement._debug("    - requesting all networks")

            # build a list of reachable networks
            netlist = []

            # start with directly connected networks
            for xadapter in sap.adapters:
                if (xadapter is not adapter):
                    netlist.append(xadapter.adapterNet)

            # build a list of other available networks
            for net, rref in sap.networks.items():
                if rref.adapter is not adapter:
                    ### skip those marked unreachable
                    ### skip those that are not available
                    netlist.append(net)

            if netlist:
                if _debug: NetworkServiceElement._debug("    - found these: %r", netlist)

                # build a response
                iamrtn = IAmRouterToNetwork(netlist, user_data=npdu.pduUserData)
                iamrtn.pduDestination = npdu.pduSource

                # send it back
                self.response(adapter, iamrtn)

        else:
            # requesting a specific network
            if _debug: NetworkServiceElement._debug("    - requesting specific network: %r", npdu.wirtnNetwork)

            # start with directly connected networks
            for xadapter in sap.adapters:
                if (xadapter is not adapter) and (npdu.wirtnNetwork == xadapter.adapterNet):
                    if _debug: NetworkServiceElement._debug("    - found it directly connected")

                    # build a response
                    iamrtn = IAmRouterToNetwork([npdu.wirtnNetwork], user_data=npdu.pduUserData)
                    iamrtn.pduDestination = npdu.pduSource

                    # send it back
                    self.response(adapter, iamrtn)

                    break
            else:
                # check for networks I know about
                if npdu.wirtnNetwork in sap.networks:
                    rref = sap.networks[npdu.wirtnNetwork]
                    if rref.adapter is adapter:
                        if _debug: NetworkServiceElement._debug("    - same net as request")

                    else:
                        if _debug: NetworkServiceElement._debug("    - found on adapter: %r", rref.adapter)

                        # build a response
                        iamrtn = IAmRouterToNetwork([npdu.wirtnNetwork], user_data=npdu.pduUserData)
                        iamrtn.pduDestination = npdu.pduSource

                        # send it back
                        self.response(adapter, iamrtn)

                else:
                    if _debug: NetworkServiceElement._debug("    - forwarding request to other adapters")

                    # build a request
                    whoisrtn = WhoIsRouterToNetwork(npdu.wirtnNetwork, user_data=npdu.pduUserData)
                    whoisrtn.pduDestination = LocalBroadcast()

                    # if the request had a source, forward it along
                    if npdu.npduSADR:
                        whoisrtn.npduSADR = npdu.npduSADR
                    else:
                        whoisrtn.npduSADR = RemoteStation(adapter.adapterNet, npdu.pduSource.addrAddr)
                    if _debug: NetworkServiceElement._debug("    - whoisrtn: %r", whoisrtn)

                    # send it to all of the (other) adapters
                    for xadapter in sap.adapters:
                        if xadapter is not adapter:
                            if _debug: NetworkServiceElement._debug("    - sending on adapter: %r", xadapter)
                            self.request(xadapter, whoisrtn)

    def IAmRouterToNetwork(self, adapter, npdu):
        if _debug: NetworkServiceElement._debug("IAmRouterToNetwork %r %r", adapter, npdu)

        # pass along to the service access point
        self.elementService.add_router_references(adapter, npdu.pduSource, npdu.iartnNetworkList)

    def ICouldBeRouterToNetwork(self, adapter, npdu):
        if _debug: NetworkServiceElement._debug("ICouldBeRouterToNetwork %r %r", adapter, npdu)

        # reference the service access point
        # sap = self.elementService

    def RejectMessageToNetwork(self, adapter, npdu):
        if _debug: NetworkServiceElement._debug("RejectMessageToNetwork %r %r", adapter, npdu)

        # reference the service access point
        # sap = self.elementService

    def RouterBusyToNetwork(self, adapter, npdu):
        if _debug: NetworkServiceElement._debug("RouterBusyToNetwork %r %r", adapter, npdu)

        # reference the service access point
        # sap = self.elementService

    def RouterAvailableToNetwork(self, adapter, npdu):
        if _debug: NetworkServiceElement._debug("RouterAvailableToNetwork %r %r", adapter, npdu)

        # reference the service access point
        # sap = self.elementService

    def InitializeRoutingTable(self, adapter, npdu):
        if _debug: NetworkServiceElement._debug("InitializeRoutingTable %r %r", adapter, npdu)

        # reference the service access point
        # sap = self.elementService

    def InitializeRoutingTableAck(self, adapter, npdu):
        if _debug: NetworkServiceElement._debug("InitializeRoutingTableAck %r %r", adapter, npdu)

        # reference the service access point
        # sap = self.elementService

    def EstablishConnectionToNetwork(self, adapter, npdu):
        if _debug: NetworkServiceElement._debug("EstablishConnectionToNetwork %r %r", adapter, npdu)

        # reference the service access point
        # sap = self.elementService

    def DisconnectConnectionToNetwork(self, adapter, npdu):
        if _debug: NetworkServiceElement._debug("DisconnectConnectionToNetwork %r %r", adapter, npdu)

        # reference the service access point
        # sap = self.elementService

