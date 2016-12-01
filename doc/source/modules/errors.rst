.. BACpypes errors module

.. module:: errors

Errors
======

This module defines the exception class for errors it detects in the 
configuration of the stack or in encoding or decoding PDUs.  All of these
exceptions are derived from ValueError (in Python's built-in exceptions module).

Classes
-------

.. class:: ConfigurationError

    This error is raised when there are required components that are missing
    or defined incorrectly.  Many components, such as instances of
    :class:`comm.Client` and :class:`comm.Server`, are required to be bound 
    together in specific ways.

.. class:: EncodingError

    This error is raised while PDU data is being encoded, which typically means
    while some structured data is being turned into an octet stream or some 
    other simpler structure.  There may be limitations of the values being 
    encoded.

.. class:: DecodingError

    This error is raised while PDU data is being decoded, which typically means
    some unstructured data like an octet stream is being turned into structured
    data.  There may be values in the PDU being decoded that are not
    appropriate, or not enough data such as a truncated packet.

