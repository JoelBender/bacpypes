.. BACpypes core module

.. module:: core

Core
====

All applications have to have some kind of outer blcok.

Globals
-------

.. data:: running

    This is a boolean that the application is running.  It can be turned off
    by an application, but the :func:`stop` function is usually used.

.. data:: taskManager

    This is a reference to the :class:`TaskManager` instance that is used 
    to schedule some operation.  There is only one task manager instance in
    an application.

.. data:: deferredFns

    This is a list of function calls to make after all of the asyncore.loop
    processing has completed.  This is a list of (fn, args, kwargs) tuples
    that are appended to the list by the :func:`deferred` function.

.. data:: sleeptime

    This value is used to "sleep" the main thread for a certian amount of 
    before continuing on to the asyncore loop.  It is used to be friendly 
    to other threads that may be starved for processing time.  See 
    :func:`enable_sleeping`.

Functions
---------

.. function:: run()

    This function is called by a BACpypes application after all of its
    initialization is complete.

.. function:: stop(*args)

    :param args: optional signal handler arguments

    This function is called to stop a BACpypes application.  It resets the
    :data:`running` boolean value.  This function also installed as a 
    signal handler responding to the TERM signal so you can stop a background
    (deamon) process::

        $ kill -TERM 12345

.. function:: print_stack(sig, frame)

    :param sig: signal
    :param frame: stack trace frame

.. function:: deferred(fn, *args, **kwargs)

    :param fn: function to call
    :param args: regular arguments to pass to fn
    :param kwargs: keyword arguments to pass to fn

    This function is called to postpone a function call until after the 
    asyncore.loop processing has completed.  See :func:`run`.

.. function:: enable_sleeping([stime])

    :param stime: amount of time to sleep, defaults to one millisecond

    BACpypes applications are generally written as a single threaded 
    application, the stack is not thread safe.  However, applications may
    use threads at the application layer and above for other types of work.
    This function allows the main thread to sleep for some small amount of 
    time so that it does not starve child threads of processing time.

    When sleeping is enabled, and it only needs to be enabled for multithreaded
    applications, it will put a damper on the throughput of the application.
