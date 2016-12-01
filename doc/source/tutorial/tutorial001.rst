.. BACpypes tutorial lesson 1

Clients and Servers
===================

While exploring a library like BACpypes, take full advantage of Python being
an interpreted language with an interactive prompt!  The code for this tutorial
is also available in the *Tutorial* subdirectory of the repository.

This tutorial will be using :class:`comm.Client`, :class:`comm.Server` classes,
and the :func:`comm.bind` function, so start out by importing them::

    >>> from bacpypes.comm import Client, Server, bind

Since the server needs to do something when it gets a request, it 
needs to provide a function to get it::

    >>> class MyServer(Server):
    ...     def indication(self, arg):
    ...         print('working on', arg)
    ...         self.response(arg.upper())
    ... 

Now create an instance of this new class and bind the client and server together::

    >>> c = Client()
    >>> s = MyServer()
    >>> bind(c, s)

This only solves the downstream part of the problem, as you can see::

    >>> c.request('hi')
    ('working on ', 'hi')
    Traceback....
    ....
    NotImplementedError: confirmation must be overridden

So now we create a custom client class that does something with the response::

    >>> class MyClient(Client):
    ...     def confirmation(self, pdu):
    ...         print('thanks for the ', pdu)
    ... 

Create an instance of it, bind the client and server together and test it::

    >>> c = MyClient()
    >>> bind(c, s)
    >>> c.request('hi')
    ('working on ', 'hi')
    ('thanks for ', 'HI')

Success!
