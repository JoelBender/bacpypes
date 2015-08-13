.. BACpypes event module

.. module:: event

Event
=====

At the heart of :func:`core.run()` is a call to the **select** function of the
built in select module.  That function is provided a list of file descriptors
and will exit when there is activity on one of them.

In a multi-threaded application, if the main thread is waiting for IO activity
then child threads need a mechanism to "wake up" the main thread.  This may be
because the child thread has detected some timeout.

An instance of this class is used by the :class:`task.TaskManager` to wake up
the main thread when tasks are scheduled by child threads.  If the child thread
is requesting "as soon as possible" execution of the task, then scheduling the
task wakes up the main thread, which causes it to be processed.

.. note::
    This is not available on Windows platforms, which may suffer from a small
    preformance hit.  This can be mitigated somewhat by changing the **SPIN**
    value in the **core** module.

Classes
-------

.. class:: WaitableEvent

    The methods in this class provide the same interface as
    **asyncore.file_dispatcher** and the ones that are typically used
    in multi-threaded applications the way **Threading.Event** objects
    are used.

    These methods use an internal pipe to provide a "read" and "write" file
    descriptors.  There are no direct references to this pipe, only through
    the file descriptors that are linked to it.

    .. method:: __init__()

        The internal file descriptors which are understood by the
        **asyncore.loop** call in :func:`core.run()` are created by
        calling **os.pipe()**, then initialization continues to
        the usual **asyncore.file_dispatcher** initializer.

    .. method:: __del__()

        When an instance of this class is deleted, the file references to the
        "read" and "write" sides of the pipe are closed.  The OS will then 
        delete the pipe.

    .. method:: readable()

        This method returns ``True`` so it will always be included in the
        list of file-like objects when waiting for IO activity.

    .. method:: writable()

        This method returns ``False`` becuase there is never any pending
        write activity like there would be for a actual file or socket.

    .. method:: handle_read()

        This method performs no activity.  If an instance of this event
        is "set" then the only way to clear it is by calling :func:`clear()`
        which will read the pending character out of the pipe.

    .. method:: handle_write()

        This function is never called because :func:`writable()` always
        returns ``False``.

    .. method:: handle_close()

        This method is called when a close is requested, so this in 
        turn passes it to the **asyncore.file_dispatcher.close** function.

    .. method:: wait(timeout=None)

        :param float timeout: maximum time to wait for the event to be set

        Similar to the way the **asyncore.loop** function will wait for 
        activity on a file descriptor, **select.select** is used by this
        method to wait for some activity on the "read" side of its internal
        pipe.

        The :func:`set()` function will write to the "write" side of the pipe,
        so the "read" side will have activity and the select function will
        exit.

        This function returns ``True`` if the "event" is "set".

    .. method:: isSet()

        This method calls :func:`wait()` with a zero timeout which essentially
        probes the pipe to see if there is data waiting, which in turn implies
        the "event" is "set".

    .. method:: set()

        Setting the event involves writing a single character to the internal
        pipe, but only if there is no data in the pipe.

    .. method:: clear()

        Clearing the event involves reading the character that was written to
        the intrenal pipe, provided one is there.  If there is no data in the
        pipe then the **os.read** function would stall the thread.
