.. BACpypes vlan module

.. module:: vlan

Virtual LAN
===========

This is a long line of text.

.. class:: Network

    This is a long line of text.

    .. attribute:: nodes

        This is a long line of text.

    .. attribute:: dropPercent

        This is a long line of text.

    .. attribute:: addrLen

        This is a long line of text.

    .. attribute:: addrAddr

        This is a long line of text.

    .. method:: __init__(addr, dropPercent=0.0)

        :param float dropPercent: percentage of packets to drop

        This is a long line of text.

    .. method:: add_node(node)

        :param Node node: node to add to the network

        This is a long line of text.

    .. method:: remove_node(node)

        :param Node node: node to remove from the network

        This is a long line of text.

    .. method:: process_pdu(pdu)

        :param pdu: pdu to send on the network

        This is a long line of text.

    .. method:: __len__

        Simple mechanism to return the number of nodes on the network.

.. class:: Node

    This is a long line of text.

    .. method:: __init__(addr, lan=None, promiscuous=False, spoofing=False)

        :param Address addr: address for the node
        :param Network lan: network reference
        :param boolean promiscuous: receive all packets
        :param boolean spoofing: send with mocked source address

        This is a long line of text.

    .. method:: bind(lan)

        :param Network lan: network reference

        This is a long line of text.

    .. method:: indication(pdu)

        :param pdu: pdu to send on the network

        This is a long line of text.
