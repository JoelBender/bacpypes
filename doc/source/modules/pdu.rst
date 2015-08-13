.. BACpypes pdu module

.. module:: pdu

BACnet Protocol Data Units
==========================

This is a long line of text.


Addressing
----------

.. class:: Address

    This is a long line of text.

    .. attribute:: addrType

        This is a long line of text.

    .. attribute:: addrNet

        This is a long line of text.

    .. attribute:: addrLen

        This is a long line of text.

    .. attribute:: addrAddr

        This is a long line of text.

    .. method:: decode_address(addr)

        :param string addr: address specification to interpret

        This is a long line of text.

    .. method:: __str__

    .. method:: __repr__

        This method overrides the built-in function to provide a little bit
        better string, using *__str__* for help.

    .. method:: __hash__

        This method is used to allow addresses to be used as keys in
        dictionaries which require keys to be hashable.

        .. note::

            Once an address is used in a dictionary is should be considered
            immutable.

    .. method:: __eq__(arg)
                __ne__(arg)

        :param arg: another address, or something that can be interpreted as an address

        This is a long line of text.

.. class:: LocalStation(Address)

    This is a long line of text.

.. class:: RemoteStation(Address)

    This is a long line of text.

.. class:: LocalBroadcast(Address)

    This is a long line of text.

.. class:: RemoteBroadcast(Address)

    This is a long line of text.

.. class:: GlobalBroadcast(Address)

    This is a long line of text.

Extended PCI
------------

This is a long line of text.

.. class:: PCI(_PCI)

    This is a long line of text.

    .. attribute:: pduExpectingReply

        This is a long line of text.

    .. attribute:: pduNetworkPriority

        This is a long line of text.

.. class:: PDU(PCI, PDUData)

    This is a long line of text.
