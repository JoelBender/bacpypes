#!/usr/bin/python

"""
PDU
"""

import re
import socket
import struct

try:
    import netifaces
except ImportError:
    netifaces = None

from .debugging import ModuleLogger, bacpypes_debugging, btox, xtob
from .comm import PCI as _PCI, PDUData

# pack/unpack constants
_short_mask = 0xFFFFL
_long_mask = 0xFFFFFFFFL

# some debugging
_debug = 0
_log = ModuleLogger(globals())

#
#   Address
#

ip_address_mask_port_re = re.compile(r'^(?:(\d+):)?(\d+\.\d+\.\d+\.\d+)(?:/(\d+))?(?::(\d+))?$')
ethernet_re = re.compile(r'^([0-9A-Fa-f][0-9A-Fa-f][:]){5}([0-9A-Fa-f][0-9A-Fa-f])$' )
interface_re = re.compile(r'^(?:([\w]+))(?::(\d+))?$')

@bacpypes_debugging
class Address:
    nullAddr = 0
    localBroadcastAddr = 1
    localStationAddr = 2
    remoteBroadcastAddr = 3
    remoteStationAddr = 4
    globalBroadcastAddr = 5

    def __init__(self, *args):
        if _debug: Address._debug("__init__ %r", args)
        self.addrType = Address.nullAddr
        self.addrNet = None
        self.addrLen = 0
        self.addrAddr = b''

        if len(args) == 1:
            self.decode_address(args[0])
        elif len(args) == 2:
            self.decode_address(args[1])
            if self.addrType == Address.localStationAddr:
                self.addrType = Address.remoteStationAddr
                self.addrNet = args[0]
            elif self.addrType == Address.localBroadcastAddr:
                self.addrType = Address.remoteBroadcastAddr
                self.addrNet = args[0]
            else:
                raise ValueError("unrecognized address ctor form")

    def decode_address(self, addr):
        """Initialize the address from a string.  Lots of different forms are supported."""
        if _debug: Address._debug("decode_address %r (%s)", addr, type(addr))

        # start out assuming this is a local station
        self.addrType = Address.localStationAddr
        self.addrNet = None

        if addr == "*":
            if _debug: Address._debug("    - localBroadcast")

            self.addrType = Address.localBroadcastAddr
            self.addrNet = None
            self.addrAddr = None
            self.addrLen = None

        elif addr == "*:*":
            if _debug: Address._debug("   - globalBroadcast")

            self.addrType = Address.globalBroadcastAddr
            self.addrNet = None
            self.addrAddr = None
            self.addrLen = None

        elif isinstance(addr, int):
            if _debug: Address._debug("    - int")
            if (addr < 0) or (addr >= 256):
                raise ValueError("address out of range")

            self.addrAddr = struct.pack('B', addr)
            self.addrLen = 1

        elif isinstance(addr, str):
            if _debug: Address._debug("    - str")

            m = ip_address_mask_port_re.match(addr)
            if m:
                if _debug: Address._debug("    - IP address")

                net, addr, mask, port = m.groups()
                if not mask: mask = '32'
                if not port: port = '47808'
                if _debug: Address._debug("    - net, addr, mask, port: %r, %r, %r, %r", net, addr, mask, port)

                if net:
                    net = int(net)
                    if (net >= 65535):
                        raise ValueError("network out of range")
                    self.addrType = Address.remoteStationAddr
                    self.addrNet = net

                self.addrPort = int(port)
                self.addrTuple = (addr, self.addrPort)

                addrstr = socket.inet_aton(addr)
                self.addrIP = struct.unpack('!L', addrstr)[0]
                self.addrMask = (_long_mask << (32 - int(mask))) & _long_mask
                self.addrHost = (self.addrIP & ~self.addrMask)
                self.addrSubnet = (self.addrIP & self.addrMask)

                bcast = (self.addrSubnet | ~self.addrMask)
                self.addrBroadcastTuple = (socket.inet_ntoa(struct.pack('!L', bcast & _long_mask)), self.addrPort)

                self.addrAddr = addrstr + struct.pack('!H', self.addrPort & _short_mask)
                self.addrLen = 6

            elif ethernet_re.match(addr):
                if _debug: Address._debug("    - ethernet")

                self.addrAddr = xtob(addr, ':')
                self.addrLen = len(self.addrAddr)

            elif re.match(r"^\d+$", addr):
                if _debug: Address._debug("    - int")

                addr = int(addr)
                if (addr > 255):
                    raise ValueError("address out of range")

                self.addrAddr = struct.pack('B', addr)
                self.addrLen = 1

            elif re.match(r"^\d+:[*]$", addr):
                if _debug: Address._debug("    - remote broadcast")

                addr = int(addr[:-2])
                if (addr >= 65535):
                    raise ValueError("network out of range")

                self.addrType = Address.remoteBroadcastAddr
                self.addrNet = addr
                self.addrAddr = None
                self.addrLen = None

            elif re.match(r"^\d+:\d+$",addr):
                if _debug: Address._debug("    - remote station")

                net, addr = addr.split(':')
                net = int(net)
                addr = int(addr)
                if (net >= 65535):
                    raise ValueError("network out of range")
                if (addr > 255):
                    raise ValueError("address out of range")

                self.addrType = Address.remoteStationAddr
                self.addrNet = net
                self.addrAddr = struct.pack('B', addr)
                self.addrLen = 1

            elif re.match(r"^0x([0-9A-Fa-f][0-9A-Fa-f])+$",addr):
                if _debug: Address._debug("    - modern hex string")

                self.addrAddr = xtob(addr[2:])
                self.addrLen = len(self.addrAddr)

            elif re.match(r"^X'([0-9A-Fa-f][0-9A-Fa-f])+'$",addr):
                if _debug: Address._debug("    - old school hex string")

                self.addrAddr = xtob(addr[2:-1])
                self.addrLen = len(self.addrAddr)

            elif re.match(r"^\d+:0x([0-9A-Fa-f][0-9A-Fa-f])+$",addr):
                if _debug: Address._debug("    - remote station with modern hex string")

                net, addr = addr.split(':')
                net = int(net)
                if (net >= 65535):
                    raise ValueError("network out of range")

                self.addrType = Address.remoteStationAddr
                self.addrNet = net
                self.addrAddr = xtob(addr[2:])
                self.addrLen = len(self.addrAddr)

            elif re.match(r"^\d+:X'([0-9A-Fa-f][0-9A-Fa-f])+'$",addr):
                if _debug: Address._debug("    - remote station with old school hex string")

                net, addr = addr.split(':')
                net = int(net)
                if (net >= 65535):
                    raise ValueError("network out of range")

                self.addrType = Address.remoteStationAddr
                self.addrNet = net
                self.addrAddr = xtob(addr[2:-1])
                self.addrLen = len(self.addrAddr)

            elif netifaces and interface_re.match(addr):
                interface, port = interface_re.match(addr).groups()
                if port is not None:
                    self.addrPort = int(port)
                else:
                    self.addrPort = 47808

                interfaces = netifaces.interfaces()
                if interface not in interfaces:
                    raise ValueError("not an interface: %s" % (interface,))

                ifaddresses = netifaces.ifaddresses(interface)
                if netifaces.AF_INET not in ifaddresses:
                    raise ValueError("interface does not support IPv4: %s" % (interface,))

                ipv4addresses = ifaddresses[netifaces.AF_INET]
                if len(ipv4addresses) > 1:
                    raise ValueError("interface supports multiple IPv4 addresses: %s" % (interface,))
                ifaddress = ipv4addresses[0]

                addr = ifaddress['addr']
                self.addrTuple = (addr, self.addrPort)

                addrstr = socket.inet_aton(addr)
                self.addrIP = struct.unpack('!L', addrstr)[0]

                if 'netmask' in ifaddress:
                    maskstr = socket.inet_aton(ifaddress['netmask'])
                    self.addrMask = struct.unpack('!L', maskstr)[0]
                else:
                    self.addrMask = _long_mask

                self.addrHost = (self.addrIP & ~self.addrMask)
                self.addrSubnet = (self.addrIP & self.addrMask)

                if 'broadcast' in ifaddress:
                    self.addrBroadcastTuple = (ifaddress['broadcast'], self.addrPort)
                else:
                    self.addrBroadcastTuple = None

                self.addrAddr = addrstr + struct.pack('!H', self.addrPort & _short_mask)
                self.addrLen = 6

            else:
                raise ValueError("unrecognized format")

        elif isinstance(addr, tuple):
            addr, port = addr
            self.addrPort = int(port)

            if isinstance(addr, str):
                if not addr:
                    # when ('', n) is passed it is the local host address, but that
                    # could be more than one on a multihomed machine, the empty string
                    # means "any".
                    addrstr = b'\0\0\0\0'
                else:
                    addrstr = socket.inet_aton(addr)
                self.addrTuple = (addr, self.addrPort)

            elif isinstance(addr, (int, long)):
                addrstr = struct.pack('!L', addr & _long_mask)
                self.addrTuple = (socket.inet_ntoa(addrstr), self.addrPort)

            else:
                raise TypeError("tuple must be (string, port) or (long, port)")
            if _debug: Address._debug("    - addrstr: %r", addrstr)

            self.addrIP = struct.unpack('!L', addrstr)[0]
            self.addrMask = _long_mask
            self.addrHost = None
            self.addrSubnet = None
            self.addrBroadcastTuple = self.addrTuple

            self.addrAddr = addrstr + struct.pack('!H', self.addrPort & _short_mask)
            self.addrLen = 6

        else:
            raise TypeError("integer, string or tuple required")

    def __str__(self):
        if self.addrType == Address.nullAddr:
            return 'Null'

        elif self.addrType == Address.localBroadcastAddr:
            return '*'

        elif self.addrType == Address.localStationAddr:
            rslt = ''
            if self.addrLen == 1:
                rslt += str(ord(self.addrAddr))
            else:
                port = struct.unpack('!H', self.addrAddr[-2:])[0]
                if (len(self.addrAddr) == 6) and (port >= 47808) and (port <= 47823):
                    rslt += '.'.join(["%d" % ord(x) for x in self.addrAddr[0:4]])
                    if port != 47808:
                        rslt += ':' + str(port)
                else:
                    rslt += '0x' + btox(self.addrAddr)
            return rslt

        elif self.addrType == Address.remoteBroadcastAddr:
            return '%d:*' % (self.addrNet,)

        elif self.addrType == Address.remoteStationAddr:
            rslt = '%d:' % (self.addrNet,)
            if self.addrLen == 1:
                rslt += str(ord(self.addrAddr[0]))
            else:
                port = struct.unpack('!H', self.addrAddr[-2:])[0]
                if (len(self.addrAddr) == 6) and (port >= 47808) and (port <= 47823):
                    rslt += '.'.join(["%d" % ord(x) for x in self.addrAddr[0:4]])
                    if port != 47808:
                        rslt += ':' + str(port)
                else:
                    rslt += '0x' + btox(self.addrAddr)
            return rslt

        elif self.addrType == Address.globalBroadcastAddr:
            return '*:*'

        else:
            raise TypeError("unknown address type %d" % self.addrType)

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.__str__())

    def __hash__(self):
        return hash( (self.addrType, self.addrNet, self.addrAddr) )

    def __eq__(self,arg):
        # try an coerce it into an address
        if not isinstance(arg, Address):
            arg = Address(arg)

        # all of the components must match
        return (self.addrType == arg.addrType) and (self.addrNet == arg.addrNet) and (self.addrAddr == arg.addrAddr)

    def __ne__(self,arg):
        return not self.__eq__(arg)

    def dict_contents(self, use_dict=None, as_class=None):
        """Return the contents of an object as a dict."""
        if _debug: _log.debug("dict_contents use_dict=%r as_class=%r", use_dict, as_class)

        # exception to the rule of returning a dict
        return str(self)

