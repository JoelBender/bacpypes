.. BACpypes tutorial lesson 4

Addressing
==========

BACnet addresses come in five delicious flavors:

local station 
    A message addressed to one device on the same network as the originator.

local broadcast
    A message addressed to all devices or nodes on the same network as the originator.

remote station
    A message addressed to one device on a different network than the originator.

remote broadcast
    A message addressed to all devices or nodes on a different network than the originator.
    
global broadcast
    A message addressed to all devices or nodes on all networks known any device on any network.

BACpypes address objects are used as the source and destination for PDUs and
are also keys to dictionaries for looking up device in information and
organizing requests and responses with devices.

Building an Address
-------------------

The Address class other related classes are in the pdu module.

Local Stations
~~~~~~~~~~~~~~

The Address class is the base class from which the other classes are derived,
but for this tutorial, we'll start with the simplest::

    >>> from bacpypes.pdu import LocalStation

Local station addresses are one or more octets of binary data.  For the
simplest networks they are a single octet, for Ethernet and BACnet/IP they
are six octets long.  There is no restriction on the length of an address in
BACpypes.

A local station address is contructed by passing the octet string as bytes or
a byte array, and their string representation is hex notation::

    >>> addr1 = Address(b'123456')
    >>> print(addr1)
    0x313233343536
    
For local stations on simple networks the constructor will accept unsigned
integers with the simple string output::

    >>> addr2 = Address(12)
    >>> print(addr2)
    12

The underlying components of the address are always byte strings::

    >>> addr1.addrAddr
    b'123456'
    >>> addr1.addrAddr
    b'\x01'

When the byte string is six octets long and the next to last octet is 0xBA and
the last octet is in the range 0xC0 to 0xCF, the string output and repr value
will be presented as an IPv4 address::

    >>> LocalStation(b'\1\2\3\4\xba\xc0')
    <LocalStation 1.2.3.4>

and it will include the port number if it is not the standard port::

    >>> LocalStation(b'\1\2\3\4\xba\xc3')
    <LocalStation 1.2.3.4:47811>

Local Broadcast
~~~~~~~~~~~~~~~

The local broadcast address is used in the destination of a PDU that is to be
sent to all of the devices on a network, and if the network layer can detect
if it received a PDU as the result of another station broadcasting it.  There
are no parameters for constructing one::

    >>> from bacpypes.pdu import LocalBroadcast
    >>> print(LocalBroadcast())
    *

The string output represents any address.

Remote Station
~~~~~~~~~~~~~~

A remote station address is used in BACnet networking when the source and/or
destination is on a network other than the one considered local.  The first
parameter is the network number, which must be a valid BACnet network number,
and the second parameter is a byte string or unsigned integer like the local
station::

    >>> from bacpypes.pdu import RemoteStation
    >>> print(RemoteStation(15, 75))
    15:75
    >>> print(RemoteStation(15, b'123456'))
    15:0x313233343536

The string output is the network number and address separated by a colon.

Remote Broadcast
~~~~~~~~~~~~~~~~

A remote broadcast station is used as a destination address when sending a PDU
to all of the devices on a remote network.  The only constructor parameter is
the network number, which must be a valid BACnet network number:

    >>> from bacpypes.pdu import RemoteBroadcast
    >>> print(RemoteBroadcast(17))
    17:*

The string output is the network number number, a colon, and an asterisk for
any address.

GlobalBroadcast
~~~~~~~~~~~~~~~

The global broadcast address is used to send PDUs to all devices.  It has no
constructor parameters::

    >>> from bacpypes.pdu import GlobalBroadcast
    >>> print(GlobalBroadcast())
    *:*

The string output is an asterisk for any network, a colon, and an asterisk for
and address.

Address Parsing
---------------

The basic Address class can parse the string form of all of the address types
and a few more for older applications and notation that has appeared in
other tutorials.

.. note::
    The Address class cannot "morph" into an instance of one of its subclasses
    so to determine what kind of address it is check the addrType attribute.

For example::

    >>> from bacpypes.pdu import Address
    >>> Address(1).addrType == Address.localStationAddr
    True

And addresses created this way are identical::

    >>> Address(1) == LocalStation(b'\01')
    True

Unlike the LocalStation, the Address can take the string form of an integer::

    >>> Address("2") == LocalStation(b'\02')
    True

And can interpret hex strings of various types::

    >>> Address("0x0304") == LocalStation(b'\3\4')
    True
    >>> Address("X'050607'") == LocalStation(b'\5\6\7')
    True

It interprets the asterisk as a local broadcast::

    >>> Address("*") == LocalBroadcast()
    True

And remote stations and remote broadcasts mathing the other output::

    >>> Address("1:2") == RemoteStation(1, 2)
    True
    >>> Address("3:*") == RemoteBroadcast(3)
    True

And the global broadcast::

    >>> Address("*:*") == GlobalBroadcast()
    True

IPv4 Addresses
~~~~~~~~~~~~~~

Because they appear so often, the address parsing has special patterns for
recognizing IPv4 addresses in CIDR notation along with an optional port
number::

    >>> Address("192.168.1.2").addrAddr
    b'\xc0\xa8\x01\x02\xba\xc0'

    >>> Address("192.168.1.2:47809").addrAddr
    b'\xc0\xa8\x01\x02\xba\xc1'

For addresses that also include a subnet mask to calculate broadcast addresses,
the CIDR notation is available::

    >>> hex(Address("192.168.3.4/24").addrSubnet)
    '0xc0a80300'

And for calculating the address tuple for use with socket functions::

    >>> Address("192.168.5.6/16").addrBroadcastTuple
    ('192.168.255.255', 47808)

