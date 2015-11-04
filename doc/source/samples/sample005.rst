.. BACpypes sample code 5

Sample 5 - Building Requests
============================

This is a long line of text.

.. note::

    Some notes.

Constructing the Device
-----------------------

Initialization is simple, the simple BACnet/IP application, which includes the
networking layer and communications layers all bundled in together is created
like the other samples::

    # make a sample application
    thisApplication = BIPSimpleApplication(thisDevice, config.get('BACpypes','address'))

