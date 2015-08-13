.. BACpypes tutorial lesson 3

Protocol Data Units
===================

According to `Wikipedia <http://en.wikipedia.org/wiki/Protocol_data_unit>`_ a
*Protocol Data Unit* (PDU) is

    Information that is delivered as a unit among peer entities of a network 
    and that may contain control information, address information, or data.

BACpypes uses a slght variation of this definition in that it bundles the 
address information in with the control information.  It considers addressing 
part of how the data should be delivered, along with other concepts like how
important the PDU data is relative to other PDUs.

The basic components of a PDU are the :class:`comm.PCI` and
:class:`comm.PDUData` classes which are then bundled together to form the
:class:`comm.PDU` class.

All of the protocol interpreters that have been written in the course of 
developing BACpypes have all had at least some concept of source and
destination.  The :class:`comm.PCI` defines only two attributes, **pduSource**
and **pduDestination**.

Only in the case of pure master/slave networks has only the destination
encoded by the master to direct it to a specific slave (so source information 
is implicit and not encoded) and the response from the slave back to the master
(so no addressing is included at all).  These special cases are rare.

As a foundation layer, there are no restrictions on the form of the source and
destination, they could be integers, strings or even objects.  In general, 
the :class:`comm.PDU` class is used as a base class for a series of stack 
specific components, so UDP traffic will have combinations of IP addresses and
port numbers as source and destination, then that will be inherited by something
that provides more control information, like delivery order or priority.

Beginning with the base class::

    >>> from bacpypes.comm import PDU

While source and destination are defined in the PCI, they are optional keyword
parameters.  Debugging the contents of the PDU will skip over those attributes
that are ``None`` and strings are assumed to be a sequence of octets and so
are printed as hex encoded strings::

    >>> pdu = PDU("hello")
    >>> pdu.debug_contents()
        pduData = x'68.65.6C.6C.6F'

Now add some source and destination information::

    >>> pdu = PDU("hello", source=1, destination=2)
    >>> pdu.debug_contents()
        pduSource = 1
        pduDestination = 2
        pduData = x'68.65.6C.6C.6F'

It is customary to allow missing attributes (which is protocol control
information or it would be data) to allow the developer to mixed keyword 
parameters and post-init attribute assignment.

BACnet PDUs
-----------

The PDU definition in the core is fine for many protocols, but BACnet has two
additional protocol parameters, described as attributes of a BACnet PCI
information.

The :class:`pdu.PCI` class extends the basic PCI with **pduExpectingReply** and
**pduNetworkPriority**.  The former is only used in MS/TP networks so the 
node generating the request will not pass the token before waiting some amount
of time for a response, and the latter is a hint to routers and other deivces
with priority queues for network traffic that a PDU is more or less important.

These two fields are set at the application layer and travel with the PDU
content as it travels down the stack.

Encoding and Decoding
---------------------

The encoding and decoding process consists of consuming content from the source
PDU and generating content in the destination.  BACpypes *could* have used some
kind of "visitor" pattern so the process did not consume the source, but 
typically when a layer has finished with PDU and will be sending some other PDU
upstream or downstream and once that PDU leaves the layer it is not re-visited.

.. note::

    This concept, where an object like a PDU is passed off to some other
    function and it is no longer "owned" by the builder, is difficult to
    accomplish in language and runtime environments that do not have automatic
    garbage collection.  It tremendiously simplifies interpreter code.

PDUs nest the control infommation of one level into the data portion of the
next level down, and when decoding on the way up a stack it is customary to
pass the control information along, even when it isn't strictly necessary.

The :func:`pdu.PCI.update` function is an example of a method that is used
the way a "copy" operation might be used.  The PCI classes, and nested versions
of them, usually have an update function.

Decoding consumes some number of octets from the front of the PDU data::

    >>> pdu = PDU("hello!!")
    >>> pdu.get()
    104
    >>> pdu.get_short()
    25964
    >>> pdu.get_long()
    1819222305

And the PDU is now empty::

    >>> pdu.debug_contents()
        pduData = x''

But the contents can be put back, an implicit append operation::

    >>> pdu.put(104)
    >>> pdu.put_short(25964)
    >>> pdu.put_long(1819222305)
    >>> pdu.debug_contents()
        pduData = x'68.65.6C.6C.6F.21.21'

.. note::

    There is no distinction between a PDU that is being used as the source
    to some interpretation process and one that is the destination.  Earlier
    versions of this library made that distinction and the type casting
    and type conversion code became an impediment to understanding the 
    interpretation, so it was dropped.
