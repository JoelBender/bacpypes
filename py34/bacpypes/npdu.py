#!/usr/bin/python

"""
NPDU
"""

from .errors import DecodingError
from .debugging import ModuleLogger, DebugContents, bacpypes_debugging, btox

from .pdu import Address, RemoteStation, RemoteBroadcast, GlobalBroadcast, \
    PCI, PDUData

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# a dictionary of message type values and classes
npdu_types = {}

def register_npdu_type(klass):
    npdu_types[klass.messageType] = klass

#
#  NPCI
#

@bacpypes_debugging
class NPCI(PCI, DebugContents):

    _debug_contents = ('npduVersion', 'npduControl', 'npduDADR', 'npduSADR'
        , 'npduHopCount', 'npduNetMessage', 'npduVendorID'
        )

    whoIsRouterToNetwork            = 0x00
    iAmRouterToNetwork              = 0x01
    iCouldBeRouterToNetwork         = 0x02
    rejectMessageToNetwork          = 0x03
    routerBusyToNetwork             = 0x04
    routerAvailableToNetwork        = 0x05
    initializeRoutingTable          = 0x06
    initializeRoutingTableAck       = 0x07
    establishConnectionToNetwork    = 0x08
    disconnectConnectionToNetwork   = 0x09
    challengeRequest                = 0x0A
    securityPayload                 = 0x0B
    securityResponse                = 0x0C
    requestKeyUpdate                = 0x0D
    updateKeySet                    = 0x0E
    updateDistributionKey           = 0x0F
    requestMasterKey                = 0x10
    setMasterKey                    = 0x11
    whatIsNetworkNumber             = 0x12
    networkNumberIs                 = 0x13

    def __init__(self, *args, **kwargs):
        super(NPCI, self).__init__(*args, **kwargs)

        self.npduVersion = 1
        self.npduControl = None
        self.npduDADR = None
        self.npduSADR = None
        self.npduHopCount = None
        self.npduNetMessage = None
        self.npduVendorID = None

    def update(self, npci):
        PCI.update(self, npci)
        self.npduVersion = npci.npduVersion
        self.npduControl = npci.npduControl
        self.npduDADR = npci.npduDADR
        self.npduSADR = npci.npduSADR
        self.npduHopCount = npci.npduHopCount
        self.npduNetMessage = npci.npduNetMessage
        self.npduVendorID = npci.npduVendorID

    def encode(self, pdu):
        """encode the contents of the NPCI into the PDU."""
        if _debug: NPCI._debug("encode %s", repr(pdu))

        PCI.update(pdu, self)

        # only version 1 messages supported
        pdu.put(self.npduVersion)

        # build the flags
        if self.npduNetMessage is not None:
            netLayerMessage = 0x80
        else:
            netLayerMessage = 0x00

        # map the destination address
        dnetPresent = 0x00
        if self.npduDADR is not None:
            dnetPresent = 0x20

        # map the source address
        snetPresent = 0x00
        if self.npduSADR is not None:
            snetPresent = 0x08

        # encode the control octet
        control = netLayerMessage | dnetPresent | snetPresent
        if self.pduExpectingReply:
            control |= 0x04
        control |= (self.pduNetworkPriority & 0x03)
        self.npduControl = control
        pdu.put(control)

        # make sure expecting reply and priority get passed down
        pdu.pduExpectingReply = self.pduExpectingReply
        pdu.pduNetworkPriority = self.pduNetworkPriority

        # encode the destination address
        if dnetPresent:
            if self.npduDADR.addrType == Address.remoteStationAddr:
                pdu.put_short(self.npduDADR.addrNet)
                pdu.put(self.npduDADR.addrLen)
                pdu.put_data(self.npduDADR.addrAddr)
            elif self.npduDADR.addrType == Address.remoteBroadcastAddr:
                pdu.put_short(self.npduDADR.addrNet)
                pdu.put(0)
            elif self.npduDADR.addrType == Address.globalBroadcastAddr:
                pdu.put_short(0xFFFF)
                pdu.put(0)

        # encode the source address
        if snetPresent:
            pdu.put_short(self.npduSADR.addrNet)
            pdu.put(self.npduSADR.addrLen)
            pdu.put_data(self.npduSADR.addrAddr)

        # put the hop count
        if dnetPresent:
            pdu.put(self.npduHopCount)

        # put the network layer message type (if present)
        if netLayerMessage:
            pdu.put(self.npduNetMessage)
            # put the vendor ID
            if (self.npduNetMessage >= 0x80) and (self.npduNetMessage <= 0xFF):
                pdu.put_short(self.npduVendorID)

    def decode(self, pdu):
        """decode the contents of the PDU and put them into the NPDU."""
        if _debug: NPCI._debug("decode %s", str(pdu))

        PCI.update(self, pdu)

        # check the length
        if len(pdu.pduData) < 2:
            raise DecodingError("invalid length")

        # only version 1 messages supported
        self.npduVersion = pdu.get()
        if (self.npduVersion != 0x01):
            raise DecodingError("only version 1 messages supported")

        # decode the control octet
        self.npduControl = control = pdu.get()
        netLayerMessage = control & 0x80
        dnetPresent = control & 0x20
        snetPresent = control & 0x08
        self.pduExpectingReply = (control & 0x04) != 0
        self.pduNetworkPriority = control & 0x03

        # extract the destination address
        if dnetPresent:
            dnet = pdu.get_short()
            dlen = pdu.get()
            dadr = pdu.get_data(dlen)

            if dnet == 0xFFFF:
                self.npduDADR = GlobalBroadcast()
            elif dlen == 0:
                self.npduDADR = RemoteBroadcast(dnet)
            else:
                self.npduDADR = RemoteStation(dnet, dadr)

        # extract the source address
        if snetPresent:
            snet = pdu.get_short()
            slen = pdu.get()
            sadr = pdu.get_data(slen)

            if snet == 0xFFFF:
                raise DecodingError("SADR can't be a global broadcast")
            elif slen == 0:
                raise DecodingError("SADR can't be a remote broadcast")

            self.npduSADR = RemoteStation(snet, sadr)

        # extract the hop count
        if dnetPresent:
            self.npduHopCount = pdu.get()

        # extract the network layer message type (if present)
        if netLayerMessage:
            self.npduNetMessage = pdu.get()
            if (self.npduNetMessage >= 0x80) and (self.npduNetMessage <= 0xFF):
                # extract the vendor ID
                self.npduVendorID = pdu.get_short()
        else:
            # application layer message
            self.npduNetMessage = None

    def npci_contents(self, use_dict=None, as_class=dict):
        """Return the contents of an object as a dict."""
        if _debug: NPCI._debug("npci_contents use_dict=%r as_class=%r", use_dict, as_class)

        # make/extend the dictionary of content
        if use_dict is None:
            if _debug: NPCI._debug("    - new use_dict")
            use_dict = as_class()

        # version and control are simple
        use_dict.__setitem__('version', self.npduVersion)
        use_dict.__setitem__('control', self.npduControl)

        # dnet/dlen/dadr
        if self.npduDADR is not None:
            if self.npduDADR.addrType == Address.remoteStationAddr:
                use_dict.__setitem__('dnet', self.npduDADR.addrNet)
                use_dict.__setitem__('dlen', self.npduDADR.addrLen)
                use_dict.__setitem__('dadr', btox(self.npduDADR.addrAddr or b''))
            elif self.npduDADR.addrType == Address.remoteBroadcastAddr:
                use_dict.__setitem__('dnet', self.npduDADR.addrNet)
                use_dict.__setitem__('dlen', 0)
                use_dict.__setitem__('dadr', '')
            elif self.npduDADR.addrType == Address.globalBroadcastAddr:
                use_dict.__setitem__('dnet', 0xFFFF)
                use_dict.__setitem__('dlen', 0)
                use_dict.__setitem__('dadr', '')

        # snet/slen/sadr
        if self.npduSADR is not None:
            use_dict.__setitem__('snet', self.npduSADR.addrNet)
            use_dict.__setitem__('slen', self.npduSADR.addrLen)
            use_dict.__setitem__('sadr', btox(self.npduSADR.addrAddr or b''))

        # hop count
        if self.npduHopCount is not None:
            use_dict.__setitem__('hop_count', self.npduHopCount)

        # network layer message name decoded
        if self.npduNetMessage is not None:
            use_dict.__setitem__('net_message', self.npduNetMessage)
        if self.npduVendorID is not None:
            use_dict.__setitem__('vendor_id', self.npduVendorID)

        # return what we built/updated
        return use_dict

