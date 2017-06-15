.. BACpypes capability module

.. module:: capability

Capability
==========

Something here.

Classes
-------

.. class:: Capability

    .. attribute:: _zIndex

        Capability functions are ordered by this attribute.

.. class:: Collector

    .. attribute:: capabilities

        A list of Capability derived classes that are in the inheritance
        graph.

    .. method:: __init__()

        At initialization time the collector searches through the inheritance
        graph and builds the list of Capability derived classes and then
        calls the `__init__()` method for each of them.

    .. method:: capability_functions(fn)

        :param string fn: name of a capability function

        A generator that yields all of the functions of the Capability classes
        with the given name, ordered by z-index.

    .. method:: add_capability(cls)

        :param class cls: add a Capability derived class

        Add a Capability derived class to the method resolution order of the
        object.  This will give the object a new value for its __class__
        attribute.  The `__init__()` method will also be called with the
        object instance.

        This new capability will only be given to the object, no other objects
        with the same type will be given the new capability.

    .. method:: _search_capability(base)

        This private method returns a flatten list of all of the Capability
        derived classes, including other Collector classes that might be in
        the inheritance graph using recursion.

Functions
---------

.. function:: compose_capability(base, *classes)

    :param Collector base: Collector derived class
    :param Capability classes: Capability derived classes

    Create a new class composed of the base collector and the provided
    capability classes.

.. function:: add_capability(base, *classes)

    :param Collector base: Collector derived class
    :param Capability classes: Capability derived classes

    Add a capability derived class to a collector base.

    .. note::
        Objects that were created *before* the additional capabilities were
        added will have the new capability, but the `__init__()` functions
        of the classes will not be called.

        Objects created *after* the additional capabilities were added will
        have the additional capabilities with the `__init__()` functions called.
