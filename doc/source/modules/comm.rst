.. BACpypes comm module

.. module:: comm

Comm
====

All applications have to have some kind of outer blcok.

Globals
-------

.. data:: client_map

    This is ...

.. data:: server_map

    This is ...

.. data:: service_map

    This is ...

.. data:: element_map

    This is ...

Functions
---------

.. function:: bind(*args)

    :param args: a list of clients and servers to bind together in a stack

Protocol Data Units
-------------------

A Protocol Data Unit (PDU) is the name for a collection of information that
is passed between two entities.  It is composed of Protcol Control Information
(PCI) - information about addressing, processing instructions - and data.  
The set of classes in this module are not specific to BACnet.

.. class:: PCI

    .. attribute:: pduSouce

        The source of a PDU.  The datatype and composition of the address is
        dependent on the client/server relationship and protocol context.  The
        source may be `None`, in which case it has no source or the source is
        implicit.

    .. attribute:: pduDestination

        The destination of a PDU.  The datatype and composition of the address
        is dependent on the client/server relationship and protocol context.
        The destination may be `None`, in which case it has no destination or the
        destination is implicit.

    .. method:: __init__([source=addr][,destination=addr])

        :param addr source: the initial source value
        :param addr destination: the initial destination value

    Protocol Control Information is generally the context information and/or
    other types of processing instructions.

.. class:: PDUData

    The PDUData class has functions for extracting information from the front
    of the data octet string, or append information to the end.  These are helper
    functions but may not be applicable for higher layer protocols which may
    be passing significantly more complex data.

    .. attribute:: pduData

        This attribute typically holds a simple octet string, but for higher
        layers of a protocol stack it may contain more abstract pieces or
        components.

    .. method:: get()

        Extract a single octet from the front of the data.  If the octet string
        is empty this will raise a DecodingError.

    .. method:: get_data(len)

        :param integer len: the number of octets to extract.

        Extract a number of octets from the front of the data.  If there
        are not at least `len` octets this will raise a DecodingError
        exception.

    .. method:: get_short()
    
        Extract a short integer (two octets) from the front of the data.

    .. method:: get_long()

        Extract a long integer (four octets) from the front of the data.

    .. method:: put(ch)

        :param octet ch: the octet to append to the end

    .. method:: put_data(data)

        :param string data: the octet string to append to the end

    .. method:: put_short(n)

        :param short integer: two octets to append to the end

    .. method:: put_long(n)

        :param long integer: four octets to append to the end


.. class:: PDU(PCI, PDUData)

    The PDU class combines the PCI and PDUData classes together into one
    object.

Protocol Stack Classes
----------------------

.. class:: Client

.. class:: Server

.. class:: Debug

.. class:: Echo

Application Classes
-------------------

.. class:: ServiceAccessPoint

.. class:: ApplicationServiceElement

.. class:: NullServiceElement

.. class:: DebugServiceElement

