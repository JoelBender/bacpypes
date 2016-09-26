.. BACpypes capability module

.. module:: capability

Capability
==========

Something here.

Classes
-------

.. class:: Capability

.. class:: Collector

    .. attribute:: capabilities

    .. method:: __init__()

        Method description.

    .. method:: capability_functions(fn)

        :param string fn: name of a capability function

        Method description.

    .. method:: add_capability(cls)

        :param class cls: add a Capability derived class

        Method description.

    .. method:: _search_capability(base)

        Method description.

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