#
#   pack_ip_addr, unpack_ip_addr
#

def pack_ip_addr(addr):
    """Given an IP address tuple like ('1.2.3.4', 47808) return the six-octet string
    useful for a BACnet address."""
    addr, port = addr
    return socket.inet_aton(addr) + struct.pack('!H', port & _short_mask)

def unpack_ip_addr(addr):
    """Given a six-octet BACnet address, return an IP address tuple."""
    return (socket.inet_ntoa(addr[0:4]), struct.unpack('!H', addr[4:6])[0])

#
#   LocalStation
#

class LocalStation(Address):

    def __init__(self, addr):
        self.addrType = Address.localStationAddr
        self.addrNet = None

        if isinstance(addr, int):
            if (addr < 0) or (addr >= 256):
                raise ValueError("address out of range")

            self.addrAddr = struct.pack('B', addr)
            self.addrLen = 1

        elif isinstance(addr, (bytes, bytearray)):
            if _debug: Address._debug("    - bytes or bytearray")

            self.addrAddr = bytes(addr)
            self.addrLen = len(addr)

        else:
            raise TypeError("integer, bytes or bytearray required")

#
#   RemoteStation
#

class RemoteStation(Address):

    def __init__(self, net, addr):
        if not isinstance(net, int):
            raise TypeError("integer network required")
        if (net < 0) or (net >= 65535):
            raise ValueError("network out of range")

        self.addrType = Address.remoteStationAddr
        self.addrNet = net

        if isinstance(addr, int):
            if (addr < 0) or (addr >= 256):
                raise ValueError("address out of range")

            self.addrAddr = struct.pack('B', addr)
            self.addrLen = 1

        elif isinstance(addr, (bytes, bytearray)):
            if _debug: Address._debug("    - bytes or bytearray")

            self.addrAddr = bytes(addr)
            self.addrLen = len(addr)

        else:
            raise TypeError("integer, bytes or bytearray required")

