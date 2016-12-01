.. BACpypes tutorial lesson 2

Stacking with Debug
===================

This tutorial uses the same :class:`comm.Client`, :class:`comm.Server` classes
from the previous one, so continuing on from previous tutorial, all we need is 
to import the class:`comm.Debug`::

    >>> from bacpypes.comm import Debug

Because there could be lots of **Debug** instances, it could be confusing if you
didn't know which instance was generating the output.  So initialize the debug 
instance with a name::

    >>> d = Debug("middle")

As you can guess, this is going to go into the middle of a :term:`stack` of
objects.  The *top* of the stack is a client, then *bottom* of a stack is a
server.  When messages are flowing from clients to servers they are called
:term:`downstream` messages, and when they flow from server to client they 
are :term:`upstream` messages.

The :func:`comm.bind` function takes an arbitrary number of objects.  It 
assumes that the first one will always be a client, the last one is a server, 
and the objects in the middle are hybrids which can be
bound with the client to its left, and to the server on its right::

    >>> bind(c, d, s)

Now when the client generates a request, rather than the message being sent
to the MyServer instance, it is sent to the debugging instance, which  
prints out that it received the message::

    >>> c.request('hi')
    Debug(middle).indication
        - args[0]: hi

The debugging instance then forwards the message to the server, which prints 
its message.  Completeing the requests *downstream* journey.::

    working on hi

The server then generates a reply.  The reply moves *upstream* from the server, 
through the debugging instance, this time as a confirmation::

    Debug(middle).confirmation
        - args[0]: HI

Which is then forwarded *upstream* to the client::

    thanks for the HI

This demonstrates how requests first move *downstream* from client to server; then 
cause the generation of replies that move *upstream* from server to client; and how the 
debug instance in the middle sees the messages moving both ways.
 
With clearly defined "envelopes" of protocol data, matching the combination of
clients and servers into layers can provide a clear separation of functionality
in a protocol stack.
