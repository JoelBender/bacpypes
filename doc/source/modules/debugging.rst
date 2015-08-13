.. BACpypes debugging module

.. module:: debugging

Debugging
=========

All applications use some kind of debugging.

Globals
-------

.. data:: _root

    This is a long line of text.

Functions
---------

.. function:: ModuleLogger(globs)

    :param globs: dictionary of module globals

    This function, posing as an instance creator, returns a ...

Function Decorators
-------------------

.. function:: function_debugging

    This function decorates a function with instances of buggers that are
    named by the function name combined with the module name.  It is used like
    this::

        @function_debugging
        def some_function(arg):
            if _debug: some_function._debug("some_function %r", arg)
            # rest of code

    This results in a bugger called **module.some_function** that can be
    accessed by that name when attaching log handlers.

    .. note::
        This should really be called **debug_function** or something
        like that.

Classes
-------

.. class:: DebugContents

    This is a long line of text.

    .. attribute:: _debug_contents

        This is a long line of text.

    .. method:: debug_contents(indent=1, file=sys.stdout, _ids=None)

        :param indent: function to call
        :param file: regular arguments to pass to fn
        :param _ids: keyword arguments to pass to fn
    
        This is a long line of text.

.. class:: LoggingFormatter(logging.Formatter)

    This is a long line of text.

    .. method:: __init__()

        This is a long line of text.

    .. method:: format(record)

        :param logging.LogRecord record: record to format

        This function converts the record into a string.  It uses
        the regular formatting function that it overrides, then 
        if any of the parameters inherit from :class:`DebugContents`
        (or duck typed by providing a **debug_contents** function) the 
        message is extended with the deconstruction of those parameters.

.. class:: Logging

    This is a long line of text.

    .. note::
        Now that Python supports class decorators, this should really be a
        class decorator called **debug_class** or something
        like that.
