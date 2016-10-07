.. BACpypes IO control block module

.. module:: iocb

IO Control Block
================

The IO Control Block (IOCB) is a data structure that is used to store parameters
for some kind of processing and then used to retrieve the results of that
processing at a later time.  An IO Controller (IOController) is the executor
of that processing.

They are modeled after the VAX/VMS IO subsystem API in which a single function
could take a wide variety of combinations of parameters and the application
did not necessarily wait for the operation to complete, but could be notified
when it was by an event flag or semaphore.  It could also provide a callback
function to be called when processing was complete.

For example, given a simple function call::

    result = some_function(arg1, arg2, kwarg1=1)

The IOCB would contain the arguments and keyword arguments, the some_function()
would be the controller, and the result would alo be stored in the IOCB when
the function is complete.

If the IOController encountered an error during processing, some value specifying
the error is also stored in the IOCB.

Classes
-------

There are two fundamental classes in this module, the :class:`IOCB` for bundling
request parameters together and processing the result, and :class:`IOController`
for executing requests.

The :class:`IOQueue` is an object that manages a queue of IOCB requests when
some functionality needs to be processed one at a time, and an :class:`IOQController`
which has the same signature as an IOController but takes advantage of a queue.

The :class:`IOGroup` is used to bundle a collection of requests together that
may be processed by separate controllers at different times but has `wait()`
and `add_callback()` functions and can be otherwise treated as an IOCB.

.. class:: IOCB

    The IOCB contains a unique identifier, references to the arguments and
    keyword arguments used when it was constructed, and placeholders for
    processing results or errors.

    .. attribute:: ioID

        Every IOCB has a unique identifier that persists for the lifetime of
        the block.  Similar to the Invoke ID for confirmed services, it can be used
        to synchronize communications and related functions.
    
        The default identifier value is a thread safe monotonically increasing
        value.

    .. attribute:: args, kwargs

        These are copies of the arguments and keyword arguments passed during the
        construction of the IOCB.

    .. attribute:: ioState

        The ioState of an IOCB is the state of processing for the block.
    
            * *idle* - an IOCB is idle when it is first constructed and before it has been given to a controller.
            * *pending* - the IOCB has been given to a controller but the processing of the request has not started.
            * *active* - the IOCB is being processed by the controller.
            * *completed* - the processing of the IOCB has completed and the positive results have been stored in `ioResponse`.
            * *aborted* - the processing of the IOCB has encountered an error of some kind and the error condition has been stored in `ioError`.

    .. attribute:: ioResponse

        The result that some controller is providing to the application that
        created the IOCB.

    .. attribute:: ioError

        The error condition that the controller is providing when the processing
        resulted in an error.    

    .. method:: __init__(*args, **kwargs)

        :param args: arbitrary arguments
        :param kwargs: arbitrary keyword arguments

        Create an IOCB and store the arguments and keyword arguments in it.  The
        IOCB will be given a unique identifier and start in the *idle* state.

    .. method:: complete(msg)

        :param msg: positive result of request

    .. method:: abort(msg)

        :param msg: negative results of request

    .. method:: trigger()

        This method is called by complete() or abort() after the positive or
        negative result has been stored in the IOCB.

    .. method:: wait(*args)

        :param args: arbitrary arguments

        Block until the IO operation is complete and the positive or negative
        result has been placed in the ICOB.  The arguments are passed to the
        `wait()` function of the ioComplete event.

    .. method:: add_callback(fn, *args, **kwargs)

        :param fn: the function to call when the IOCB is triggered
        :param args: additional arguments passed to the function
        :param kwargs: additional keyword arguments passed to the function

        Add the function `fn` to a list of functions to call when the IOCB is
        triggered because it is complete or aborted.  When the function is
        called the first parameter will be the IOCB that was triggered.

        An IOCB can have any number of callback functions added to it and they
        will be called in the order they were added to the IOCB.

        If the IOCB is has already been triggered then the callback function
        will be called immediately.  Callback functions are typically added
        to an IOCB before it is given to a controller.

    .. method:: set_timeout(delay, err=TimeoutError)

        :param seconds delay: the time limit for processing the IOCB
        :param err: the error to use when the IOCB is aborted

        Set a time limit on the amount of time an IOCB can take to be completed,
        and if the time is exceeded then the IOCB is aborted.

