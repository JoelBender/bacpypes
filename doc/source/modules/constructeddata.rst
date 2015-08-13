.. BACpypes constructed data module

.. module:: constructeddata

Constructed Data
================

This is a long line of text.

Elements
--------

This is a long line of text.

.. class:: Element

    .. attribute:: name

        This is a long line of text.

    .. attribute:: klass

        This is a long line of text.

    .. attribute:: context

        This is a long line of text.

    .. attribute:: optional

        This is a long line of text.

Sequences
---------

This is a long line of text.

.. class:: Sequence

    .. attribute:: sequenceElements

        This is a long line of text.

    .. method:: encode(taglist)
                decode(taglist)

        :param taglist: list of :class:`primitivedata.Tag` objects

        This is a long line of text.

    .. method:: debug_contents(indent=1, file=sys.stdout, _ids=None)

        This is a long line of text.

.. class:: SequenceOf(klass)

    .. method:: append(value)

        This is a long line of text.

    .. method:: __getitem__(item)

        :param item: item number

        This is a long line of text.

    .. method:: __len__()

        This is a long line of text.

    .. method:: encode(taglist)
                decode(taglist)

        :param taglist: list of :class:`primitivedata.Tag` objects

        This is a long line of text.

    .. method:: debug_contents(indent=1, file=sys.stdout, _ids=None)

        This is a long line of text.

Arrays
------

This is a long line of text.

.. class:: Array

    This is a long line of text.

.. class:: ArrayOf(klass)

    This is a long line of text.

    .. method:: append(value)

        This is a long line of text.

    .. method:: __len__()

        This is a long line of text.

    .. method:: __getitem__(item)

        :param item: item number

        This is a long line of text.

    .. method:: __setitem__(item, value)

        :param item: item number
        :param value: new value for item

        This is a long line of text.

    .. method:: __delitem__(item)

        :param item: item number

        This is a long line of text.

    .. method:: index(value)

        :param value: new value for item

        This is a long line of text.

    .. method:: encode(taglist)
                decode(taglist)

        :param taglist: list of :class:`primitivedata.Tag` objects

        This is a long line of text.

    .. method:: encode_item(item, taglist)
                decode_item(item, taglist)

        :param item: item number
        :param taglist: list of :class:`primitivedata.Tag` objects

        This is a long line of text.

    .. method:: debug_contents(indent=1, file=sys.stdout, _ids=None)

        This is a long line of text.

Choice
------

This is a long line of text.

.. class:: Choice

    This is a long line of text.

    .. method:: __init__(self, **kwargs)

        :param kwargs: expected value to set choice

        This is a long line of text.

    .. method:: encode(taglist)
                decode(taglist)

        :param taglist: list of :class:`primitivedata.Tag` objects

        This is a long line of text.

    .. method:: debug_contents(indent=1, file=sys.stdout, _ids=None)

        This is a long line of text.

Any
---

This is a long line of text.

.. class:: Any

    This is a long line of text.

    .. attribute:: tagList

        This is a long line of text.

    .. method:: __init__(self, *args)

        :param args: initial values to cast in

        This is a long line of text.

    .. method:: encode(taglist)
                decode(taglist)

        :param taglist: list of :class:`primitivedata.Tag` objects

        This is a long line of text.

    .. method:: cast_in(element)

        :param element: value to cast in

        This is a long line of text.

    .. method:: cast_out(klass)

        :param klass: class reference to decode value

        This is a long line of text.

    .. method:: debug_contents(indent=1, file=sys.stdout, _ids=None)

        This is a long line of text.
