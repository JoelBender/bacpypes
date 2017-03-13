.. BACpypes change detection module

.. module:: detect

Detect
======

This is a long line of text.

Classes
-------


.. class:: DetectionMonitor

    .. attribute:: algorithm
    .. attribute:: parameter
    .. attribute:: obj
    .. attribute:: prop
    .. attribute:: filter

    .. method:: __init__(algorithm, parameter, obj, prop, filter=None)

        This is a long line of text.

    .. method:: property_change(old_value, new_value)

        This is a long line of text.

.. class:: DetectionAlgorithm

    .. attribute:: _monitors

        This private attribute is a list of `DetectionMonitor` objects that
        associate this algorithm instance with objects and properties.

    .. attribute:: _triggered

        This private attribute is `True` when there is a change in a parameter
        which causes the algorithm to schedule itself to execute.  More than
        one parameter may change between the times that the algorithm can
        execute.

    .. method:: __init__()

        Initialize a detection algorithm, which simply initializes the
        instance attributes.

    .. method:: bind(**kwargs)

        :param tuple kwargs: parameter to property mapping

        Create a `DetectionMonitor` instance for each of the keyword arguments
        and point it back to this algorithm instance.  The algorithm parameter
        matches the keyword parameter name and the parameter value is an
        (object, property_name) tuple.

    .. method:: unbind()

        Delete the `DetectionMonitor` objects associated with this algorithm
        and remove them from the property changed call list(s).

    .. method:: execute()

        This function is provided by a derived class which checks to see if
        something should happen when its parameters have changed.  For example,
        maybe a change-of-value or event notification should be generated.

    .. method:: _execute()

        This method is a special wrapper around the `execute()` function
        that sets the internal trigger flag.  When the flag is set then the
        `execute()` function is already scheduled to run (via `deferred()`)
        and doesn't need to be scheduled again.

Decorators
----------

.. function:: monitor_filter(parameter)

    :param string parameter: name of parameter to filter

    This decorator is used with class methods of an algorithm to determine
    if the new value for a propert of an object is significant enough to
    consider the associated parameter value changed.  For example::

        class SomeAlgorithm(DetectionAlgorithm):
        
            @monitor_filter('pValue')
            def value_changed(self, old_value, new_value):
                return new_value > old_value + 10

    Assume that an instance of this algorithm is bound to the `presentValue`
    of an `AnalogValueObject`::
    
        some_algorithm = SomeAlgorithm()
        some_algorithm.bind(pValue = (avo, 'presentValue'))

    The algorithm parameter `pValue` will only be considered changed when
    the present value of the analog value object has increased by more than
    10 at once.  If it slowly climbs by something less than 10, or declines
    at all, the algorithm will not execute.

