.. BACpypes analysis module

.. module:: analysis

Analysis of PCAP Files
======================

This is a long line of text.

Functions
---------

.. function:: strftimestamp(ts)

    :param ts: timestamp

    This is a long line of text.

Decoders
--------

This is a long line of text.

.. function:: decode_ethernet(s)

    :param s: packet string

    This is a long line of text.

.. function:: decode_vlan(s)

    :param s: packet string

    This is a long line of text.

.. function:: decode_ip(s)

    :param s: packet string

    This is a long line of text.

.. function:: decode_udp(s)

    :param s: packet string

    This is a long line of text.

.. function:: decode_udp(s)

    :param s: packet string

    This is a long line of text.

.. function:: decode_packet(s)

    :param s: packet string

    This is a long line of text.

.. function:: decode_file(fname)

    :param name: pcap file name

    This is a long line of text.

Tracing
-------

This is a long line of text.

.. class:: Tracer

    .. attribute:: currentState

        This is a long line of text.

    .. method:: __init__(initialState=None)

        :param initialState: initial state function

        This is a long line of text.

    .. method:: Start(pkt)

        :param pkt: packet

        This is a long line of text.

    .. method:: Next(pkt)

        :param pkt: packet

        This is a long line of text.

.. function:: trace(fname, tracers)

    :param fname: pcap file name
    :param tracers: list of tracer classes

    This is a long line of text.