#
#   NPDU
#

@bacpypes_debugging
class NPDU(NPCI, PDUData):

    def __init__(self, *args, **kwargs):
        super(NPDU, self).__init__(*args, **kwargs)

    def encode(self, pdu):
        NPCI.encode(self, pdu)
        pdu.put_data(self.pduData)

    def decode(self, pdu):
        NPCI.decode(self, pdu)
        self.pduData = pdu.get_data(len(pdu.pduData))

    def npdu_contents(self, use_dict=None, as_class=dict):
        return PDUData.pdudata_contents(self, use_dict=use_dict, as_class=as_class)

    def dict_contents(self, use_dict=None, as_class=dict):
        """Return the contents of an object as a dict."""
        if _debug: NPDU._debug("dict_contents use_dict=%r as_class=%r", use_dict, as_class)

        # make/extend the dictionary of content
        if use_dict is None:
            use_dict = as_class()

        # call the parent classes
        self.npci_contents(use_dict=use_dict, as_class=as_class)
        self.npdu_contents(use_dict=use_dict, as_class=as_class)

        # return what we built/updated
        return use_dict

#
#   key_value_contents
#

@bacpypes_debugging
def key_value_contents(use_dict=None, as_class=dict, key_values=()):
    """Return the contents of an object as a dict."""
    if _debug: key_value_contents._debug("key_value_contents use_dict=%r as_class=%r key_values=%r", use_dict, as_class, key_values)

    # make/extend the dictionary of content
    if use_dict is None:
        use_dict = as_class()

    # loop through the values and save them
    for k, v in key_values:
        if v is not None:
            if hasattr(v, 'dict_contents'):
                v = v.dict_contents(as_class=as_class)
            use_dict.__setitem__(k, v)

    # return what we built/updated
    return use_dict

