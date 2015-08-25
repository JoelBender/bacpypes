.. BACpypes errors module

.. module:: errors

Errors
======

This module defines exception class for errors that it detects in the 
configuration of the stack or in encoding and decoding PDUs.  All of these
exceptions are derived from ValueError from the built-in exceptions module.

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
    data.  There may be values in the pdu being decoded that are not
    appropriate, or not enough data such as a truncated packet.

