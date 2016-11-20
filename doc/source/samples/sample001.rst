
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

Debugging and logging is brought to the application via a decorator (see later in class) and
you will need :class:`debugging.ModuleLogger`::

    from bacpypes.debugging import bacpypes_debugging, ModuleLogger

All BACpypes applications gather some options from the command line and use the
:class:`consolelogging.ConfigArgumentParser` function for reading configuration 
information::

    from bacpypes.consolelogging import ConfigArgumentParser

For applications that communicate on the network, it needs the :func:`core.run`
function::

    from bacpypes.core import run

Now there are usually a variety of other imports depending on what the application
wants to do.  This one is simple, it just needs to create a derived class of 
:class:`app.BIPSimpleApplication` and an instance of
:class:`service.device.LocalDeviceObject`::

    from bacpypes.app import BIPSimpleApplication
    from bacpypes.service.device import LocalDeviceObject

Global variables are initialized before any other classes or functions::

    # some debugging
    _debug = 0
    _log = ModuleLogger(globals())

Now skipping down to the main function.  Everything is wrapped in a
try..except..finally because many "real world" applications send startup and 
shutdown notifications to other processes and it is important to include 
the exception (or graceful conclusion) of the application along with the
notification::

    #
    #   __main__
    #
    
    def main():
        
        # code goes here...
    
        if _debug: _log.debug("initialization")
        if _debug: _log.debug("    - args: %r", args)
    
        try:
            # code goes here...
    
            _log.debug("initialization")
            # code goes here...
    
            _log.debug("running")
            # code goes here...
    
        except Exception as e:
            _log.exception("an error has occurred: %s", e)
        finally:
            _log.debug("finally")

    if __name__ == "__main__":
        main()

Generic Initialization
----------------------

These sample applications and other server applications are run on many machines
on a BACnet intranet so INI files are used for configuration parameters.

.. note::
    When instances of applications are going to be run on virtual machines that
    are dynamically created in a cloud then most of these parameters will be 
    gathered from the environment, like the server name and address.

The INI file is usually called **BACpypes.ini** and located in the same directory
as the application, but the '--ini' option is available when it's not. Here is
the basic example of a INI file::

    [BACpypes]
    objectName: Betelgeuse
    address: 192.168.1.2/24
    objectIdentifier: 599
    maxApduLengthAccepted: 1024
    segmentationSupported: segmentedBoth
    maxSegmentsAccepted: 1024
    vendorIdentifier: 15
    foreignPort: 0
    foreignBBMD: 128.253.109.254
    foreignTTL: 30

.. tip::

    There is a sample INI file called **BACpypes~.ini** as part of the repository.  Make 
    a local copy and edit it with information appropriate to your installation::

        $ pwd
        .../samples
        $ cp ../BACpypes~.ini BACpypes.ini
        $ nano BACpypes.ini

.. tip::
    
    Windows user may want to have a look to Notepad++ as a file editor. If
    using the Anaconda suite, you can use Spyder or any other text editor
    you like.

The INI file must exist when you will run the code.

Filling the blanks
----------------------

Before the application specific code there is template code that lists the names
of the debugging log handlers (which are affectionately called *buggers*) 
available to attach debug handlers.  This list changes depending on what has
been imported, and sometimes it's easy to get lost.::

    # parse the command line arguments and initialize loggers
    args = ConfigArgumentParser(description=__doc__).parse_args()

You can get a quick list of the debug loggers defined in this application by
looking for everything with *__main__* in the name::

    $ python sample001.py --buggers | grep __main__

Will output::

    __main__
    __main__.SampleApplication

Now that the names of buggers are known, the *--debug* option will attach a 
:class:`commandlogging.ConsoleLogHandler` to each of them and consume the section
of the argv list.  Usually the debugging hooks will be added to the end of the
parameter and option list::

    $ python SampleApplication.py --debug __main__

