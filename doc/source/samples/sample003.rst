
Sample 3 - Who-Has/I-Have Counter
=================================

This sample application is very similar to the second sample.  It has the 
same basic structure and initialization, it counts the number of Who-Has and
I-Have messages it receives, and prints out a summary after the application
has been signalled to terminate (<ctrl-C> - KeyboardInterrupt).


Processing Service Requests
---------------------------

The beginning is going to be standard boiler plate function header::

    def do_WhoHasRequest(self, apdu):
        """Respond to a Who-Has request."""
        if _debug: SampleApplication._debug("do_WhoHasRequest %r", apdu)

Unlike the Who-Is request, Who-Has can come in two different flavors, one 
checking for an object by its identifier and one checking by its name.  Both 
cannot appear in the APDU at the same time::

        key = (str(apdu.pduSource),)
        if apdu.object.objectIdentifier is not None:
            key += (str(apdu.object.objectIdentifier),)
        elif apdu.object.objectName is not None:
            key += (apdu.object.objectName,)
        else:
            print "(rejected APDU:"
            apdu.debug_contents()
            print ")"
            return

        # count the times this has been received
        who_has_counter[key] += 1

When an optional parameter is not specified in a PDU then the corresponding 
attribute is ``None``.  With this particular APDU the *object*
parameter is required, and one of its child attributes *objectIdentifier*
or *objectName* will be not ``None``.  If both are ``None`` then the 
request is not properly formed.

.. note::

    The encoding and decoding layer does not understand all  
    the combinations of required and optional parameters in an APDU, so
    verify the validity of the request is the responsibility of the application.

    The application can rely on the fact that the APDU is well-formed - meaning 
    it has the appropriate opening and closing tags and the data
    types of the parameters are correct.  Watch out for parameters of type Any! 

The I-Am function is much simpler because all of the parameters are required::

        key = (
            str(apdu.pduSource),
            str(apdu.deviceIdentifier),
            str(apdu.objectIdentifier),
            apdu.objectName
            )

        # count the times this has been received
        i_have_counter[key] += 1

Dumping the contents of the counters is simple.

Just like Who-Is and I-Am, pairing up the requests and responses can be a
useful exercize, but in most cases the I-Am response from a device will be a
unicast message directly back to the requestor, so relying on broadcast traffic
to analyze object binding is not as useful as it used to be.

Running the Application
-----------------------

::

    $ python WhoHasIHaveApplication.py --debug __main__
    
    DEBUG:__main__:initialization
    DEBUG:__main__:    - args: Namespace(buggers=False, color=False, debug=['__main__'], ini=<class 'bacpypes.consolelogging.ini'>)
    DEBUG:__main__.WhoHasIHaveApplication:__init__ <bacpypes.app.LocalDeviceObject object at 0x7f887e83ca90> '192.168.87.59/24'
    DEBUG:__main__:    - services_supported: <bacpypes.basetypes.ServicesSupported object at 0x7f887c5f0f50>
    DEBUG:__main__:running

Allow the application to run for a few minutes.  Then end it so it will output its results.::

    DEBUG:__main__:fini
    ----- Who Has -----
    
    ----- I Have -----
    
.. note::

    The Who-Has and I-Have services are not widely used.

