Sample 2 - Who-Is/I-Am Counter
==============================

This sample application builds on the first sample by overriding the default 
processing for Who-Is and I-Am requests, counting them, then continuing on
with the regular processing.

The description of this sample will be about the parts that are different from
sample 1.

.. note::

    New in 0.15! As you've seen reading :ref:`Capabilities`, the new API allows
    mixing functionnality to application more easily. In fact, by default, 
    inheriting from :class:`app.BISimpleApplication` includes 
    :class:`service.device.WhoIsIAmServices` and 
    :class:`service.device.ReadWritePropertyServices` capabilities.

Counters
--------

Python has a excellent *defaultdict* datatype from the *collections* module
that is perfect for this application.  It is very easy to use::

    >>> from collections import defaultdict
    >>> x = defaultdict(int)

The essential idea is that you can treat some key as having a default value
if it doesn't exist, so rather than doing this::

    >>> x['a'] = x.get('a', 0) + 1

You can do this::

    >>> x['a'] += 1

Processing Service Requests
---------------------------

When an instance of the :class:`app.Application` receives a request it attempts
to look up a function based on the message.  So when a WhoIsRequest APDU is
received, there should be a do_WhoIsRequest function. In fact, 
:class:`services.device.WhoIsIAmServices` provides this function. For the sake 
of this sample, we will override it so we can count requests.

The beginning is going to be standard boiler plate function header::

    def do_WhoIsRequest(self, apdu):
        """Respond to a Who-Is request."""
        if _debug: SampleApplication._debug("do_WhoIsRequest %r", apdu)

The middle is going to process the data in the request::

        # build a key from the source and parameters
        key = (str(apdu.pduSource),
            apdu.deviceInstanceRangeLowLimit,
            apdu.deviceInstanceRangeHighLimit,
            )

        # count the times this has been received
        who_is_counter[key] += 1

And the end of the function is going to call back to the standard application
processing::

        # pass back to the default implementation
        BIPSimpleApplication.do_WhoIsRequest(self, apdu)

The do_IAmRequest function is similar::

    def do_IAmRequest(self, apdu):
        """Given an I-Am request, cache it."""
        if _debug: SampleApplication._debug("do_IAmRequest %r", apdu)

It uses a diferent key, but counts them the same::

        # build a key from the source, just use the instance number
        key = (str(apdu.pduSource),
            apdu.iAmDeviceIdentifier[1],
            )

        # count the times this has been received
        i_am_counter[key] += 1

And has an identical call to the base class::

        # pass back to the default implementation
        BIPSimpleApplication.do_IAmRequest(self, apdu)

Printing Results
----------------

By building the key out of elements in a useful order, it is simple enough
to sort the dictionary items and print them out, and being able to unpack
the key in the for loop is a nice feature of Python::

    print("----- Who Is -----")
    for (src, lowlim, hilim), count in sorted(who_is_counter.items()):
        print("%-20s %8s %8s %4d" % (src, lowlim, hilim, count))
    print("")

Pairing up the requests and responses can be a useful exercize, but in most
cases the I-Am response from a device will be a unicast message directly back
to the requestor, so relying on broadcast traffic to analyze device and 
address binding is not as useful as it used to be.

Running the Application
-----------------------

::

    $ python WhoIsIAmApplication.py --debug __main__
    
    DEBUG:__main__:initialization
    DEBUG:__main__:    - args: Namespace(buggers=False, color=False, debug=['__main__'], ini=<class 'bacpypes.consolelogging.ini'>)
    DEBUG:__main__.WhoIsIAmApplication:__init__ <bacpypes.app.LocalDeviceObject object at 0x7f596a817a90> '192.168.87.59/24'
    DEBUG:__main__:    - services_supported: <bacpypes.basetypes.ServicesSupported object at 0x7f59685cbe90>
    DEBUG:__main__:running

Let it run for a minute, then Press <ctrl-C> to end it.  It will output its results.::

    DEBUG:__main__.WhoIsIAmApplication:do_WhoIsRequest <bacpypes.apdu.WhoIsRequest(8) instance at 0x7f7ca6792510>
        <bacpypes.apdu.WhoIsRequest(8) instance at 0x7f7ca6792510>
            pduSource = <Address 192.168.87.115>
            pduDestination = <GlobalBroadcast *:*>
            pduExpectingReply = False
            pduNetworkPriority = 0
            apduType = 1
            apduService = 8
            deviceInstanceRangeLowLimit = 59L
            deviceInstanceRangeHighLimit = 59L
            pduData = x''
    [clipped...]
    DEBUG:__main__:fini
    ----- Who Is -----
    10001:0x0040ae007e01        1        1    1
    10001:0x0040ae007e01     9830     9830    1
    10001:0x005008067649      536      536    1
    10001:0x005008067649     2323     2323    1
    192.168.87.115              9        9    3
    192.168.87.115             59       59    1
    192.168.87.115            226      226    3
    192.168.87.115            900      900    2
    192.168.87.115          11189    11189    3
    192.168.87.115          80403    80403    3
    192.168.87.115         110900   110900    3
    192.168.87.115        4194302  4194302    2
    192.168.87.48            3300     3300    1

    ----- I Am -----

