
Sample 1 - Simple Application
=============================

This sample application is the simplest BACpypes application that is a complete
:term:`stack`.  Using an INI file it will configure a :class:`LocalDeviceObject`, 
create a **SampleApplication** instance, and run, waiting for a keyboard interrupt
or a TERM signal to quit.

Generic Application Structure
-----------------------------

There is a common pattern to all BACpypes applications such as import statements
in a similar order, the same debugging initialization, and the same try...except
wrapper for the __main__ outer block.

All BACpypes applications gather some options from the command line and use the
ConfigParser module for reading configuration information::

    import sys
    import logging
    from ConfigParser import ConfigParser

Immediately following the built-in module includes are those for debugging::

    from bacpypes.debugging import Logging, ModuleLogger
    from bacpypes.consolelogging import ConsoleLogHandler

For applications that communicate on the network, it needs the :func:`core.run`
function::

    from bacpypes.core import run

Now there are usually a variety of other imports depending on what the application
wants to do.  This one is simple, it just needs to create a derived class of 
:class:`app.BIPSimpleApplication` and an instance of
:class:`object.LocalDeviceObject`::

    from bacpypes.app import BIPSimpleApplication
    from bacpypes.object import LocalDeviceObject

Global variables are initialized before any other classes or functions::

    # some debugging
    _debug = 0
    _log = ModuleLogger(globals())

Now skipping down to the main block.  Everything is wrapped in a
try..except..finally because many "real world" applications send startup and 
shutdown notfications to other processes and it is important to include 
the exception (or graceful conclusion) of the application along with the
notification::

    #
    #   __main__
    #

    try:
        # code goes here...

        _log.debug("initialization")
        # code goes here...

        _log.debug("running")
        # code goes here...

    except Exception, e:
        _log.exception("an error has occurred: %s", e)
    finally:
        _log.debug("finally")

Before the application specific code there is template code that lists the names
of the debugging log handlers (which are affectionately called *buggers*) 
available to attach debug handlers.  This list changes depending on what has
been imported, and sometimes it's easy to get lost.  The application simply
quits after the list::

    if ('--buggers' in sys.argv):
        loggers = logging.Logger.manager.loggerDict.keys()
        loggers.sort()
        for loggerName in loggers:
            sys.stdout.write(loggerName + '\n')
        sys.exit(0)

You can get a quick list of the debug loggers defined in this application by
looking for everything with *__main__* in the name::

    $ python sample001.py --buggers | grep __main__

Now that the names of buggers are known, the *--debug* option will attach a 
:class:`commandlogging.ConsoleLogHandler` to each of them and consume the section
of the argv list::

    if ('--debug' in sys.argv):
        indx = sys.argv.index('--debug')
        i = indx + 1
        while (i < len(sys.argv)) and (not sys.argv[i].startswith('--')):
            ConsoleLogHandler(sys.argv[i])
            i += 1
        del sys.argv[indx:i]

Usually the debugging hooks will be added to the end of the parameter and option
list::

    $ python sample001.py --debug __main__

Generic Initialization
----------------------

These sample applications and other server applications are run on many machines
on a BACnet intranet so INI files are used for configuration parameters.

.. note::
    When instances of applications are going to be run on virtual machines that
    are dynamically created in a cloud then most of these parameters will be 
    gathered from the environment, like the server name and address.

The INI file is usually called **BACpypes.ini** and located in the same directory
as the application, but the '--ini' option is available when it's not::

        # read in a configuration file
        config = ConfigParser()
        if ('--ini' in sys.argv):
            indx = sys.argv.index('--ini')
            ini_file = sys.argv[indx + 1]
            if not config.read(ini_file):
                raise RuntimeError, "configuration file %r not found" % (ini_file,)
            del sys.argv[indx:indx+2]
        elif not config.read('BACpypes.ini'):
            raise RuntimeError, "configuration file not found"

.. tip::

    There is a sample INI file called **BACpypes~.ini** as part of the repository.  Make 
    a local copy and edit it with information appropriate to your installation::

        $ pwd
        .../samples
        $ cp ../BACpypes~.ini BACpypes.ini
        $ nano BACpypes.ini


