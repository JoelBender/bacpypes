.. BACpypes tutorial lesson 3

Protocol Data Units
===================

According to `Wikipedia <http://en.wikipedia.org/wiki/Protocol_data_unit>`_ a
*Protocol Data Unit* (PDU) is

    Information that is delivered as a unit among peer entities of a network 
    and that may contain control information, address information, or data.

BACpypes uses a slight variation of this definition in that it bundles the 
address information with the control information.  It considers addressing as  
part of how the data should be delivered, along with other concepts like how
important the PDU data is relative to other PDUs.

The basic components of a PDU are the :class:`comm.PCI` and
:class:`comm.PDUData` classes which are then bundled together to form the
:class:`comm.PDU` class.

All of the protocol interpreters written in the course of 
developing BACpypes have a concept of source and
destination.  The :class:`comm.PCI` defines only two attributes, **pduSource**
and **pduDestination**.

.. note::

    Master/slave networks, are an exception.  Messages sent by the master, contain 
    only the destination (the source is implicit).  Messages returned by the slaves 
    have no addressing (both the source, and destination are implicit).
     
As a foundation layer, there are no restrictions on the form of the source and
destination, they could be integers, strings or even objects.  In general, 
the :class:`comm.PDU` class is used as a base class for a series of stack 
specific components.  UDP traffic have combinations of IP addresses and
port numbers as source and destination, then that will be inherited by something
that provides more control information, like delivery order or priority.


Exploring PDU's
---------------

Begin with importing the base class::

    >>> from bacpypes.comm import PDU

Create a new PDU with some simple content::

    >>> pdu = PDU(b"hello")

.. caution::

    If you are not using Python 3, you don't need to specify the bytes type.
    >>> pdu = PDU("Hello")

We can then see the contents of the PDU as it will be seen on the network 
wire and by Wireshark - as a sequence of octets (printed as hex encoded strings)::

    >>> pdu.debug_contents()
        pduData = x'68.65.6C.6C.6F'

Now lets add some source and destination addressing information, so the message 
can be sent somewhere::

    >>> pdu.pduSource = 1
    >>> pdu.pduDestination = 2
    >>> pdu.debug_contents()
        pduSource = 1
        pduDestination = 2
        pduData = x'68.65.6c.6c.6f'

Of course, we could have provided the addressing information when we created the PDU::

    >>> pdu = PDU(b"hello", source=1, destination=2)
    >>> pdu.debug_contents()
        pduSource = 1
        pduDestination = 2
        pduData = x'68.65.6C.6C.6F'

.. tip::

    It is customary to allow missing attributes (be it protocol control
    information or data) as this allows the developer to mix keyword 
    parameters with post-init attribute assignments.


BACnet PDUs
-----------

The basic PDU definition is fine for many protocols, but BACnet has two
additional protocol parameters, described as attributes of the BACnet PCI
information.

The :class:`pdu.PCI` class extends the basic PCI with **pduExpectingReply** and
**pduNetworkPriority**.  The former is only used in MS/TP networks so the 
node generating the request will not pass the token before waiting some amount
of time for a response, and the latter is a hint to routers, and devices
with priority queues for network traffic, that a PDU is more or less important.

These two fields are assigned at the application layer and travel with the PDU
as it travels through the stack.

Encoding and Decoding
---------------------

The encoding and decoding process consists of consuming content from the source
PDU and generating content in the destination.  BACpypes *could* have used some
kind of "visitor" pattern so the process did not consume the source, but 
typically when a layer has finished with PDU it will be sending some different PDU
upstream or downstream so once the layer is finished, the PDU is not re-visited.

.. note::

    This concept, where an object like a PDU is passed off to another
    function and is no longer "owned" by the builder, is difficult to
    accomplish in language environments without automatic
    garbage collection, but tremendiously simplifies our interpreter code.

PDUs nest the control information of one level into the data portion of the
next level.  So when decoding on the way up, it is customary to
pass the control information along, even when it isn't strictly necessary.

The :func:`pdu.PCI.update` function is an example of a method that is used
the way a "copy" operation might be used.  The PCI classes, and nested versions
of them, usually have an update function.

Decoding
+++++++++

Decoding always consumes some number of octets from the front of the PDU data.  
Lets create a pdu and then use decoding to consume it::

    >>> pdu=PDU(b'hello!!')
    >>> pdu.debug_contents()
        pduData = x'68.65.6c.6c.6f.21.21'

Consume 1 octet (x'68 = decimal 104'):: 

    >>> pdu.get()
    104
    >>> pdu.debug_contents()
        pduData = x'65.6c.6c.6f.21.21'

Consume a short integer (two octets)::

    >>> pdu.get_short()
    25964
    >>> pdu.debug_contents()
        pduData = x'6c.6f.21.21'
    
Consume a long integer (four octets)::

    >>> pdu.get_long()
    1819222305
    >>> pdu.debug_contents()
        pduData = x''
    >>> 
    
And the PDU is now empty!

Encoding
+++++++++

We can then build the PDU contents back up through a series of *put* operations. 
A *put* is an implicit append operation::

    >>> pdu.debug_contents()
        pduData = x''
    >>> pdu.put(108)
    >>> pdu.debug_contents()
        pduData = x'6c'

    >>> pdu.put_short(25964)
    >>> pdu.debug_contents()
        pduData = x'6c.65.6c'

    >>> pdu.put_long(1819222305)
    >>> pdu.debug_contents()
        pduData = x'6c.65.6c.6c.6f.21.21'

.. note::

    There is no distinction between a PDU that is being taken apart (by get) 
    and one that is being built up (by put).
    