.. class:: IOController

    An IOController is an API for processing an IOCB.  It has one method
    `process_io()` provided by a derived class which will be called for each IOCB
    that is requested of it.  It calls one of its `complete_io()` or `abort_io()`
    functions as necessary to satisfy the request.

    This class does not restrict a controller from processing more than one
    IOCB simultaneously.

    .. method:: request_io(iocb)

        :param iocb: the IOCB to be processed

        This method is called by the application requesting the service of a
        controller.

    .. method:: process_io(iocb)

        :param iocb: the IOCB to be processed

        The implementation of `process_io()` should be written using "functional
        programming" principles by not modifying the arguments or keyword arguments
        in the IOCB, and without side effects that would require the application
        using the controller to submit IOCBs in a particular order.  There may be
        occasions following a "remote procedure call" model where the application
        making the request is not in the same process, or even on the same machine,
        as the controller providing the functionality.

    .. method:: active_io(iocb)

        :param iocb: the IOCB being processed

        This method is called by the derived class when it would like to signal
        to other types of applications that the IOCB is being processed.

    .. method:: complete_io(iocb, msg)

        :param iocb: the IOCB to be processed
        :param msg: the message to be returned

        This method is called by the derived class when the IO processing is
        complete.  The `msg`, which may be None, is put in the `ioResponse`
        attribute of the IOCB which is then triggered.

        IOController derived classes should call this function rather than
        the `complete()` function of the IOCB.

    .. method:: abort_io(iocb, msg)

        :param iocb: the IOCB to be processed
        :param msg: the error to be returned

        This method is called by the derived class when the IO processing has
        encountered an error.  The `msg` is put in the `ioError`
        attribute of the IOCB which is then triggered.

        IOController derived classes should call this function rather than
        the `abort()` function of the IOCB.

    .. method:: abort(err)

        :param msg: the error to be returned

        This method is called to abort all of the IOCBs associated with the
        controller.  There is no default implementation of this method.

.. class:: IOQueue

    An IOQueue is simply a first-in-first-out priority queue of IOCBs, but the
    IOCBs are modified to know that they can been queued.  If an IOCB is aborted
    before being retrieved from the queue, it will ask the queue to remove it.

    .. method:: put(iocb)

        :param iocb: add an IOCB to the queue

    .. method:: get(block=1, delay=None)

        :param block: wait for an IOCB to be available in the queue
        :param delay: maximum time to wait for an IOCB

        The `get()` request returns the next IOCB in the queue and waits for one
        if there are none available.  If `block` is false and the queue is
        empty, it will return None.

    .. method:: remove(iocb)

        :param iocb: an IOCB to remove from the queue

        Removes an IOCB from the queue.  If the IOCB is not in the queue, no
        action is performed.

    .. method:: abort(err)

        :param msg: the error to be returned

        This method is called to abort all of the IOCBs in the queue.

.. class:: IOQController

    An `IOQController` has an identical interface as the `IOContoller`, but
    provides additional hooks to make sure that only one IOCB is being processed
    at a time.

    .. method:: request_io(iocb)

        :param iocb: the IOCB to be processed

        This method is called by the application requesting the service of a
        controller.  If the controller is already busy processing a request,
        this IOCB is queued until the current processing is complete.

    .. method:: process_io(iocb)

        :param iocb: the IOCB to be processed

        Provided by a derived class, this is identical to `IOController.process_io`.

    .. method:: active_io(iocb)

        :param iocb: the IOCB to be processed

        Called by a derived class, this is identical to `IOController.active_io`.

    .. method:: complete_io(iocb, msg)

        :param iocb: the IOCB to be processed

        Called by a derived class, this is identical to `IOController.complete_io`.

    .. method:: abort_io(iocb, msg)

        :param iocb: the IOCB to be processed

        Called by a derived class, this is identical to `IOController.abort_io`.

    .. method:: abort(err)

        :param msg: the error to be returned

        This method is called to abort all of the IOCBs associated with the
        controller.  All of the pending IOCBs will be aborted with this error.        