Now applications will create a :class:`object.LocalDeviceObject` which will
respond to Who-Is requests for device-address-binding procedures, and 
Read-Property-Requests to get more details about the device, including its 
object list, which will only have itself::

    # make a device object
    thisDevice = \
        LocalDeviceObject( objectName=config.get('BACpypes','objectName')
            , objectIdentifier=config.getint('BACpypes','objectIdentifier')
            , maxApduLengthAccepted=config.getint('BACpypes','maxApduLengthAccepted')
            , segmentationSupported=config.get('BACpypes','segmentationSupported')
            , vendorIdentifier=config.getint('BACpypes','vendorIdentifier')
            )

The application will create a SampleApplication instance::

        # make a test application
        SampleApplication(thisDevice, config.get('BACpypes','address'))

Last but not least it is time to run::

        run()

Sample Application
------------------

The sample application creates a class that does almost nothing.  The definition
and initialization mirrors the :class:`app.BIPSimpleApplication` and uses the
usual debugging statements at the front of the method calls::

    #
    #   SampleApplication
    #

    class SampleApplication(BIPSimpleApplication, Logging):

        def __init__(self, device, address):
            if _debug: SampleApplication._debug("__init__ %r %r", device, address)
            BIPSimpleApplication.__init__(self, device, address)

The following functions follow the :class:`comm.ApplicationServiceElement` 
design pattern.  In this sample application it does not make any requests, 
so this override is for symmetry::

    def request(self, apdu):
        if _debug: SampleApplication._debug("request %r", apdu)
        BIPSimpleApplication.request(self, apdu)

This sample application will receive many requests, particularly on a busy
network::

    def indication(self, apdu):
        if _debug: SampleApplication._debug("indication %r", apdu)
        BIPSimpleApplication.indication(self, apdu)

When the application is responding to a confirmed service request it will call
its response function::

    def response(self, apdu):
        if _debug: SampleApplication._debug("response %r", apdu)
        BIPSimpleApplication.response(self, apdu)

Because this sample application doesn't make any requests, it will not be 
receiving any responses from other BACnet servers, so again this function
is provided for symmetry::

    def confirmation(self, apdu):
        if _debug: SampleApplication._debug("confirmation %r", apdu)
        BIPSimpleApplication.confirmation(self, apdu)

Running
-------

When this sample application is run without any options, nothing appears on
the console because there are no statements other than debugging::

    $ python SampleApplication.py

So to see what is actually happening, run the application with debugging
enabled::

    $ python SampleApplication.py --debug __main__

The output will include the initialization, running, and finally statements.::

    DEBUG:__main__:initialization
    DEBUG:__main__:    - args: Namespace(buggers=False, color=False, debug=['__main__'], ini=<class 'bacpypes.consolelogging.ini'>)
    DEBUG:__main__.SampleApplication:__init__ <bacpypes.app.LocalDeviceObject object at 0x7fcd37a2ba90> '192.168.0.10/24'
    DEBUG:__main__:    - this_application: <__main__.SampleApplication object at 0x7fcd357dea50>
    DEBUG:__main__:    - services_supported: <bacpypes.basetypes.ServicesSupported object at 0x7fcd357def50>
    DEBUG:__main__:running

To run with debugging on just the SampleApplication class::

    $ python SampleApplication.py --debug __main__.SampleApplication

    DEBUG:__main__.SampleApplication:__init__ <bacpypes.app.LocalDeviceObject object at 0x7fadb71bca90> '192.168.0.10/24'

Or to see what is happening at the UDP layer of the program, use that module name::

    $ python SampleApplication.py --debug bacpypes.udp

Or to simplify the output to the methods of instances of the :class:`udp.UDPActor`
use the class name::

    $ python SampleApplication.py --debug bacpypes.udp.UDPActor

Then to see what BACnet packets are received and make it all the way up the 
stack to the application, combine the debugging::

    $ python SampleApplication.py --debug bacpypes.udp.UDPActor __main__.SampleApplication

The most common broadcast messages that are *not* application layer messages 
are **Who-Is-Router-To-Network** and **I-Am-Router-To-Network**.  You can see these 
messages being received and processed by the :class:`netservice.NetworkServiceElement`
buried in the stack::

    $ python SampleApplication.py --debug bacpypes.netservice.NetworkServiceElement

