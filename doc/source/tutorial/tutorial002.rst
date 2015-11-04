.. BACpypes tutorial lesson 2

Stacking with Debug
===================

This tutorial uses the same :class:`comm.Client`, :class:`comm.Server` classes
from the previous one, so continuing on all it needs is the :class:`comm.Debug`
class, so import it::

    >>> from bacpypes.comm import Debug

Because there could be lots of Debug instances, it could be confusing if you
didn't know which instance was generating the output.  So you can initialize
an instance with a lobel::

    >>> d = Debug("middle")

As you can guess, this is going to go into the middle of a :term:`stack` of
objects.  The *top* of the stack is a client, then *bottom* of a stack is a
server.  When messages are flowing from clients to servers they are called
:term:`downstream` messages, and when they go from server to the client they go
:term:`upstream`.

The :func:`comm.bind` function takes an arbitrary number of objects, but it 
assumes that the first one will always be a client, the last one is a server, 
and that the objects in the middle are both a kind of server that can be
bound with the client to its left in the parameter list, and a client that can
be bound to a server to its right::

    >>> bind(c, d, s)

Now when the client generates a request, rather than the message being sent
to the MyServer instance, it is sent to the debugging instance.  That is acting
as a server, so it prints out that it received an indication::

    >>> c.request('hi')
    Debug(middle).indication
        - args[0]: hi

Now it acts as a client and forwards it down to the server in the stack.  That
generates a print statement and responds with the string uppercase::

    working on hi

Upstream from the server is the debugging instance again, this time as a 
confirmation::

    Debug(middle).confirmation
        - args[0]: HI

Now it acts as a server and continues the response up the stack, which is 
printed out by the client::

    thanks for the HI

With clearly defined "envelopes" of protocol data, matching the combination of
clients and servers into layers can provide a clear separation of functionality
in a protocol stack.
