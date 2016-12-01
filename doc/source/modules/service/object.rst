.. BACpypes object services

Object Services
===============

.. class:: ReadWritePropertyServices(Capability)

    This class provides the capability to respond to ReadProperty and
    WriteProperty service, used by a client BACnet-user to request the value
    of one property of one BACnet Object.

    .. method:: do_ReadPropertyRequest(apdu)

        :param ReadPropertyRequest apdu: request from the network

        See Clause 15.5 for the parameters to this service.

    .. method:: do_WritePropertyRequest(apdu)

        :param WritePropertyRequest apdu: request from the network

        See Clause 15.9 for the parameters to this service.

.. class:: ReadWritePropertyMultipleServices(Capability)

    This class provides the capability to respond to ReadPropertyMultiple and
    WritePropertyMultiple service, used by a client BACnet-user to request the
    values of one or more specified properties of one or more BACnet Objects.

    .. method:: do_ReadPropertyMultipleRequest(apdu)

        :param ReadPropertyRequest apdu: request from the network

        See Clause 15.7 for the parameters to this service.

    .. method:: do_WritePropertyMultipleRequest(apdu)

        :param WritePropertyMultipleRequest apdu: request from the network

        Not implemented.

Support Functions
-----------------

    .. function:: read_property_to_any(obj, propertyIdentifier, propertyArrayIndex=None):

        :param obj: object
        :param propertyIdentifier: property identifier
        :param propertyArrayIndex: optional array index

        Called by `read_property_to_result_element` to build an appropriate
        `Any` result object from the supplied object given the property
        identifier and optional array index.

    .. function:: read_property_to_result_element(obj, propertyIdentifier, propertyArrayIndex=None):

        :param obj: object
        :param propertyIdentifier: property identifier
        :param propertyArrayIndex: optional array index

        Called by `do_ReadPropertyMultipleRequest` to build the result element
        components of a `ReadPropertyMultipleACK`.
