#!/usr/bin/python

"""
Network Service
"""

from copy import deepcopy as _deepcopy

from .settings import settings
from .debugging import ModuleLogger, DebugContents, bacpypes_debugging
from .errors import ConfigurationError

from .core import deferred
from .comm import Client, Server, bind, \
    ServiceAccessPoint, ApplicationServiceElement
from .task import FunctionTask

from .pdu import Address, LocalBroadcast, LocalStation, PDU, RemoteStation, \
    GlobalBroadcast
from .npdu import NPDU, npdu_types, IAmRouterToNetwork, WhoIsRouterToNetwork, \
    WhatIsNetworkNumber, NetworkNumberIs
from .apdu import APDU as _APDU

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# router status values
ROUTER_AVAILABLE = 0            # normal
ROUTER_BUSY = 1                 # router is busy
ROUTER_DISCONNECTED = 2         # could make a connection, but hasn't
ROUTER_UNREACHABLE = 3          # temporarily unreachable

#
#   RouterInfo
#

class RouterInfo(DebugContents):
    """These objects are routing information records that map router
    addresses with destination networks."""

    _debug_contents = ('snet', 'address', 'dnets')

    def __init__(self, snet, address):
        self.snet = snet        # source network
        self.address = address  # address of the router
        self.dnets = {}         # {dnet: status}

    def set_status(self, dnets, status):
        """Change the status of each of the DNETS."""
        for dnet in dnets:
            self.dnets[dnet] = status

#
#   RouterInfoCache
#

@bacpypes_debugging
class RouterInfoCache:

    def __init__(self):
        if _debug: RouterInfoCache._debug("__init__")

        self.routers = {}           # snet -> {Address: RouterInfo}
        self.path_info = {}         # (snet, dnet) -> RouterInfo

    def get_router_info(self, snet, dnet):
        if _debug: RouterInfoCache._debug("get_router_info %r %r", snet, dnet)

        # return the network and address
        router_info = self.path_info.get((snet, dnet), None)
        if _debug: RouterInfoCache._debug("   - router_info: %r", router_info)

        return router_info

    def update_router_info(self, snet, address, dnets, status=ROUTER_AVAILABLE):
        if _debug: RouterInfoCache._debug("update_router_info %r %r %r", snet, address, dnets)

        existing_router_info = self.routers.get(snet, {}).get(address, None)

        other_routers = set()
        for dnet in dnets:
            other_router = self.path_info.get((snet, dnet), None)
            if other_router and (other_router is not existing_router_info):
                other_routers.add(other_router)

        # remove the dnets from other router(s) and paths
        if other_routers:
            for router_info in other_routers:
                for dnet in dnets:
                    if dnet in router_info.dnets:
                        del router_info.dnets[dnet]
                        del self.path_info[(snet, dnet)]
                        if _debug: RouterInfoCache._debug("    - del path: %r -> %r via %r", snet, dnet, router_info.address)
                if not router_info.dnets:
                    del self.routers[snet][router_info.address]
                    if _debug: RouterInfoCache._debug("    - no dnets: %r via %r", snet, router_info.address)

        # update current router info if there is one
        if not existing_router_info:
            router_info = RouterInfo(snet, address)
            if snet not in self.routers:
                self.routers[snet] = {address: router_info}
            else:
                self.routers[snet][address] = router_info

            for dnet in dnets:
                self.path_info[(snet, dnet)] = router_info
                if _debug: RouterInfoCache._debug("    - add path: %r -> %r via %r", snet, dnet, router_info.address)
                router_info.dnets[dnet] = status
        else:
            for dnet in dnets:
                if dnet not in existing_router_info.dnets:
                    self.path_info[(snet, dnet)] = existing_router_info
                    if _debug: RouterInfoCache._debug("    - add path: %r -> %r", snet, dnet)
                existing_router_info.dnets[dnet] = status

    def update_router_status(self, snet, address, status):
        if _debug: RouterInfoCache._debug("update_router_status %r %r %r", snet, address, status)

        existing_router_info = self.routers.get(snet, {}).get(address, None)
        if not existing_router_info:
            if _debug: RouterInfoCache._debug("    - not a router we know about")
            return

        existing_router_info.status = status
        if _debug: RouterInfoCache._debug("    - status updated")

    def delete_router_info(self, snet, address=None, dnets=None):
        if _debug: RouterInfoCache._debug("delete_router_info %r %r %r", dnets)

        if (address is None) and (dnets is None):
            raise RuntimeError("inconsistent parameters")

        # remove the dnets from a router or the whole router
        if (address is not None):
            router_info = self.routers.get(snet, {}).get(address, None)
            if not router_info:
                if _debug: RouterInfoCache._debug("    - no route info")
            else:
                for dnet in (dnets or router_info.dnets):
                    del self.path_info[(snet, dnet)]
                    if _debug: RouterInfoCache._debug("    - del path: %r -> %r via %r", snet, dnet, router_info.address)
                del self.routers[snet][address]
            return

        # look for routers to the dnets
        other_routers = set()
        for dnet in dnets:
            other_router = self.path_info.get((snet, dnet), None)
            if other_router and (other_router is not existing_router_info):
                other_routers.add(other_router)

        # remove the dnets from other router(s) and paths
        for router_info in other_routers:
            for dnet in dnets:
                if dnet in router_info.dnets:
                    del router_info.dnets[dnet]
                    del self.path_info[(snet, dnet)]
                    if _debug: RouterInfoCache._debug("    - del path: %r -> %r via %r", snet, dnet, router_info.address)
            if not router_info.dnets:
                del self.routers[snet][router_info.address]
                if _debug: RouterInfoCache._debug("    - no dnets: %r via %r", snet, router_info.address)

    def update_source_network(self, old_snet, new_snet):
        if _debug: RouterInfoCache._debug("update_source_network %r %r", old_snet, new_snet)

        if old_snet not in self.routers:
            if _debug: RouterInfoCache._debug("    - no router references: %r", list(self.routers.keys()))
            return

        # move the router info records to the new net
        snet_routers = self.routers[new_snet] = self.routers.pop(old_snet)

        # update the paths
        for address, router_info in snet_routers.items():
            for dnet in router_info.dnets:
                self.path_info[(new_snet, dnet)] = self.path_info.pop((old_snet, dnet))