#------------------------------

#
#   WhoIsRouterToNetwork
#

class WhoIsRouterToNetwork(NPDU):

    _debug_contents = ('wirtnNetwork',)

    messageType = 0x00

    def __init__(self, net=None, *args, **kwargs):
        super(WhoIsRouterToNetwork, self).__init__(*args, **kwargs)

        self.npduNetMessage = WhoIsRouterToNetwork.messageType
        self.wirtnNetwork = net

    def encode(self, npdu):
        NPCI.update(npdu, self)
        if self.wirtnNetwork is not None:
            npdu.put_short( self.wirtnNetwork )

    def decode(self, npdu):
        NPCI.update(self, npdu)
        if npdu.pduData:
            self.wirtnNetwork = npdu.get_short()
        else:
            self.wirtnNetwork = None

    def npdu_contents(self, use_dict=None, as_class=dict):
        return key_value_contents(use_dict=use_dict, as_class=as_class,
            key_values=(
                ('function', 'WhoIsRouterToNetwork'),
                ('network', self.wirtnNetwork),
            ))

register_npdu_type(WhoIsRouterToNetwork)

#
#   IAmRouterToNetwork
#

class IAmRouterToNetwork(NPDU):

    _debug_contents = ('iartnNetworkList',)

    messageType = 0x01

    def __init__(self, netList=[], *args, **kwargs):
        super(IAmRouterToNetwork, self).__init__(*args, **kwargs)

        self.npduNetMessage = IAmRouterToNetwork.messageType
        self.iartnNetworkList = netList

    def encode(self, npdu):
        NPCI.update(npdu, self)
        for net in self.iartnNetworkList:
            npdu.put_short(net)

    def decode(self, npdu):
        NPCI.update(self, npdu)
        self.iartnNetworkList = []
        while npdu.pduData:
            self.iartnNetworkList.append(npdu.get_short())

    def npdu_contents(self, use_dict=None, as_class=dict):
        return key_value_contents(use_dict=use_dict, as_class=as_class,
            key_values=(
                ('function', 'IAmRouterToNetwork'),
                ('network_list', self.iartnNetworkList),
            ))

register_npdu_type(IAmRouterToNetwork)

#
#   ICouldBeRouterToNetwork
#