Will output::

    DEBUG:__main__:initialization
    DEBUG:__main__:    - args: Namespace(buggers=False, color=False, debug=['__main_
    _'], ini=<class 'bacpypes.consolelogging.ini'>)
    DEBUG:__main__:running
    DEBUG:__main__:fini

Now applications will create a :class:`service.device.LocalDeviceObject` which will
respond to Who-Is requests for device-address-binding procedures, and 
Read-Property-Requests to get more details about the device, including its 
object list, which will only have itself::

    # make a device object
    this_device = LocalDeviceObject(
        objectName=args.ini.objectname,
        objectIdentifier=int(args.ini.objectidentifier),
        maxApduLengthAccepted=int(args.ini.maxapdulengthaccepted),
        segmentationSupported=args.ini.segmentationsupported,
        vendorIdentifier=int(args.ini.vendoridentifier),
        vendorName="B612",
        )

.. note::

    As you can see, information from the INI file is used to descrive `this_device`

The application will create a SampleApplication instance::

    # make a sample application
    this_application = SampleApplication(this_device, args.ini.address)
    if _debug: _log.debug("    - this_application: %r", this_application)

We need to add service supported to the device using default values::

    # get the services supported
    services_supported = this_application.get_services_supported()
    if _debug: _log.debug("    - services_supported: %r", services_supported)

    # let the device object know
    this_device.protocolServicesSupported = services_supported.value

Last but not least it is time to run::

    run()

SampleApplication Class
------------------------

The sample application creates a class that does almost nothing.  The definition
and initialization mirrors the :class:`app.BIPSimpleApplication` and uses the
usual debugging decorator.::

    #
    #   SampleApplication
    #

    @bacpypes_debugging
    class SampleApplication(BIPSimpleApplication):

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
    DEBUG:__main__:    - args: Namespace(buggers=False, color=False, debug=['__main_
    _'], ini=<class 'bacpypes.consolelogging.ini'>)
    DEBUG:__main__.SampleApplication:__init__ <bacpypes.service.device.LocalDeviceOb
    ject object at 0x00000000026CC9B0> '192.168.1.2/24'
    DEBUG:__main__:    - this_application: <__main__.SampleApplication object at 0x0
    00000000301FC88>
    DEBUG:__main__:    - services_supported: <bacpypes.basetypes.ServicesSupported 
    object at 0x000000000301F940>
    DEBUG:__main__:running

To run with debugging on just the SampleApplication class::

    $ python SampleApplication.py --debug __main__.SampleApplication

Will output::

    DEBUG:__main__.SampleApplication:__init__ <bacpypes.service.device.LocalDeviceObject 
    object at 0x000000000231C9B0> '192.168.1.2/24'

Or to see what is happening at the UDP layer of the program, use that module name::

    $ python SampleApplication.py --debug bacpypes.udp

Will output::

    DEBUG:bacpypes.udp.UDPDirector:__init__ ('192.168.1.2', 47808) timeout=0 
    reuse=False actorClass=<class 'bacpypes.udp.UDPActor'> sid=None sapID=None
    DEBUG:bacpypes.udp.UDPDirector:    - getsockname: ('192.168.1.2', 47808)
    
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

Sending Log to a file
----------------------

The current --debug command line option takes a list of named debugging access 
points and attaches a StreamHandler which sends the output to sys.stderr. 
There is a way to send the debugging output to a 
RotatingFileHandler by providing a file name, and optionally maxBytes and 
backupCount. For example, this invocation sends the main application debugging 
to standard error and the debugging output of the bacpypes.udp module to the 
traffic.txt file::

    $ python SampleApplication.py --debug __main__ bacpypes.udp:traffic.txt

By default the `maxBytes` is zero so there is no rotating file, but it can be 
provided, for example this limits the file size to 1MB::

    $ python SampleApplication.py --debug __main__ bacpypes.udp:traffic.txt:1048576

If `maxBytes` is provided, then by default the `backupCount` is 10, but it can also 
be specified, so this limits the output to one hundred files::

    $ python SampleApplication.py --debug __main__ bacpypes.udp:traffic.txt:1048576:100

The definition of debug::

    positional arguments:
        --debug [DEBUG [ DEBUG ... ]]
            DEBUG ::= debugger [ : fileName [ : maxBytes [ : backupCount ]]]