.. class:: IOGroup(IOCB)

    An `IOGroup` is like a set that is an IOCB.  The group will complete
    when all of the IOCBs that have been added to the group are complete.

    .. method:: add(iocb)

        :param iocb: an IOCB to include in the group

        Adds an IOCB to the group.

    .. method:: abort(err)

        :param err: the error to be returned

        This method is call to abort all of the IOCBs that are members of
        the group.

    .. method:: group_callback(iocb)

        : param iocb: the member IOCB that has completed

        This method is added as a callback to all of the IOCBs that are added
        to the group and it is called when each one completes.  Its purpose
        is to check to see if all of the IOCBs have completed and if they
        have, trigger the group as completed.

.. class:: IOChainMixIn

    The IOChainMixIn class adds an additional API to things that act like
    an IOCB and can be mixed into the inheritance chain for translating
    requests from one form to another.

    .. method:: __init__(iocb)

        :param iocb: the IOCB to chain from

        Create an object that is chained from some request.

    .. method:: encode()

        This method is called to transform the arguments and keyword arguments
        into something suitable for the other controller.  It is typically
        overridden by a derived class to perform this function.

    .. method:: decode()

        This method is called to transform the result or error returned by
        the other controller into something suitable to return.  It is typically
        overridden by a derived class to perform this function.

    .. method:: chain_callback(iocb)

        :param iocb: the IOCB that has completed, which is itself

        When a chained IOCB has completed, the results are translated or
        decoded for the next higher level of the application.  The `iocb`
        parameter is redundant because the IOCB becomes its own controller,
        but the callback API requires the parameter.

    .. method:: abort_io(iocb, err)

        :param iocb: the IOCB that is being aborted
        :param err: the error to be used as the abort reason

        Call this method to abort the IOCB, which will in turn cascade the
        abort operation to the chained IOCBs.  This has the same function
        signature that is used by an IOController because this instance
        becomes its own controller.

.. class:: IOChain(IOCB, IOChainMixIn)

    An IOChain is a class that is an IOCB that includes the IOChain API.
    Chains are used by controllers when they need the services of some other
    controller and results need to be processed further.

    Controllers that operate this way are similar to an adapter, they take
    arguments in one form, encode them in some way in an IOCB, pass it to the
    other controller, then decode the results.

.. class:: ClientController(Client, IOQController)

    An instance of this class is a controller that sits at the top of a
    protocol stack as a client.  The IOCBs to be processed contain a single
    PDU parameter that is sent down the stack.  Any PDU coming back up
    the stack is assumed to complete the current request.

    This class is used for protocol stacks with a strict master/slave
    architecture.

    This class inherits from `IOQController` so if there is already an active
    request then subsequent requests are queued.

.. class:: _SieveQueue(IOQController)

    This is a special purpose controller used by the `SieveClientController`
    to serialize requests for the same source/destination address.

.. class:: SieveClientController(Client, IOController)

    Similar to the `ClientController`, this class is a controller that also
    sits at the top of a protocol stack as a client.  The IOCBs to be processed
    contain a single PDU parameter with a `pduDestination` address.  Unlike
    the `ClientController`, this class creates individual queues for each
    destination address so it can process multiple requests simultaneously while
    maintaining a strict master/slave relationship with each address.

    When an upstream PDU is received, the `pduSource` address is used to
    associate this response with the correct request.

Functions
---------

.. function:: register_controller(controller)

    :param controller: controller to register

    The module keeps a dictionary of "registered" controllers so that other
    parts of the application can find the controller instance.  For example,
    if an HTTP controller provided a GET service and it was registered then
    other parts of the application could take advantage of the service the
    controller provides.
