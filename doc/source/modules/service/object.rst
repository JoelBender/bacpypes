.. BACpypes object services

Object Services
===============

.. class:: ReadWritePropertyServices(Capability)

    This is a long line of text.

    .. method:: do_ReadPropertyRequest(apdu)

        :param ReadPropertyRequest apdu: request from the network

        This is a long line of text.

    .. method:: do_WritePropertyRequest(apdu)

        :param WritePropertyRequest apdu: request from the network

        This is a long line of text.

.. class:: ReadWritePropertyMultipleServices(Capability)

    This is a long line of text.

    .. method:: do_ReadPropertyMultipleRequest(apdu)

        :param ReadPropertyRequest apdu: request from the network

        This is a long line of text.

    .. method:: do_WritePropertyMultipleRequest(apdu)

        :param WritePropertyMultipleRequest apdu: request from the network

        Not implemented.

Support Functions
-----------------

    .. function:: read_property_to_any(obj, propertyIdentifier, propertyArrayIndex=None):

        :param obj: object
        :param propertyIdentifier: property identifier
        :param propertyArrayIndex: optional array index

    .. function:: read_property_to_result_element(obj, propertyIdentifier, propertyArrayIndex=None):

        :param obj: object
        :param propertyIdentifier: property identifier
        :param propertyArrayIndex: optional array index