class ICouldBeRouterToNetwork(NPDU):

    _debug_contents = ('icbrtnNetwork','icbrtnPerformanceIndex')

    messageType = 0x02

    def __init__(self, net=None, perf=None, *args, **kwargs):
        super(ICouldBeRouterToNetwork, self).__init__(*args, **kwargs)

        self.npduNetMessage = ICouldBeRouterToNetwork.messageType
        self.icbrtnNetwork = net
        self.icbrtnPerformanceIndex = perf

    def encode(self, npdu):
        NPCI.update(npdu, self)
        npdu.put_short( self.icbrtnNetwork )
        npdu.put( self.icbrtnPerformanceIndex )

    def decode(self, npdu):
        NPCI.update(self, npdu)
        self.icbrtnNetwork = npdu.get_short()
        self.icbrtnPerformanceIndex = npdu.get()

    def npdu_contents(self, use_dict=None, as_class=dict):
        return key_value_contents(use_dict=use_dict, as_class=as_class,
            key_values=(
                ('function', 'ICouldBeRouterToNetwork'),
                ('network', self.icbrtnNetwork),
                ('performance_index', self.icbrtnPerformanceIndex),
            ))

register_npdu_type(ICouldBeRouterToNetwork)

#
#   RejectMessageToNetwork
#

class RejectMessageToNetwork(NPDU):

    _debug_contents = ('rmtnRejectReason','rmtnDNET')

    messageType = 0x03

    def __init__(self, reason=None, dnet=None, *args, **kwargs):
        super(RejectMessageToNetwork, self).__init__(*args, **kwargs)

        self.npduNetMessage = RejectMessageToNetwork.messageType
        self.rmtnRejectionReason = reason
        self.rmtnDNET = dnet

    def encode(self, npdu):
        NPCI.update(npdu, self)
        npdu.put( self.rmtnRejectionReason )
        npdu.put_short( self.rmtnDNET )

    def decode(self, npdu):
        NPCI.update(self, npdu)
        self.rmtnRejectionReason = npdu.get()
        self.rmtnDNET = npdu.get_short()

    def npdu_contents(self, use_dict=None, as_class=dict):
        return key_value_contents(use_dict=use_dict, as_class=as_class,
            key_values=(
                ('function', 'RejectMessageToNetwork'),
                ('reject_reason', self.rmtnRejectionReason),
                ('dnet', self.rmtnDNET),
            ))

register_npdu_type(RejectMessageToNetwork)

#
#   RouterBusyToNetwork
#

class RouterBusyToNetwork(NPDU):

    _debug_contents = ('rbtnNetworkList',)

    messageType = 0x04

    def __init__(self, netList=[], *args, **kwargs):
        super(RouterBusyToNetwork, self).__init__(*args, **kwargs)

        self.npduNetMessage = RouterBusyToNetwork.messageType
        self.rbtnNetworkList = netList

    def encode(self, npdu):
        NPCI.update(npdu, self)
        for net in self.rbtnNetworkList:
            npdu.put_short(net)

    def decode(self, npdu):
        NPCI.update(self, npdu)
        self.rbtnNetworkList = []
        while npdu.pduData:
            self.rbtnNetworkList.append(npdu.get_short())

    def npdu_contents(self, use_dict=None, as_class=dict):
        return key_value_contents(use_dict=use_dict, as_class=as_class,
            key_values=(
                ('function', 'RouterBusyToNetwork'),
                ('network_list', self.rbtnNetworkList),
            ))

register_npdu_type(RouterBusyToNetwork)

#
#   RouterAvailableToNetwork
#

class RouterAvailableToNetwork(NPDU):

    _debug_contents = ('ratnNetworkList',)

    messageType = 0x05

    def __init__(self, netList=[], *args, **kwargs):
        super(RouterAvailableToNetwork, self).__init__(*args, **kwargs)

        self.npduNetMessage = RouterAvailableToNetwork.messageType
        self.ratnNetworkList = netList

    def encode(self, npdu):
        NPCI.update(npdu, self)
        for net in self.ratnNetworkList:
            npdu.put_short(net)

    def decode(self, npdu):
        NPCI.update(self, npdu)
        self.ratnNetworkList = []
        while npdu.pduData:
            self.ratnNetworkList.append(npdu.get_short())

    def npdu_contents(self, use_dict=None, as_class=dict):
        return key_value_contents(use_dict=use_dict, as_class=as_class,
            key_values=(
                ('function', 'RouterAvailableToNetwork'),
                ('network_list', self.ratnNetworkList),
            ))

