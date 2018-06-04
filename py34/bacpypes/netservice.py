#!/usr/bin/python

"""
Network Service
"""

from copy import deepcopy as _deepcopy

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
#   RouterInfo
#

class RouterInfo(DebugContents):
    """These objects are routing information records that map router
    addresses with destination networks."""

    _debug_contents = ('snet', 'address', 'dnets', 'status')

    def __init__(self, snet, address, dnets, status=ROUTER_AVAILABLE):
        self.snet = snet        # source network
        self.address = address  # address of the router
        self.dnets = dnets      # list of reachable networks through this router
        self.status = status    # router status

#
#   RouterInfoCache
#

@bacpypes_debugging
class RouterInfoCache:

    def __init__(self):
        if _debug: RouterInfoCache._debug("__init__")

        self.routers = {}           # (snet, address) -> RouterInfo
        self.networks = {}          # network -> RouterInfo

    def get_router_info(self, dnet):
        if _debug: RouterInfoCache._debug("get_router_info %r", dnet)

        # check to see if we know about it
        if dnet not in self.networks:
            if _debug: RouterInfoCache._debug("   - no route")
            return None

        # return the network and address
        router_info = self.networks[dnet]
        if _debug: RouterInfoCache._debug("   - router_info: %r", router_info)

        # return the network, address, and status
        return (router_info.snet, router_info.address, router_info.status)

    def update_router_info(self, snet, address, dnets):
        if _debug: RouterInfoCache._debug("update_router_info %r %r %r", snet, address, dnets)

        # look up the router reference, make a new record if necessary
        key = (snet, address)
        if key not in self.routers:
            if _debug: RouterInfoCache._debug("   - new router")
            router_info = self.routers[key] = RouterInfo(snet, address, list())
        else:
            router_info = self.routers[key]

        # add (or move) the destination networks
        for dnet in dnets:
            if dnet in self.networks:
                other_router = self.networks[dnet]
                if other_router is router_info:
                    if _debug: RouterInfoCache._debug("   - existing router, match")
                    continue
                elif dnet not in other_router.dnets:
                    if _debug: RouterInfoCache._debug("   - where did it go?")
                else:
                    other_router.dnets.remove(dnet)
                    if not other_router.dnets:
                        if _debug: RouterInfoCache._debug("    - no longer care about this router")
                        del self.routers[(snet, other_router.address)]

            # add a reference to the router
            self.networks[dnet] = router_info
            if _debug: RouterInfoCache._debug("   - reference added")

            # maybe update the list of networks for this router
            if dnet not in router_info.dnets:
                router_info.dnets.append(dnet)
                if _debug: RouterInfoCache._debug("   - dnet added, now: %r", router_info.dnets)

    def update_router_status(self, snet, address, status):
        if _debug: RouterInfoCache._debug("update_router_status %r %r %r", snet, address, status)

        key = (snet, address)
        if key not in self.routers:
            if _debug: RouterInfoCache._debug("   - not a router we care about")
            return

        router_info = self.routers[key]
        router_info.status = status
        if _debug: RouterInfoCache._debug("   - status updated")

    def delete_router_info(self, snet, address=None, dnets=None):
        if _debug: RouterInfoCache._debug("delete_router_info %r %r %r", dnets)

        # if address is None, remove all the routers for the network
        if address is None:
            for rnet, raddress in self.routers.keys():
                if snet == rnet:
                    if _debug: RouterInfoCache._debug("   - going down")
                    self.delete_router_info(snet, raddress)
            if _debug: RouterInfoCache._debug("   - back topside")
            return

        # look up the router reference
        key = (snet, address)
        if key not in self.routers:
            if _debug: RouterInfoCache._debug("   - unknown router")
            return

        router_info = self.routers[key]
        if _debug: RouterInfoCache._debug("   - router_info: %r", router_info)

        # if dnets is None, remove all the networks for the router
        if dnets is None:
            dnets = router_info.dnets

        # loop through the list of networks to be deleted
        for dnet in dnets:
            if dnet in self.networks:
                del self.networks[dnet]
                if _debug: RouterInfoCache._debug("   - removed from networks: %r", dnet)
            if dnet in router_info.dnets:
                router_info.dnets.remove(dnet)
                if _debug: RouterInfoCache._debug("   - removed from router_info: %r", dnet)

        # see if we still care
        if not router_info.dnets:
            if _debug: RouterInfoCache._debug("    - no longer care about this router")
            del self.routers[key]

