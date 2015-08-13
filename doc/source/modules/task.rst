.. BACpypes task module

.. module:: task

Task
====

A **task** is something that needs to be done.  Tasks come in a variety of 
flavors:

* :class:`OneShotTask` - do something once
* :class:`OneShotDeleteTask` - do something once, then delete the task object
* :class:`RecurringTask` - do something at regular intervals

Every derived class of one of these classes must provide a `process_task` method
which will be called at the next opportunity available to the application.
All task processing is expected to be cooperative, which means that it must
be written so that it is cognizant that other tasks may also be waiting for a 
chance to be processed.

Tasks are *installed* when they should be scheduled for processing, may be 
*suspended* or removed from scheduling, and then may be *resumed* or
re-installed.

Singleton Task Manager
----------------------

All operations involving tasks are directed to a single instance of
:class:`TaskManager` or an instance of a derived class.  If the developer
creates a derived class of :class:`TaskManager` and an instance of it *before*
the :func:`core.run()` function is called, that instance will be used to 
schedule tasks and return the next task to process.

Globals
-------

.. data:: _task_manager

    This is a long line of text.

.. data:: _unscheduled_tasks

    This is a long line of text.

Functions
---------

.. function:: OneShotFunction(fn, *args, **kwargs)

    :param fn: function to schedule
    :param args: function to schedule
    :param kwargs: function to schedule

    This is a long line of text.

.. function:: FunctionTask(fn, *args, **kwargs)

    :param fn: function to update

    This is a long line of text.

.. function:: RecurringFunctionTask(interval, fn, *args, **kwargs)

    :param fn: function to update

    This is a long line of text.

Function Decorators
-------------------

.. function:: recurring_function(interval)

    :param interval: interval to call the function

    This function will return a decorator which will wrap a function in a task
    object that will be called at regular intervals and can also be called 
    as a function.  For example::

        @recurring_function(5000)
        def my_ping(arg=None):
            print "my_ping", arg

    The my_ping object is a task that can be installed, suspended, and resumed
    like any other task.  This is installed to run every 5s and will print::

        my_ping None

    And can also be called as a regular function with parameters, so calling
    my_ping("hello") will print::

        my_ping hello

Classes
-------

.. class:: _Task

    This is a long line of text.

    .. method:: install_task(when=None)

        :param float when: time task should be processed

        This is a long line of text.

    .. method:: process_task()

        :param float when: time task should be processed

        This is a long line of text.

    .. method:: suspend_task()

        :param float when: time task should be processed

        This is a long line of text.

    .. method:: resume_task()

        :param float when: time task should be processed

        This is a long line of text.

.. class:: OneShotTask

    This is a long line of text.

.. class:: OneShotDeleteTask

    This is a long line of text.

.. class:: RecurringTask

    This is a long line of text.

.. class:: TaskManager

    This is a long line of text.

    .. method:: install_task(task)

        :param task: task to be installed

        This is a long line of text.

    .. method:: suspend_task(task)

        :param task: task to be suspended

        This is a long line of text.

    .. method:: resume_task(task)

        :param task: task to be resumed

        This is a long line of text.

    .. method:: get_next_task()

        This is a long line of text.

    .. method:: process_task()

        This is a long line of text.

