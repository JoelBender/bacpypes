.. BACpypes object module

.. module:: object

Objects
=======

BACnet virtual link layer...

Globals
-------

This is a long line of text.

.. data:: map_name_re

    This is a long line of text.

.. data:: object_types

    This is a long line of text.

Functions
---------

This is a long line of text.

.. function:: map_name(name)

    :param string name: something

    This is a long line of text.

.. function:: register_object_type(klass)

    :param klass: class to register

    This is a long line of text.

.. function:: get_object_class(objectType)

    :param objectType: something
    :returns: something

    This is a long line of text.

.. function:: get_datatype(objectType, property)

    :param objectType: something
    :param property: something
    :returns: datatype class

    This is a long line of text.

Properties
----------

This is a long line of text.

.. class:: Property

    This is a long line of text.

    .. attribute:: identifier

        This is a long line of text.

    .. attribute:: datatype

        This is a long line of text.

    .. attribute:: optional

        This is a long line of text.

    .. attribute:: mutable

        This is a long line of text.

    .. attribute:: default

        This is a long line of text.

    .. method:: ReadProperty(obj, arrayIndex=None)

        :param obj: object reference
        :param arrayIndex: optional array index

        This is a long line of text.

    .. method:: WriteProperty(obj, value, arrayIndex=None, priority=None)
    
        :param obj: object reference
        :param value: new property value
        :param arrayIndex: optional array index
        :param priority: optional priority

        This is a long line of text.

.. class:: ObjectIdentifierProperty

    .. method:: WriteProperty(obj, value, arrayIndex=None, priority=None)
    
        :param obj: object reference
        :param value: new property value
        :param arrayIndex: optional array index
        :param priority: optional priority

        This is a long line of text.

.. class:: CurrentDateProperty

    .. method:: ReadProperty(obj, arrayIndex=None)

        :param obj: object reference
        :param arrayIndex: optional array index

        This is a long line of text.

    .. method:: WriteProperty(obj, value, arrayIndex=None, priority=None)

        This method is to override the :func:`Property.WriteProperty` so 
        instances of this class will raise an expection and be considered
        unwriteable.
    
.. class:: CurrentTimeProperty

    .. method:: ReadProperty(obj, arrayIndex=None)

        :param obj: object reference
        :param arrayIndex: optional array index

        This is a long line of text.

    .. method:: WriteProperty(obj, value, arrayIndex=None, priority=None)

        This method is to override the :func:`Property.WriteProperty` so 
        instances of this class will raise an expection and be considered
        unwriteable.

Objects
-------

This is a long line of text.

.. class Object

    This is a long line of text.

    .. attribute:: properties

        This is a long line of text.

    .. attribute:: _properties

        This is a long line of text.

    .. attribute:: _values

        This is a long line of text.

    .. method:: _attr_to_property(attr)
    
        :param attr: attribute name to map to property instance

        This is a long line of text.

    .. method:: __getattr__(attr)

        :param attr: attribute name (Python form)

        This is a long line of text.

    .. method:: __setattr__(attr, value)

        :param attr: attribute name (Python form)
        :param value: new value

        This is a long line of text.

    .. method:: ReadProperty(property, arrayIndex=None)

        :param property: property reference
        :param arrayIndex: optional array index

        This is a long line of text.

    .. method:: WriteProperty(property, value, arrayIndex=None, priority=None)

        :param property: property reference
        :param value: new value
        :param arrayIndex: optional array index
        :param priority: optional priority

        This is a long line of text.

    .. method:: get_datatype(property)

        :param property: property reference

        This is a long line of text.

    .. method:: debug_contents(indent=1, file=sys.stdout, _ids=None)

        This function has the same interface as
        :func:`debugging.DebugContents.debug_contents` and provides a way of
        debugging the contents of the object when the property values are
        complex objects that also have a *debug_contents* method.

        This function presents the properties in the order they are defined
        in the *_properties* attribute, including going through the class
        heirarchy to pick up inherited properties.

Standard Object Types
---------------------

This is a long line of text.

.. class:: AccumulatorObject(Object)

.. class:: BACnetAccumulatorRecord(Sequence)

.. class:: AnalogInputObject(Object)

.. class:: AnalogOutputObject(Object)

.. class:: AnalogValueObject(Object)

.. class:: AveragingObject(Object)

.. class:: BinaryInputObject(Object)

.. class:: BinaryOutputObject(Object)

.. class:: BinaryValueObject(Object)

.. class:: CalendarObject(Object)

.. class:: CommandObject(Object)

.. class:: DeviceObject(Object)

.. class:: EventEnrollmentObject(Object)

.. class:: FileObject(Object)

.. class:: GroupObject(Object)

.. class:: LifeSafetyPointObject(Object)

.. class:: LifeSafetyZoneObject(Object)

.. class:: LoopObject(Object)

.. class:: MultiStateInputObject(Object)

.. class:: MultiStateOutputObject(Object)

.. class:: MultiStateValueObject(Object)

.. class:: NotificationClassObject(Object)

.. class:: ProgramObject(Object)

.. class:: PulseConverterObject(Object)

.. class:: ScheduleObject(Object)

.. class:: StructuredViewObject(Object)

.. class:: TrendLogObject(Object)

Extended Object Types
---------------------

.. class:: LocalDeviceObject(DeviceObject)
