.. BACpypes tcp module

.. module:: tcp

TCP
===

Transmission Control Protocol is wonderful...

Client Classes
--------------

.. class:: TCPClientDirector(Server, ServiceAccessPoint)

    This is a long line of text.

    .. method:: __init__(address, timeout=0, actorClass=UDPActor)

        :param address: the initial source value
        :param timeout: the initial source value
        :param actorClass: the initial source value

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

    .. method:: connect(address, reconnect=0)

        :param address: address to establish a connection
        :param reconnect: timer value

    .. method:: disconnect(address)

        :param address: address to disconnect

    .. method:: indication(pdu)

        This is a long line of text.

.. class:: TCPClient(asyncore.dispatcher)

    .. method:: __init__(peer)

        :param peer: This is a long line of text.

        This is a long line of text.

    .. method:: handle_connect()

        This is a long line of text.

    .. method:: handle_expt()

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

        :param pdu: data to send

        This is a long line of text.

.. class:: TCPClientActor(Logging)

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

    .. method:: handle_close()

        This is a long line of text.

    .. method:: IdleTimeout()

        This is a long line of text.

    .. method:: indication(pdu)

        :param pdu: the initial source value

        This is a long line of text.

    .. method:: response(pdu)

        :param pdu: the initial source value

        This is a long line of text.

    .. method:: Flush()

        This is a long line of text.

.. class:: TCPPickleClientActor(PickleActorMixIn, TCPClientActor)

    This is a long line of text.

Server Classes
--------------

.. class:: TCPServerDirector(asyncore.dispatcher, Server, ServiceAccessPoint)

    .. method:: __init__(address, listeners=5, timeout=0, reuse=False, actorClass=TCPServerActor)

        :param address: socket for connection
        :param listeners: socket for connection
        :param timeout: socket for connection
        :param reuse: socket for connection
        :param actorClass: socket for connection

        This is a long line of text.

    .. method:: handle_accept()

        This is a long line of text.

    .. method:: handle_close()

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

    .. method:: indication(pdu)

        This is a long line of text.

.. class:: TCPServer(asyncore.dispatcher)

    .. method:: __init__(sock, peer)

        :param sock: socket for connection
        :param peer: This is a long line of text.

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

        :param pdu: data to send

        This is a long line of text.

.. class:: TCPServerActor(TCPServer)

    This is a long line of text.

    .. attribute:: director

        This is a long line of text.

    .. attribute:: peer

        This is a long line of text.

    .. attribute:: timeout

        This is a long line of text.

    .. attribute:: timer

        This is a long line of text.

    .. method:: __init__(director, sock, peer)

        :param director: the initial source value
        :param sock: socket for connection
        :param peer: the initial destination value

        This is a long line of text.

    .. method:: handle_close()

        This is a long line of text.

    .. method:: IdleTimeout()

        This is a long line of text.

    .. method:: indication(pdu)

        :param pdu: the initial source value

        This is a long line of text.

    .. method:: response(pdu)

        :param pdu: the initial source value

        This is a long line of text.

    .. method:: Flush()

        This is a long line of text.

.. class:: TCPPickleServerActor(PickleActorMixIn, TCPServerActor)

    This is a long line of text.

Streaming Packets
-----------------

.. class:: StreamToPacket(Client, Server)

    .. method:: Packetize(pdu, streamBuffer)

        This is a long line of text.

    .. method:: indication(pdu)

        This is a long line of text.

    .. method:: confirmation(pdu)

        This is a long line of text.

.. class:: StreamToPacketSAP(ApplicationServiceElement, ServiceAccessPoint)

    .. indication(addPeer=None, delPeer=None)

Stream Pickling
---------------

.. class:: PickleActorMixIn

    .. method:: indication(pdu)

        :param pdu: the initial source value

        This is a long line of text.

    .. method:: response(pdu)

        :param pdu: the initial source value

        This is a long line of text.
