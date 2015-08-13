.. BACpypes udp module

.. module:: udp

UDP
===

User Datagram Protocol is wonderful...

Classes
-------

.. class:: UDPDirector(asyncore.dispatcher, Server, ServiceAccessPoint, Logging)

    This is a long line of text.

    .. method:: __init__(self, address, timeout=0, actorClass=UDPActor, sid=None, sapID=None)

        :param address: the initial source value
        :param timeout: the initial source value
        :param actorClass: the initial source value
        :param sid: the initial source value
        :param sapID: the initial source value

        This is a long line of text.

    .. method:: AddActor(actor)

        :param actor: the initial source value

        This is a long line of text.

    .. method:: RemoveActor(actor)

        :param actor: the initial source value

        This is a long line of text.

    .. method:: GetActor(address)

        :param address: the initial source value

        This is a long line of text.

    .. method:: handle_connect()

        This is a long line of text.

    .. method:: readable()

        This is a long line of text.

    .. method:: handle_read()

        This is a long line of text.

    .. method:: writable()

        This is a long line of text.

    .. method:: handle_write()

        This is a long line of text.

    .. method:: handle_close()

        This is a long line of text.

    .. method:: indication(pdu)

        This is a long line of text.

    .. method:: _response(pdu)

.. class:: UDPActor(Logging)

    This is a long line of text.

    .. attribute:: director

        This is a long line of text.

    .. attribute:: peer

        This is a long line of text.

    .. attribute:: timeout

        This is a long line of text.

    .. attribute:: timer

        This is a long line of text.

    .. method:: __init__(director, peer)

        :param director: the initial source value
        :param peer: the initial destination value

        This is a long line of text.

    .. method:: IdleTimeout()

        This is a long line of text.

    .. method:: indication(pdu)

        :param pdu: the initial source value

        This is a long line of text.

    .. method:: response(pdu)

        :param pdu: the initial source value

        This is a long line of text.

.. class:: UDPPickleActor(UDPActor, Logging)

    .. method:: indication(pdu)

        :param pdu: the initial source value

        This is a long line of text.

    .. method:: response(pdu)

        :param pdu: the initial source value

        This is a long line of text.