register_npdu_type(RouterAvailableToNetwork)

#
#   Routing Table Entry
#

class RoutingTableEntry(DebugContents):

    _debug_contents = ('rtDNET', 'rtPortID', 'rtPortInfo')

    def __init__(self, dnet=None, portID=None, portInfo=None):
        self.rtDNET = dnet
        self.rtPortID = portID
        self.rtPortInfo = portInfo

    def __eq__(self, other):
        """Return true iff entries are identical."""
        return (self.rtDNET == other.rtDNET) and \
            (self.rtPortID == other.rtPortID) and \
            (self.rtPortInfo == other.rtPortInfo)

    def dict_contents(self, use_dict=None, as_class=dict):
        """Return the contents of an object as a dict."""
        # make/extend the dictionary of content
        if use_dict is None:
            use_dict = as_class()

        # save the content
        use_dict.__setitem__('dnet', self.rtDNET)
        use_dict.__setitem__('port_id', self.rtPortID)
        use_dict.__setitem__('port_info', self.rtPortInfo)

        # return what we built/updated
        return use_dict

#
#   InitializeRoutingTable
#

class InitializeRoutingTable(NPDU):
    messageType = 0x06
    _debug_contents = ('irtTable++',)

    def __init__(self, routingTable=[], *args, **kwargs):
        super(InitializeRoutingTable, self).__init__(*args, **kwargs)

        self.npduNetMessage = InitializeRoutingTable.messageType
        self.irtTable = routingTable

    def encode(self, npdu):
        NPCI.update(npdu, self)
        npdu.put(len(self.irtTable))
        for rte in self.irtTable:
            npdu.put_short(rte.rtDNET)
            npdu.put(rte.rtPortID)
            npdu.put(len(rte.rtPortInfo))
            npdu.put_data(rte.rtPortInfo)

    def decode(self, npdu):
        NPCI.update(self, npdu)
        self.irtTable = []

        rtLength = npdu.get()
        for i in range(rtLength):
            dnet = npdu.get_short()
            portID = npdu.get()
            portInfoLen = npdu.get()
            portInfo = npdu.get_data(portInfoLen)
            rte = RoutingTableEntry(dnet, portID, portInfo)
            self.irtTable.append(rte)

    def npdu_contents(self, use_dict=None, as_class=dict):
        routing_table = []
        for rte in self.irtTable:
            routing_table.append(rte.dict_contents(as_class=as_class))

        return key_value_contents(use_dict=use_dict, as_class=as_class,
            key_values=(
                ('function', 'InitializeRoutingTable'),
                ('routing_table', routing_table),
            ))

register_npdu_type(InitializeRoutingTable)

#
#   InitializeRoutingTableAck
#

class InitializeRoutingTableAck(NPDU):
    messageType = 0x07
    _debug_contents = ('irtaTable++',)

    def __init__(self, routingTable=[], *args, **kwargs):
        super(InitializeRoutingTableAck, self).__init__(*args, **kwargs)

        self.npduNetMessage = InitializeRoutingTableAck.messageType
        self.irtaTable = routingTable

    def encode(self, npdu):
        NPCI.update(npdu, self)
        npdu.put(len(self.irtaTable))
        for rte in self.irtaTable:
            npdu.put_short(rte.rtDNET)
            npdu.put(rte.rtPortID)
            npdu.put(len(rte.rtPortInfo))
            npdu.put_data(rte.rtPortInfo)

    def decode(self, npdu):
        NPCI.update(self, npdu)
        self.irtaTable = []

        rtLength = npdu.get()
        for i in range(rtLength):
            dnet = npdu.get_short()
            portID = npdu.get()
            portInfoLen = npdu.get()
            portInfo = npdu.get_data(portInfoLen)
            rte = RoutingTableEntry(dnet, portID, portInfo)
            self.irtaTable.append(rte)

    def npdu_contents(self, use_dict=None, as_class=dict):
        routing_table = []
        for rte in self.irtaTable:
            routing_table.append(rte.dict_contents(as_class=as_class))

        return key_value_contents(use_dict=use_dict, as_class=as_class,
            key_values=(
                ('function', 'InitializeRoutingTableAck'),
                ('routing_table', routing_table),
            ))