#
#   LocalBroadcast
#

class LocalBroadcast(Address):

    def __init__(self):
        self.addrType = Address.localBroadcastAddr
        self.addrNet = None
        self.addrAddr = None
        self.addrLen = None

#
#   RemoteBroadcast
#

class RemoteBroadcast(Address):

    def __init__(self, net):
        if not isinstance(net, int):
            raise TypeError("integer network required")
        if (net < 0) or (net >= 65535):
            raise ValueError("network out of range")

        self.addrType = Address.remoteBroadcastAddr
        self.addrNet = net
        self.addrAddr = None
        self.addrLen = None

#
#   GlobalBroadcast
#

class GlobalBroadcast(Address):

    def __init__(self):
        self.addrType = Address.globalBroadcastAddr
        self.addrNet = None
        self.addrAddr = None
        self.addrLen = None

#
#   PCI
#

@bacpypes_debugging
class PCI(_PCI):

    _debug_contents = ('pduExpectingReply', 'pduNetworkPriority')

    def __init__(self, *args, **kwargs):
        if _debug: PCI._debug("__init__ %r %r", args, kwargs)

        # split out the keyword arguments that belong to this class
        my_kwargs = {}
        other_kwargs = {}
        for element in ('expectingReply', 'networkPriority'):
            if element in kwargs:
                my_kwargs[element] = kwargs[element]
        for kw in kwargs:
            if kw not in my_kwargs:
                other_kwargs[kw] = kwargs[kw]
        if _debug: PCI._debug("    - my_kwargs: %r", my_kwargs)
        if _debug: PCI._debug("    - other_kwargs: %r", other_kwargs)

        # call some superclass, if there is one
        super(PCI, self).__init__(*args, **other_kwargs)

        # set the attribute/property values for the ones provided
        self.pduExpectingReply = my_kwargs.get('expectingReply', 0)     # see 6.2.2 (1 or 0)
        self.pduNetworkPriority = my_kwargs.get('networkPriority', 0)   # see 6.2.2 (0..3)

    def update(self, pci):
        """Copy the PCI fields."""
        _PCI.update(self, pci)

        # now do the BACnet PCI fields
        self.pduExpectingReply = pci.pduExpectingReply
        self.pduNetworkPriority = pci.pduNetworkPriority

    def pci_contents(self, use_dict=None, as_class=dict):
        """Return the contents of an object as a dict."""
        if _debug: PCI._debug("pci_contents use_dict=%r as_class=%r", use_dict, as_class)

        # make/extend the dictionary of content
        if use_dict is None:
            use_dict = as_class()

        # call the parent class
        _PCI.pci_contents(self, use_dict=use_dict, as_class=as_class)

        # save the values
        use_dict.__setitem__('expectingReply', self.pduExpectingReply)
        use_dict.__setitem__('networkPriority', self.pduNetworkPriority)

        # return what we built/updated
        return use_dict

    def dict_contents(self, use_dict=None, as_class=dict):
        """Return the contents of an object as a dict."""
        if _debug: PCI._debug("dict_contents use_dict=%r as_class=%r", use_dict, as_class)

        return self.pci_contents(use_dict=use_dict, as_class=as_class)

#
#   PDU
#

@bacpypes_debugging
class PDU(PCI, PDUData):

    def __init__(self, *args, **kwargs):
        if _debug: PDU._debug("__init__ %r %r", args, kwargs)
        super(PDU, self).__init__(*args, **kwargs)

    def __str__(self):
        return '<%s %s -> %s : %s>' % (self.__class__.__name__, self.pduSource, self.pduDestination, btox(self.pduData,'.'))

    def dict_contents(self, use_dict=None, as_class=dict):
        """Return the contents of an object as a dict."""
        if _debug: PDUData._debug("dict_contents use_dict=%r as_class=%r", use_dict, as_class)

        # make/extend the dictionary of content
        if use_dict is None:
            use_dict = as_class()

        # call into the two base classes
        self.pci_contents(use_dict=use_dict, as_class=as_class)
        self.pdudata_contents(use_dict=use_dict, as_class=as_class)

        # return what we built/updated
        return use_dict

