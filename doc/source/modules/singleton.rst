.. BACpypes core module

.. module:: singleton

Singleton
=========

Singleton classes are a `design pattern <http://en.wikipedia.org/wiki/Singleton_pattern>`_
which returns the same object for every 'create an instance' call.  In the case
of BACpypes there can only be one instance of a :class:`task.TaskManager` and
all of the tasks are scheduled through it.  The design pattern "hides" all
of the implementation details of the task manager behind its interface.

There are occasions when the task manager needs to provide additional
functionality, or a derived class would like a change to intercept the methods.
In this case the developer can create a subclass of :class:`TaskManager`, then
create an instance of it.  Every subsequent call to get a task manager will
return this special instance.

Classes
-------

.. class:: Singleton

    By inheriting from this class, all calls to build an object will return
    the same object.

.. class:: SingletonLogging

    This special class binds together the metaclasses from both this singleton
    module and from the :class:`debugging.Logging`.  Python classes cannot
    inherit from two separate metaclasses at the same time, but this class takes
    advantage of Pythons ability to have multiple inheritance of metaclasses.
