.. BACpypes IOCB tutorial

Controllers and IOCB
====================

The IO Control Block (IOCB) is an object that holds the parameters for some
kind of operation or function and a place for the result.  The IOController
processes the IOCBs it is given and returns the IOCB back to the caller.

For this tutorial section, import the IOCB and IOController::

    >>> from bacpypes.iocb import IOCB, IOController

Building an IOCB
----------------

Build an IOCB with some arguments and keyword arguments::

    >>> iocb = IOCB(1, 2, a=3)

The parameters are kept for processing::

    >>> iocb.args
    (1, 2)
    >>> iocb.kwargs
    {'a': 3}

Make a Controller
-----------------

Now we need a controller to process this request.  This controller is just
going to add and multiply the arguments together::

    class SomeController(IOController):

        def process_io(self, iocb):
            self.complete_io(iocb, iocb.args[0] + iocb.args[1] * iocb.kwargs['a'])

Now create an instance of the controller and pass it the request::

    >>> some_controller = SomeController()
    >>> some_controller.request_io(iocb)

First, you'll notice that `request_io()` was called rather than the processing
function directly.  This intermediate layer between the caller of the service
and the thing providing the service can be detached from each other in a
variety of different ways.

For example, there are some types of controllers that can only process one
request at a time and these are derived from `IOQController`.  If the application
layer requests IOCB processing faster than the controller can manage (perhaps
because it is waiting for some networking functions) the requests will be queued.

In other examples, the application making the request is in a different process
or on a different machine, so the `request_io()` function builds a remote
procedure call wrapper around the request and manages the response.  This is
similar to an HTTP proxy server.

Similarly, inside the controller it calls `self.complete_io()` so if there is
some wrapper functionality the code inside the `process_io()` function doesn't
need to worry about it.

Check the Result
----------------

There are a few ways to check to see if an IOCB has been processed.  Every
IOCB has an `Event` from the `threading` built in module, so the application
can check to see if the event is set::

    >>> iocb.ioComplete
    <threading._Event object at 0x101349590>
    >>> iocb.ioComplete.is_set()
    True

There is also an IOCB state which has one of a collection of enumerated values::

    >>> import bacpypes
    >>> iocb.ioState == bacpypes.iocb.COMPLETED
    True

And the state could also be aborted::

    >>> iocb.ioState == bacpypes.iocb.ABORTED
    False

Almost all controllers return some kind of information back to the requestor
in the form of some data.  In this example, it's just a number::

    >>> iocb.ioResponse
    7

But we can provide some invalid combination of arguments and the exception
will show up in the `ioError`::

    >>> iocb = IOCB(1, 2)
    >>> some_controller.request_io(iocb)
    >>> iocb.ioError
    KeyError('a',)

The types of results and errors depend on the controller.

Getting a Callback
------------------

When a controller completes the processing of a request, the IOCB can contain
one or more functions to be called.  First, define a callback function::

    def call_me(iocb):
        print("call me, %r or %r" % (iocb.ioResponse, iocb.ioError))

Now create a request and add the callback function::

    >>> iocb = IOCB(1, 2, a=10)
    >>> iocb.add_callback(call_me)

Pass the IOCB to the controller and the callback function is called::

    >>> some_controller.request_io(iocb)
    call me, 21 or None

Threading
---------

The IOCB module is thread safe, but the IOController derived classes may
not be.  The thread initiating the request to the controller may simply
wait for the completion event to be set::

    >>> some_controller.request_io(iocb)
    >>> iocb.ioComplete.wait()

But for this to work correctly, the IOController must be running in a
separate thread, or there won't be any way for the event to be set.

If the iocb has callback functions, they will be executed in the thread
context of the controller.