#
#   NetworkAdapter
#

@bacpypes_debugging
class NetworkAdapter(Client, DebugContents):

    _debug_contents = (
        'adapterSAP-',
        'adapterNet',
        'adapterAddr',
        'adapterNetConfigured',
        )

    def __init__(self, sap, net, addr, cid=None):
        if _debug: NetworkAdapter._debug("__init__ %s %r %r cid=%r", sap, net, addr, cid)
        Client.__init__(self, cid)
        self.adapterSAP = sap
        self.adapterNet = net
        self.adapterAddr = addr

        # record if this was 0=learned, 1=configured, None=unknown
        if net is None:
            self.adapterNetConfigured = None
        else:
            self.adapterNetConfigured = 1

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

    _debug_contents = ('adapters++', 'pending_nets',
        'local_adapter-',
        )

    def __init__(self, router_info_cache=None, sap=None, sid=None):
        if _debug: NetworkServiceAccessPoint._debug("__init__ sap=%r sid=%r", sap, sid)
        ServiceAccessPoint.__init__(self, sap)
        Server.__init__(self, sid)

        # map of directly connected networks
        self.adapters = {}          # net -> NetworkAdapter

        # use the provided cache or make a default one
        self.router_info_cache = router_info_cache or RouterInfoCache()

        # map to a list of application layer packets waiting for a path
        self.pending_nets = {}

        # set when bind() is called
        self.local_adapter = None

    def bind(self, server, net=None, address=None):
        """Create a network adapter object and bind.

        bind(s, None, None)
            Called for simple applications, local network unknown, no specific
            address, APDUs sent upstream

        bind(s, net, None)
            Called for routers, bind to the network, (optionally?) drop APDUs

        bind(s, None, address)
            Called for applications or routers, bind to the network (to be
            discovered), send up APDUs with a metching address

        bind(s, net, address)
            Called for applications or routers, bind to the network, send up
            APDUs with a metching address.
        """
        if _debug: NetworkServiceAccessPoint._debug("bind %r net=%r address=%r", server, net, address)

        # make sure this hasn't already been called with this network
        if net in self.adapters:
            raise RuntimeError("already bound: %r" % (net,))

        # create an adapter object, add it to our map
        adapter = NetworkAdapter(self, net, address)
        self.adapters[net] = adapter
        if _debug: NetworkServiceAccessPoint._debug("    - adapter: %r, %r", net, adapter)

        # if the address was given, make it the "local" one
        if address:
            if _debug: NetworkServiceAccessPoint._debug("    - setting local adapter")
            self.local_adapter = adapter

        # if the local adapter isn't set yet, make it the first one, and can
        # be overridden by a subsequent call if the address is specified
        if not self.local_adapter:
            if _debug: NetworkServiceAccessPoint._debug("    - default local adapter")
            self.local_adapter = adapter

        if not self.local_adapter.adapterAddr:
            if _debug: NetworkServiceAccessPoint._debug("    - no local address")

        # bind to the server
        bind(adapter, server)

    #-----

    def update_router_references(self, snet, address, dnets):
        """Update references to routers."""
        if _debug: NetworkServiceAccessPoint._debug("update_router_references %r %r %r", snet, address, dnets)

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

        # get the local adapter
        local_adapter = self.local_adapter
        if _debug: NetworkServiceAccessPoint._debug("    - local_adapter: %r", local_adapter)

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

        # if this is route aware, use it for the destination
        if settings.route_aware and npdu.pduDestination.addrRoute:
            # always a local station for now, in theory this could also be
            # a local braodcast address, remote station, or remote broadcast
            # but that is not supported by the patterns
            assert npdu.pduDestination.addrRoute.addrType == Address.localStationAddr
            if _debug: NetworkServiceAccessPoint._debug("    - routed: %r", npdu.pduDestination.addrRoute)

            if npdu.pduDestination.addrType in (Address.remoteStationAddr, Address.remoteBroadcastAddr, Address.globalBroadcastAddr):
                if _debug: NetworkServiceAccessPoint._debug("    - continue DADR: %r", apdu.pduDestination)
                npdu.npduDADR = apdu.pduDestination

            npdu.pduDestination = npdu.pduDestination.addrRoute
            local_adapter.process_npdu(npdu)
            return

        # local stations given to local adapter
        if (npdu.pduDestination.addrType == Address.localStationAddr):
            local_adapter.process_npdu(npdu)
            return

        # local broadcast given to local adapter
        if (npdu.pduDestination.addrType == Address.localBroadcastAddr):
            local_adapter.process_npdu(npdu)
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
        if _debug: NetworkServiceAccessPoint._debug("    - dnet: %r", dnet)

        # if the network matches the local adapter it's local
        if (dnet == local_adapter.adapterNet):
            if (npdu.pduDestination.addrType == Address.remoteStationAddr):
                if _debug: NetworkServiceAccessPoint._debug("    - mapping remote station to local station")
                npdu.pduDestination = LocalStation(npdu.pduDestination.addrAddr)
            elif (npdu.pduDestination.addrType == Address.remoteBroadcastAddr):
                if _debug: NetworkServiceAccessPoint._debug("    - mapping remote broadcast to local broadcast")
                npdu.pduDestination = LocalBroadcast()
            else:
                raise RuntimeError("addressing problem")

            local_adapter.process_npdu(npdu)
            return

        # get it ready to send when the path is found
        npdu.pduDestination = None
        npdu.npduDADR = apdu.pduDestination

        # we might already be waiting for a path for this network
        if dnet in self.pending_nets:
            if _debug: NetworkServiceAccessPoint._debug("    - already waiting for path")
            self.pending_nets[dnet].append(npdu)
            return

        # look for routing information from the network of one of our
        # adapters to the destination network
        router_info = None
        for snet, snet_adapter in self.adapters.items():
            router_info = self.router_info_cache.get_router_info(snet, dnet)
            if router_info:
                break

        # if there is info, we have a path
        if router_info:
            if _debug: NetworkServiceAccessPoint._debug("    - router_info found: %r", router_info)

            ### check the path status
            dnet_status = router_info.dnets[dnet]
            if _debug: NetworkServiceAccessPoint._debug("    - dnet_status: %r", dnet_status)

            # fix the destination
            npdu.pduDestination = router_info.address

            # send it along
            snet_adapter.process_npdu(npdu)

        else:
            if _debug: NetworkServiceAccessPoint._debug("    - no known path to network")

            # add it to the list of packets waiting for the network
            net_list = self.pending_nets.get(dnet, None)
            if net_list is None:
                net_list = self.pending_nets[dnet] = []
            net_list.append(npdu)

            # build a request for the network and send it to all of the adapters
            xnpdu = WhoIsRouterToNetwork(dnet)
            xnpdu.pduDestination = LocalBroadcast()

            # send it to all of the adapters
            for adapter in self.adapters.values():
                self.sap_indication(adapter, xnpdu)

    def process_npdu(self, adapter, npdu):
        if _debug: NetworkServiceAccessPoint._debug("process_npdu %r %r", adapter, npdu)

        # make sure our configuration is OK
        if not self.adapters:
            raise ConfigurationError("no adapters")

        # check for source routing
        if npdu.npduSADR and (npdu.npduSADR.addrType != Address.nullAddr):
            if _debug: NetworkServiceAccessPoint._debug("    - check source path")

            # see if this is attempting to spoof a directly connected network
            snet = npdu.npduSADR.addrNet
            if snet in self.adapters:
                NetworkServiceAccessPoint._warning("    - path error (1)")
                return

            # pass this new path along to the cache
            self.router_info_cache.update_router_info(adapter.adapterNet, npdu.pduSource, [snet])

        # check for destination routing
        if (not npdu.npduDADR) or (npdu.npduDADR.addrType == Address.nullAddr):
            if _debug: NetworkServiceAccessPoint._debug("    - no DADR")

            processLocally = (adapter is self.local_adapter) or (npdu.npduNetMessage is not None)
            forwardMessage = False

        elif npdu.npduDADR.addrType == Address.remoteBroadcastAddr:
            if _debug: NetworkServiceAccessPoint._debug("    - DADR is remote broadcast")

            if (npdu.npduDADR.addrNet == adapter.adapterNet):
                NetworkServiceAccessPoint._warning("    - path error (2)")
                return

            processLocally = (npdu.npduDADR.addrNet == self.local_adapter.adapterNet)
            forwardMessage = True

        elif npdu.npduDADR.addrType == Address.remoteStationAddr:
            if _debug: NetworkServiceAccessPoint._debug("    - DADR is remote station")

            if (npdu.npduDADR.addrNet == adapter.adapterNet):
                NetworkServiceAccessPoint._warning("    - path error (3)")
                return

            processLocally = (npdu.npduDADR.addrNet == self.local_adapter.adapterNet) \
                and (npdu.npduDADR.addrAddr == self.local_adapter.adapterAddr.addrAddr)
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
                        apdu.pduSource = RemoteStation(adapter.adapterNet, npdu.pduSource.addrAddr)
                    else:
                        apdu.pduSource = npdu.npduSADR
                    if settings.route_aware:
                        apdu.pduSource.addrRoute = npdu.pduSource

                    # map the destination
                    if not npdu.npduDADR:
                        apdu.pduDestination = self.local_adapter.adapterAddr
                    elif npdu.npduDADR.addrType == Address.globalBroadcastAddr:
                        apdu.pduDestination = GlobalBroadcast()
                    elif npdu.npduDADR.addrType == Address.remoteBroadcastAddr:
                        apdu.pduDestination = LocalBroadcast()
                    else:
                        apdu.pduDestination = self.local_adapter.adapterAddr
                else:
                    # combine the source address
                    if npdu.npduSADR:
                        apdu.pduSource = npdu.npduSADR
                        if settings.route_aware:
                            if _debug: NetworkServiceAccessPoint._debug("    - adding route")
                            apdu.pduSource.addrRoute = npdu.pduSource
                    else:
                        apdu.pduSource = npdu.pduSource

                    # pass along global broadcast
                    if npdu.npduDADR and npdu.npduDADR.addrType == Address.globalBroadcastAddr:
                        apdu.pduDestination = GlobalBroadcast()
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

            # look for routing information from the network of one of our
            # adapters to the destination network
            router_info = None
            for snet, snet_adapter in self.adapters.items():
                router_info = self.router_info_cache.get_router_info(snet, dnet)
                if router_info:
                    break

            # found a path
            if router_info:
                if _debug: NetworkServiceAccessPoint._debug("    - found path via %r", router_info)

                # the destination is the address of the router
                newpdu.pduDestination = router_info.address

                # send the packet downstream
                snet_adapter.process_npdu(_deepcopy(newpdu))
                return

            if _debug: NetworkServiceAccessPoint._debug("    - no router info found")

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

    _startup_disabled = False

    def __init__(self, eid=None):
        if _debug: NetworkServiceElement._debug("__init__ eid=%r", eid)
        ApplicationServiceElement.__init__(self, eid)

        # network number is timeout
        self.network_number_is_task = None

        # if starting up is enabled defer our startup function
        if not self._startup_disabled:
            deferred(self.startup)

    def startup(self):
        if _debug: NetworkServiceElement._debug("startup")

        # reference the service access point
        sap = self.elementService
        if _debug: NetworkServiceElement._debug("    - sap: %r", sap)

        # loop through all of the adapters
        for adapter in sap.adapters.values():
            if _debug: NetworkServiceElement._debug("    - adapter: %r", adapter)

            if (adapter.adapterNet is None):
                if _debug: NetworkServiceElement._debug("    - skipping, unknown net")
                continue
            elif (adapter.adapterAddr is None):
                if _debug: NetworkServiceElement._debug("    - skipping, unknown addr")
                continue

            # build a list of reachable networks
            netlist = []

            # loop through the adapters
            for xadapter in sap.adapters.values():
                if (xadapter is not adapter):
                    if (xadapter.adapterNet is None) or (xadapter.adapterAddr is None):
                        continue
                    netlist.append(xadapter.adapterNet)

            # skip for an empty list, perhaps they are not yet learned
            if not netlist:
                if _debug: NetworkServiceElement._debug("    - skipping, no netlist")
                continue

            # pass this along to the cache -- on hold #213
            # sap.router_info_cache.update_router_info(adapter.adapterNet, adapter.adapterAddr, netlist)

            # send an announcement
            self.i_am_router_to_network(adapter=adapter, network=netlist)

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

    def i_am_router_to_network(self, adapter=None, destination=None, network=None):
        if _debug: NetworkServiceElement._debug("i_am_router_to_network %r %r %r", adapter, destination, network)

        # reference the service access point
        sap = self.elementService
        if _debug: NetworkServiceElement._debug("    - sap: %r", sap)

        # if we're not a router, trouble
        if len(sap.adapters) == 1:
            raise RuntimeError("not a router")

        if adapter is not None:
            if destination is None:
                destination = LocalBroadcast()
            elif destination.addrType in (Address.localStationAddr, Address.localBroadcastAddr):
                pass
            elif destination.addrType == Address.remoteStationAddr:
                if destination.addrNet != adapter.adapterNet:
                    raise ValueError("invalid address, remote station for a different adapter")
                destination = LocalStation(destination.addrAddr)
            elif destination.addrType == Address.remoteBroadcastAddr:
                if destination.addrNet != adapter.adapterNet:
                    raise ValueError("invalid address, remote broadcast for a different adapter")
                destination = LocalBroadcast()
            else:
                raise TypeError("invalid destination address")
        else:
            if destination is None:
                destination = LocalBroadcast()
            elif destination.addrType == Address.localStationAddr:
                raise ValueError("ambiguous destination")
            elif destination.addrType == Address.localBroadcastAddr:
                pass
            elif destination.addrType == Address.remoteStationAddr:
                if destination.addrNet not in sap.adapters:
                    raise ValueError("invalid address, no network for remote station")
                adapter = sap.adapters[destination.addrNet]
                destination = LocalStation(destination.addrAddr)
            elif destination.addrType == Address.remoteBroadcastAddr:
                if destination.addrNet not in sap.adapters:
                    raise ValueError("invalid address, no network for remote broadcast")
                adapter = sap.adapters[destination.addrNet]
                destination = LocalBroadcast()
            else:
                raise TypeError("invalid destination address")
        if _debug: NetworkServiceElement._debug("    - adapter, destination, network: %r, %r, %r", adapter, destination, network)

        # process a single adapter or all of the adapters
        if adapter is not None:
            adapter_list = [adapter]
        else:
            adapter_list = list(sap.adapters.values())

        # loop through all of the adapters
        for adapter in adapter_list:
            # build a list of reachable networks
            netlist = []

            # loop through the adapters
            for xadapter in sap.adapters.values():
                if (xadapter is not adapter):
                    netlist.append(xadapter.adapterNet)
                    ### add the other reachable networks

            if network is None:
                pass
            elif isinstance(network, int):
                if network not in netlist:
                    continue
                netlist = [network]
            elif isinstance(network, list):
                netlist = [net for net in netlist if net in network]

            # build a response
            iamrtn = IAmRouterToNetwork(netlist)
            iamrtn.pduDestination = destination

            if _debug: NetworkServiceElement._debug("    - adapter, iamrtn: %r, %r", adapter, iamrtn)

            # send it back
            self.request(adapter, iamrtn)

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

                ### add the other reachable networks?

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

                if sap.adapters[dnet] is adapter:
                    if _debug: NetworkServiceElement._debug("    - same network")
                    return

                # build a response
                iamrtn = IAmRouterToNetwork([dnet], user_data=npdu.pduUserData)
                iamrtn.pduDestination = npdu.pduSource

                # send it back
                self.response(adapter, iamrtn)
                return


            # look for routing information from the network of one of our
            # adapters to the destination network
            router_info = None
            for snet, snet_adapter in sap.adapters.items():
                router_info = sap.router_info_cache.get_router_info(snet, dnet)
                if router_info:
                    break

            # found a path
            if router_info:
                if _debug: NetworkServiceElement._debug("    - router found: %r", router_info)

                if snet_adapter is adapter:
                    if _debug: NetworkServiceElement._debug("    - same network")
                    return

                # build a response
                iamrtn = IAmRouterToNetwork([dnet], user_data=npdu.pduUserData)
                iamrtn.pduDestination = npdu.pduSource

                # send it back
                self.response(adapter, iamrtn)

            else:
                if _debug: NetworkServiceElement._debug("    - forwarding to other adapters")

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
        sap.update_router_references(adapter.adapterNet, npdu.pduSource, npdu.iartnNetworkList)

        # skip if this is not a router
        if len(sap.adapters) == 1:
            if _debug: NetworkServiceElement._debug("    - not a router")

        else:
            if _debug: NetworkServiceElement._debug("    - forwarding to other adapters")

            # build a broadcast annoucement
            iamrtn = IAmRouterToNetwork(npdu.iartnNetworkList, user_data=npdu.pduUserData)
            iamrtn.pduDestination = LocalBroadcast()

            # send it to all of the connected adapters
            for xadapter in sap.adapters.values():
                if xadapter is not adapter:
                    if _debug: NetworkServiceElement._debug("    - sending on adapter: %r", xadapter)
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

    def what_is_network_number(self, adapter=None, address=None):
        if _debug: NetworkServiceElement._debug("what_is_network_number %r", adapter, address)

        # reference the service access point
        sap = self.elementService

        # a little error checking
        if (adapter is None) and (address is not None):
            raise RuntimeError("inconsistent parameters")

        # build a request
        winn = WhatIsNetworkNumber()
        winn.pduDestination = LocalBroadcast()

        # check for a specific adapter
        if adapter:
            if address is not None:
                winn.pduDestination = address
            adapter_list = [adapter]
        else:
            # send to adapters we don't know anything about
            adapter_list = []
            for xadapter in sap.adapters.values():
                if xadapter.adapterNet is None:
                    adapter_list.append(xadapter)
        if _debug: NetworkServiceElement._debug("    - adapter_list: %r", adapter_list)

        # send it to the adapter(s)
        for xadapter in adapter_list:
            self.request(xadapter, winn)

    def WhatIsNetworkNumber(self, adapter, npdu):
        if _debug: NetworkServiceElement._debug("WhatIsNetworkNumber %r %r", adapter, npdu)

        # reference the service access point
        sap = self.elementService

        # check to see if the local network is known
        if adapter.adapterNet is None:
            if _debug: NetworkServiceElement._debug("   - local network not known")
            return

        # if this is not a router, wait for somebody else to answer
        if (npdu.pduDestination.addrType == Address.localBroadcastAddr):
            if _debug: NetworkServiceElement._debug("    - local broadcast request")

            if len(sap.adapters) == 1:
                if _debug: NetworkServiceElement._debug("    - not a router")

                if self.network_number_is_task:
                    if _debug: NetworkServiceElement._debug("    - already waiting")
                else:
                    self.network_number_is_task = FunctionTask(self.network_number_is, adapter)
                    self.network_number_is_task.install_task(delta=10 * 1000)
                    return

        # send out what we know
        self.network_number_is(adapter)

    def network_number_is(self, adapter=None):
        if _debug: NetworkServiceElement._debug("network_number_is %r", adapter)

        # reference the service access point
        sap = self.elementService

        # specific adapter, or all configured adapters
        if adapter is not None:
            adapter_list = [adapter]
        else:
            # send to adapters we are configured to know
            adapter_list = []
            for xadapter in sap.adapters.values():
                if (xadapter.adapterNet is not None) and (xadapter.adapterNetConfigured == 1):
                    adapter_list.append(xadapter)
        if _debug: NetworkServiceElement._debug("    - adapter_list: %r", adapter_list)

        # loop through the adapter(s)
        for xadapter in adapter_list:
            if xadapter.adapterNet is None:
                if _debug: NetworkServiceElement._debug("    - unknown network: %r", xadapter)
                continue

            # build a broadcast annoucement
            nni = NetworkNumberIs(net=xadapter.adapterNet, flag=xadapter.adapterNetConfigured)
            nni.pduDestination = LocalBroadcast()
            if _debug: NetworkServiceElement._debug("    - nni: %r", nni)

            # send it to the adapter
            self.request(xadapter, nni)

    def NetworkNumberIs(self, adapter, npdu):
        if _debug: NetworkServiceElement._debug("NetworkNumberIs %r %r", adapter, npdu)

        # reference the service access point
        sap = self.elementService

        # if this was not sent as a broadcast, ignore it
        if (npdu.pduDestination.addrType != Address.localBroadcastAddr):
            if _debug: NetworkServiceElement._debug("    - not broadcast")
            return

        # if we are waiting for someone else to say what this network number
        # is, cancel that task
        if self.network_number_is_task:
            if _debug: NetworkServiceElement._debug("    - cancel waiting task")
            self.network_number_is_task.suspend_task()
            self.network_number_is_task = None

        # check to see if the local network is known
        if adapter.adapterNet is None:
            if _debug: NetworkServiceElement._debug("   - local network not known: %r", list(sap.adapters.keys()))

            # update the routing information
            sap.router_info_cache.update_source_network(None, npdu.nniNet)

            # delete the reference from an unknown network
            del sap.adapters[None]

            adapter.adapterNet = npdu.nniNet
            adapter.adapterNetConfigured = 0

            # we now know what network this is
            sap.adapters[adapter.adapterNet] = adapter

            if _debug: NetworkServiceElement._debug("   - local network learned")
            return

        # check if this matches what we have
        if adapter.adapterNet == npdu.nniNet:
            if _debug: NetworkServiceElement._debug("   - matches what we have")
            return

        # check it this matches what we know, if we know it
        if adapter.adapterNetConfigured == 1:
            if _debug: NetworkServiceElement._debug("   - doesn't match what we know")
            return

        if _debug: NetworkServiceElement._debug("   - learning something new")

        # update the routing information
        sap.router_info_cache.update_source_network(adapter.adapterNet, npdu.nniNet)

        # delete the reference from the old (learned) network
        del sap.adapters[adapter.adapterNet]

        adapter.adapterNet = npdu.nniNet
        adapter.adapterNetConfigured = npdu.nniFlag

        # we now know what network this is
        sap.adapters[adapter.adapterNet] = adapter