register_npdu_type(InitializeRoutingTableAck)

#
#   EstablishConnectionToNetwork
#

class EstablishConnectionToNetwork(NPDU):

    _debug_contents = ('ectnDNET', 'ectnTerminationTime')

    messageType = 0x08

    def __init__(self, dnet=None, terminationTime=None, *args, **kwargs):
        super(EstablishConnectionToNetwork, self).__init__(*args, **kwargs)

        self.npduNetMessage = EstablishConnectionToNetwork.messageType
        self.ectnDNET = dnet
        self.ectnTerminationTime = terminationTime

    def encode(self, npdu):
        NPCI.update(npdu, self)
        npdu.put_short( self.ectnDNET )
        npdu.put( self.ectnTerminationTime )

    def decode(self, npdu):
        NPCI.update(self, npdu)
        self.ectnDNET = npdu.get_short()
        self.ectnTerminationTime = npdu.get()

    def npdu_contents(self, use_dict=None, as_class=dict):
        return key_value_contents(use_dict=use_dict, as_class=as_class,
            key_values=(
                ('function', 'EstablishConnectionToNetwork'),
                ('dnet', self.ectnDNET),
                ('termination_time', self.ectnTerminationTime),
            ))

register_npdu_type(EstablishConnectionToNetwork)

#
#   DisconnectConnectionToNetwork
#

class DisconnectConnectionToNetwork(NPDU):

    _debug_contents = ('dctnDNET',)

    messageType = 0x09

    def __init__(self, dnet=None, *args, **kwargs):
        super(DisconnectConnectionToNetwork, self).__init__(*args, **kwargs)

        self.npduNetMessage = DisconnectConnectionToNetwork.messageType
        self.dctnDNET = dnet

    def encode(self, npdu):
        NPCI.update(npdu, self)
        npdu.put_short( self.dctnDNET )

    def decode(self, npdu):
        NPCI.update(self, npdu)
        self.dctnDNET = npdu.get_short()

    def npdu_contents(self, use_dict=None, as_class=dict):
        return key_value_contents(use_dict=use_dict, as_class=as_class,
            key_values=(
                ('function', 'DisconnectConnectionToNetwork'),
                ('dnet', self.dctnDNET),
            ))

register_npdu_type(DisconnectConnectionToNetwork)

#
#   WhatIsNetworkNumber
#

class WhatIsNetworkNumber(NPDU):

    _debug_contents = ()

    messageType = 0x12

    def __init__(self, *args, **kwargs):
        super(WhatIsNetworkNumber, self).__init__(*args, **kwargs)

        self.npduNetMessage = WhatIsNetworkNumber.messageType

    def encode(self, npdu):
        NPCI.update(npdu, self)

    def decode(self, npdu):
        NPCI.update(self, npdu)

    def npdu_contents(self, use_dict=None, as_class=dict):
        return key_value_contents(use_dict=use_dict, as_class=as_class,
            key_values=(
                ('function', 'WhatIsNetworkNumber'),
            ))

register_npdu_type(WhatIsNetworkNumber)

#
#   NetworkNumberIs
#

class NetworkNumberIs(NPDU):

    _debug_contents = ('nniNet', 'nniFlag',)

    messageType = 0x13

    def __init__(self, net=None, flag=None, *args, **kwargs):
        super(NetworkNumberIs, self).__init__(*args, **kwargs)

        self.npduNetMessage = NetworkNumberIs.messageType
        self.nniNet = net
        self.nniFlag = flag

    def encode(self, npdu):
        NPCI.update(npdu, self)
        npdu.put_short( self.nniNet )
        npdu.put( self.nniFlag )

    def decode(self, npdu):
        NPCI.update(self, npdu)
        self.nniNet = npdu.get_short()
        self.nniFlag = npdu.get()

    def npdu_contents(self, use_dict=None, as_class=dict):
        return key_value_contents(use_dict=use_dict, as_class=as_class,
            key_values=(
                ('function', 'NetorkNumberIs'),
                ('net', self.nniNet),
                ('flag', self.nniFlag),
            ))

register_npdu_type(NetworkNumberIs)