#
#   NetworkAdapter
#

@bacpypes_debugging
class NetworkAdapter(Client, DebugContents):

    _debug_contents = ('adapterSAP-', 'adapterNet')

    def __init__(self, sap, net, cid=None):
        if _debug: NetworkAdapter._debug("__init__ %s %r cid=%r", sap, net, cid)
        Client.__init__(self, cid)
        self.adapterSAP = sap
        self.adapterNet = net

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

    def __init__(self, routerInfoCache=None, sap=None, sid=None):
        if _debug: NetworkServiceAccessPoint._debug("__init__ sap=%r sid=%r", sap, sid)
        ServiceAccessPoint.__init__(self, sap)
        Server.__init__(self, sid)

        # map of directly connected networks
        self.adapters = {}          # net -> NetworkAdapter

        # use the provided cache or make a default one
        self.router_info_cache = routerInfoCache or RouterInfoCache()

        # map to a list of application layer packets waiting for a path
        self.pending_nets = {}

        # these are set when bind() is called
        self.local_adapter = None
        self.local_address = None

    def bind(self, server, net=None, address=None):
        """Create a network adapter object and bind."""
        if _debug: NetworkServiceAccessPoint._debug("bind %r net=%r address=%r", server, net, address)

        # make sure this hasn't already been called with this network
        if net in self.adapters:
            raise RuntimeError("already bound")

        # when binding to an adapter and there is more than one, then they
        # must all have network numbers and one of them will be the default
        if (net is not None) and (None in self.adapters):
            raise RuntimeError("default adapter bound")

        # create an adapter object, add it to our map
        adapter = NetworkAdapter(self, net)
        self.adapters[net] = adapter
        if _debug: NetworkServiceAccessPoint._debug("    - adapters[%r]: %r", net, adapter)

        # if the address was given, make it the "local" one
        if address:
            self.local_adapter = adapter
            self.local_address = address

        # bind to the server
        bind(adapter, server)

    #-----

    def add_router_references(self, snet, address, dnets):
        """Add/update references to routers."""
        if _debug: NetworkServiceAccessPoint._debug("add_router_references %r %r %r", snet, address, dnets)

        # see if we have an adapter for the snet
        if snet not in self.adapters:
            raise RuntimeError("no adapter for network: %d" % (snet,))

        # pass this along to the cache
        self.router_info_cache.update_router_info(snet, address, dnets)

    def delete_router_references(self, snet, address=None, dnets=None):
        """Delete references to routers/networks."""
        if _debug: NetworkServiceAccessPoint._debug("delete_router_references %r %r %r", snet, address, dnets)

        # see if we have an adapter for the snet
        if snet not in self.adapters:
            raise RuntimeError("no adapter for network: %d" % (snet,))

        # pass this along to the cache
        self.router_info_cache.delete_router_info(snet, address, dnets)

    #-----

    def indication(self, pdu):
        if _debug: NetworkServiceAccessPoint._debug("indication %r", pdu)

        # make sure our configuration is OK
        if (not self.adapters):
            raise ConfigurationError("no adapters")

        # might be able to relax this restriction
        if (len(self.adapters) > 1) and (not self.local_adapter):
            raise ConfigurationError("local adapter must be set")

        # get the local adapter
        adapter = self.local_adapter or self.adapters[None]
        if _debug: NetworkServiceAccessPoint._debug("    - adapter: %r", adapter)

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
            for xadapter in self.adapters.values():
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

        # get it ready to send when the path is found
        npdu.pduDestination = None
        npdu.npduDADR = apdu.pduDestination

        # we might already be waiting for a path for this network
        if dnet in self.pending_nets:
            if _debug: NetworkServiceAccessPoint._debug("    - already waiting for path")
            self.pending_nets[dnet].append(npdu)
            return

        # check cache for an available path
        path_info = self.router_info_cache.get_router_info(dnet)

        # if there is info, we have a path
        if path_info:
            snet, address, status = path_info
            if _debug: NetworkServiceAccessPoint._debug("    - path found: %r, %r, %r", snet, address, status)

            # check for an adapter
            if snet not in self.adapters:
                raise RuntimeError("network found but not connected: %r", snet)
            adapter = self.adapters[snet]
            if _debug: NetworkServiceAccessPoint._debug("    - adapter: %r", adapter)

            # fix the destination
            npdu.pduDestination = address

            # send it along
            adapter.process_npdu(npdu)
            return

        if _debug: NetworkServiceAccessPoint._debug("    - no known path to network")

        # add it to the list of packets waiting for the network
        net_list = self.pending_nets.get(dnet, None)
        if net_list is None:
            net_list = self.pending_nets[dnet] = []
        net_list.append(npdu)

        # build a request for the network and send it to all of the adapters
        xnpdu = WhoIsRouterToNetwork(dnet)
        xnpdu.pduDestination = LocalBroadcast()

        # send it to all of the connected adapters
        for adapter in self.adapters.values():
            ### make sure the adapter is OK
            self.sap_indication(adapter, xnpdu)

    def process_npdu(self, adapter, npdu):
        if _debug: NetworkServiceAccessPoint._debug("process_npdu %r %r", adapter, npdu)

        # make sure our configuration is OK
        if (not self.adapters):
            raise ConfigurationError("no adapters")

        # check for source routing
        if npdu.npduSADR and (npdu.npduSADR.addrType != Address.nullAddr):
            if _debug: NetworkServiceAccessPoint._debug("    - check source path")

            # see if this is attempting to spoof a directly connected network
            snet = npdu.npduSADR.addrNet
            if snet in self.adapters:
                NetworkServiceAccessPoint._warning("    - path error (1)")
                return

            # see if there is routing information for this source network
            router_info = self.router_info_cache.get_router_info(snet)
            if router_info:
                router_snet, router_address, router_status = router_info
                if _debug: NetworkServiceAccessPoint._debug("    - router_address, router_status: %r, %r", router_address, router_status)

                # see if the router has changed
                if not (router_address == npdu.pduSource):
                    if _debug: NetworkServiceAccessPoint._debug("    - replacing path")

                    # pass this new path along to the cache
                    self.router_info_cache.update_router_info(adapter.adapterNet, npdu.pduSource, [snet])
            else:
                if _debug: NetworkServiceAccessPoint._debug("    - new path")

                # pass this new path along to the cache
                self.router_info_cache.update_router_info(adapter.adapterNet, npdu.pduSource, [snet])

        # check for destination routing
        if (not npdu.npduDADR) or (npdu.npduDADR.addrType == Address.nullAddr):
            if _debug: NetworkServiceAccessPoint._debug("    - no DADR")

            processLocally = (not self.local_adapter) or (adapter is self.local_adapter) or (npdu.npduNetMessage is not None)
            forwardMessage = False

        elif npdu.npduDADR.addrType == Address.remoteBroadcastAddr:
            if _debug: NetworkServiceAccessPoint._debug("    - DADR is remote broadcast")

            if (npdu.npduDADR.addrNet == adapter.adapterNet):
                NetworkServiceAccessPoint._warning("    - path error (2)")
                return

            processLocally = self.local_adapter \
                and (npdu.npduDADR.addrNet == self.local_adapter.adapterNet)
            forwardMessage = True

        elif npdu.npduDADR.addrType == Address.remoteStationAddr:
            if _debug: NetworkServiceAccessPoint._debug("    - DADR is remote station")

            if (npdu.npduDADR.addrNet == adapter.adapterNet):
                NetworkServiceAccessPoint._warning("    - path error (3)")
                return

            processLocally = self.local_adapter \
                and (npdu.npduDADR.addrNet == self.local_adapter.adapterNet) \
                and (npdu.npduDADR.addrAddr == self.local_address.addrAddr)
            forwardMessage = not processLocally

        elif npdu.npduDADR.addrType == Address.globalBroadcastAddr:
            if _debug: NetworkServiceAccessPoint._debug("    - DADR is global broadcast")

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
            if _debug: NetworkServiceAccessPoint._debug("    - application layer message")

            if processLocally and self.serverPeer:
                if _debug: NetworkServiceAccessPoint._debug("    - processing APDU locally")

                # decode as a generic APDU
                apdu = _APDU(user_data=npdu.pduUserData)
                apdu.decode(_deepcopy(npdu))
                if _debug: NetworkServiceAccessPoint._debug("    - apdu: %r", apdu)

                # see if it needs to look routed
                if (len(self.adapters) > 1) and (adapter != self.local_adapter):
                    # combine the source address
                    if not npdu.npduSADR:
                        apdu.pduSource = RemoteStation( adapter.adapterNet, npdu.pduSource.addrAddr )
                    else:
                        apdu.pduSource = npdu.npduSADR

                    # map the destination
                    if not npdu.npduDADR:
                        apdu.pduDestination = self.local_address
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

        else:
            if _debug: NetworkServiceAccessPoint._debug("    - network layer message")

            if processLocally:
                if npdu.npduNetMessage not in npdu_types:
                    if _debug: NetworkServiceAccessPoint._debug("    - unknown npdu type: %r", npdu.npduNetMessage)
                    return

                if _debug: NetworkServiceAccessPoint._debug("    - processing NPDU locally")

                # do a deeper decode of the NPDU
                xpdu = npdu_types[npdu.npduNetMessage](user_data=npdu.pduUserData)
                xpdu.decode(_deepcopy(npdu))

                # pass to the service element
                self.sap_request(adapter, xpdu)

        # might not need to forward this to other devices
        if not forwardMessage:
            if _debug: NetworkServiceAccessPoint._debug("    - no forwarding")
            return

        # make sure we're really a router
        if (len(self.adapters) == 1):
            if _debug: NetworkServiceAccessPoint._debug("    - not a router")
            return

        # make sure it hasn't looped
        if (npdu.npduHopCount == 0):
            if _debug: NetworkServiceAccessPoint._debug("    - no more hops")
            return

        # build a new NPDU to send to other adapters
        newpdu = _deepcopy(npdu)

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
            if _debug: NetworkServiceAccessPoint._debug("    - global broadcasting")
            newpdu.pduDestination = LocalBroadcast()

            for xadapter in self.adapters.values():
                if (xadapter is not adapter):
                    xadapter.process_npdu(_deepcopy(newpdu))
            return

        if (npdu.npduDADR.addrType == Address.remoteBroadcastAddr) \
                or (npdu.npduDADR.addrType == Address.remoteStationAddr):
            dnet = npdu.npduDADR.addrNet
            if _debug: NetworkServiceAccessPoint._debug("    - remote station/broadcast")

            # see if this a locally connected network
            if dnet in self.adapters:
                xadapter = self.adapters[dnet]
                if xadapter is adapter:
                    if _debug: NetworkServiceAccessPoint._debug("    - path error (4)")
                    return
                if _debug: NetworkServiceAccessPoint._debug("    - found path via %r", xadapter)

                # if this was a remote broadcast, it's now a local one
                if (npdu.npduDADR.addrType == Address.remoteBroadcastAddr):
                    newpdu.pduDestination = LocalBroadcast()
                else:
                    newpdu.pduDestination = LocalStation(npdu.npduDADR.addrAddr)

                # last leg in routing
                newpdu.npduDADR = None

                # send the packet downstream
                xadapter.process_npdu(_deepcopy(newpdu))
                return

            # see if there is routing information for this destination network
            router_info = self.router_info_cache.get_router_info(dnet)
            if router_info:
                router_net, router_address, router_status = router_info
                if _debug: NetworkServiceAccessPoint._debug(
                    "    - router_net, router_address, router_status: %r, %r, %r",
                    router_net, router_address, router_status,
                    )

                if router_net not in self.adapters:
                    if _debug: NetworkServiceAccessPoint._debug("    - path error (5)")
                    return

                xadapter = self.adapters[router_net]
                if _debug: NetworkServiceAccessPoint._debug("    - found path via %r", xadapter)

                # the destination is the address of the router
                newpdu.pduDestination = router_address

                # send the packet downstream
                xadapter.process_npdu(_deepcopy(newpdu))
                return

            if _debug: NetworkServiceAccessPoint._debug("    - no router info found")

            ### queue this message for reprocessing when the response comes back

            # try to find a path to the network
            xnpdu = WhoIsRouterToNetwork(dnet)
            xnpdu.pduDestination = LocalBroadcast()

            # send it to all of the connected adapters
            for xadapter in self.adapters.values():
                # skip the horse it rode in on
                if (xadapter is adapter):
                    continue

                # pass this along as if it came from the NSE
                self.sap_indication(xadapter, xnpdu)

            return

        if _debug: NetworkServiceAccessPoint._debug("    - bad DADR: %r", npdu.npduDADR)

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

            # loop through the adapters
            for xadapter in sap.adapters.values():
                if (xadapter is adapter):
                    continue

                # add the direct network
                netlist.append(xadapter.adapterNet)

                ### add the other reachable

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
            dnet = npdu.wirtnNetwork

            # check the directly connected networks
            if dnet in sap.adapters:
                if _debug: NetworkServiceElement._debug("    - directly connected")

                # build a response
                iamrtn = IAmRouterToNetwork([dnet], user_data=npdu.pduUserData)
                iamrtn.pduDestination = npdu.pduSource

                # send it back
                self.response(adapter, iamrtn)

            else:
                # see if there is routing information for this source network
                router_info = sap.router_info_cache.get_router_info(dnet)
                if router_info:
                    if _debug: NetworkServiceElement._debug("    - router found")

                    router_net, router_address, router_status = router_info
                    if _debug: NetworkServiceElement._debug(
                        "    - router_net, router_address, router_status: %r, %r, %r",
                        router_net, router_address, router_status,
                        )
                    if router_net not in sap.adapters:
                        if _debug: NetworkServiceElement._debug("    - path error (6)")
                        return

                    # build a response
                    iamrtn = IAmRouterToNetwork([dnet], user_data=npdu.pduUserData)
                    iamrtn.pduDestination = npdu.pduSource

                    # send it back
                    self.response(adapter, iamrtn)

                else:
                    if _debug: NetworkServiceElement._debug("    - forwarding request to other adapters")

                    # build a request
                    whoisrtn = WhoIsRouterToNetwork(dnet, user_data=npdu.pduUserData)
                    whoisrtn.pduDestination = LocalBroadcast()

                    # if the request had a source, forward it along
                    if npdu.npduSADR:
                        whoisrtn.npduSADR = npdu.npduSADR
                    else:
                        whoisrtn.npduSADR = RemoteStation(adapter.adapterNet, npdu.pduSource.addrAddr)
                    if _debug: NetworkServiceElement._debug("    - whoisrtn: %r", whoisrtn)

                    # send it to all of the (other) adapters
                    for xadapter in sap.adapters.values():
                        if xadapter is not adapter:
                            if _debug: NetworkServiceElement._debug("    - sending on adapter: %r", xadapter)
                            self.request(xadapter, whoisrtn)

    def IAmRouterToNetwork(self, adapter, npdu):
        if _debug: NetworkServiceElement._debug("IAmRouterToNetwork %r %r", adapter, npdu)

        # reference the service access point
        sap = self.elementService
        if _debug: NetworkServiceElement._debug("    - sap: %r", sap)

        # pass along to the service access point
        sap.add_router_references(adapter.adapterNet, npdu.pduSource, npdu.iartnNetworkList)

        # skip if this is not a router
        if len(sap.adapters) > 1:
            # build a broadcast annoucement
            iamrtn = IAmRouterToNetwork(npdu.iartnNetworkList, user_data=npdu.pduUserData)
            iamrtn.pduDestination = LocalBroadcast()

            # send it to all of the connected adapters
            for xadapter in sap.adapters.values():
                # skip the horse it rode in on
                if (xadapter is adapter):
                    continue

                # request this
                self.request(xadapter, iamrtn)

        # look for pending NPDUs for the networks
        for dnet in npdu.iartnNetworkList:
            pending_npdus = sap.pending_nets.get(dnet, None)
            if pending_npdus is not None:
                if _debug: NetworkServiceElement._debug("    - %d pending to %r", len(pending_npdus), dnet)

                # delete the references
                del sap.pending_nets[dnet]

                # now reprocess them
                for pending_npdu in pending_npdus:
                    if _debug: NetworkServiceElement._debug("    - sending %s", repr(pending_npdu))

                    # the destination is the address of the router
                    pending_npdu.pduDestination = npdu.pduSource

                    # send the packet downstream
                    adapter.process_npdu(pending_npdu)

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

