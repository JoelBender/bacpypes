.. BACpypes primitive data module

.. module:: primitivedata

Primative Data
==============

This is a long line of text.

Tags
----

This is a long line of text.

.. class:: Tag

    This is a long line of text.

    .. attribute:: tagClass

        This is a long line of text.

    .. attribute:: tagNumber

        This is a long line of text.

    .. attribute:: tagLVT

        This is a long line of text.

    .. attribute:: tagData

        This is a long line of text.

    .. attribute:: _app_tag_name

        This is a long line of text.

    .. attribute:: _app_tag_class

        This is a long line of text.

    .. method:: __init__(*args)

        This is a long line of text.

    .. method:: set(tclass, tnum, tlvt=0, tdata='')

        This is a long line of text.

    .. method:: set_app_data(tnum, tdata)

        This is a long line of text.

    .. method:: encode(pdu)
                decode(pdu)

        This is a long line of text.

    .. method:: app_to_context(context)
                context_to_app(dataType)

        This is a long line of text.

    .. method:: app_to_object()

        This is a long line of text.

    .. method:: __repr__()

        This is a long line of text.

    .. method:: __eq__(tag)
                __ne__(tag)

        This is a long line of text.

    .. method:: debug_contents(indent=1, file=sys.stdout, _ids=None)

        This is a long line of text.

.. class:: ApplicationTag(Tag)

    This is a long line of text.

.. class:: ContextTag(Tag)

    This is a long line of text.

.. class:: OpeningTag(Tag)

    This is a long line of text.

.. class:: ClosingTag(Tag)

    This is a long line of text.

.. class:: TagList()

    This is a long line of text.

Atomic Data Types
-----------------

This is a long line of text.

.. class:: Atomic

    This is a long line of text.

    .. method:: __cmp__(other)

        :param other: reference to some other atomic data type object

        This is a long line of text.

.. class:: Null(Atomic)

    This is a long line of text.

    .. method:: encode(tag)
                decode(tag)

        :param tag: :class:`Tag` reference

        This is a long line of text.

.. class:: Boolean(Atomic)

    This is a long line of text.

    .. method:: encode(tag)
                decode(tag)

        :param tag: :class:`Tag` reference

        This is a long line of text.

.. class:: Unsigned(Atomic)

    This is a long line of text.

    .. method:: encode(tag)
                decode(tag)

        :param tag: :class:`Tag` reference

        This is a long line of text.

.. class:: Integer(Atomic)

    This is a long line of text.

    .. method:: encode(tag)
                decode(tag)

        :param tag: :class:`Tag` reference

        This is a long line of text.

.. class:: Real(Atomic)

    This is a long line of text.

    .. method:: encode(tag)
                decode(tag)

        :param tag: :class:`Tag` reference

        This is a long line of text.

.. class:: Double(Atomic)

    This is a long line of text.

    .. method:: encode(tag)
                decode(tag)

        :param tag: :class:`Tag` reference

        This is a long line of text.

.. class:: OctetString(Atomic)

    This is a long line of text.

    .. method:: encode(tag)
                decode(tag)

        :param tag: :class:`Tag` reference

        This is a long line of text.

.. class:: CharacterString(Atomic)

    This is a long line of text.

    .. method:: encode(tag)
                decode(tag)

        :param tag: :class:`Tag` reference

        This is a long line of text.

.. class:: BitString(Atomic)

    This is a long line of text.

    .. method:: encode(tag)
                decode(tag)

        :param tag: :class:`Tag` reference

        This is a long line of text.

    .. method:: __getitem__(bit)

        This is a long line of text.

    .. method:: __setitem__(bit, value)

        This is a long line of text.

.. class:: Enumerated(Atomic)

    This is a long line of text.

    .. attribute:: enumerations

        This is a long line of text.

    .. attribute:: _xlate_table

        This is a long line of text.

    .. method:: __getitem__(item)

        This is a long line of text.

    .. method:: get_long()

        This is a long line of text.

    .. method:: keylist()

        This is a long line of text.

    .. method:: __cmp__(other)

        This is a long line of text.

    .. method:: encode(tag)
                decode(tag)

        :param tag: :class:`Tag` reference

        This is a long line of text.

.. class:: Date(Atomic)

    This is a long line of text.

    .. method:: __init__(arg=None, year=255, month=255, day=255, dayOfWeek=255)

        :param arg:
        :param year:
        :param month:
        :param day:
        :param dayOfWeek:

        This is a long line of text.

    .. method:: now()

        This is a long line of text.

    .. method:: CalcDayOfWeek()

        This is a long line of text.

    .. method:: encode(tag)
                decode(tag)

        :param tag: :class:`Tag` reference

        This is a long line of text.

.. class:: Time(Atomic)

    This is a long line of text.

    .. method:: __init__(arg=None, hour=255, minute=255, second=255, hundredth=255)

        :param arg:
        :param hour:
        :param minute:
        :param second:
        :param hundredth:

        This is a long line of text.

    .. method:: now()

        This is a long line of text.

    .. method:: encode(tag)
                decode(tag)

        :param tag: :class:`Tag` reference

        This is a long line of text.

.. class:: ObjectType(Enumerated)

    This is a long line of text.

.. class:: ObjectIdentifier(Atomic)

    This is a long line of text.

    .. attribute:: objectTypeClass

        This is a long line of text.

    .. method:: __init__(*args)

        This is a long line of text.

    .. method:: set_tuple(objType, objInstance)
                get_tuple()

        :param objType: :class:`ObjectType` object type
        :param int objInstance: object instance

        This is a long line of text.

    .. method:: set_long(value)
                get_long()

        This is a long line of text.

    .. method:: encode(tag)
                decode(tag)

        :param tag: :class:`Tag` reference

        This is a long line of text.

    .. method:: __hash__()

        This is a long line of text.

    .. method:: __cmp__(other)

        This is a long line of text.
