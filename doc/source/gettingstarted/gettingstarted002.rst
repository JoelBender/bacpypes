.. BACpypes Getting Started 1

Running BACpypes Applications
=============================

All BACpypes sample applications have the same basic set of command line 
options so it is easy to move between applications, turn debugging on and 
and using different configurations.  There may be additional options and 
command parameters than the ones described in this section.

Getting Help
------------

Whatever the command line parameters and additional options might be for
an application, you can start with help::

    $ python WhoIsIAm.py --help
    usage: WhoIsIAm.py [-h] [--buggers] [--debug [DEBUG [DEBUG ...]]] [--color] [--ini INI]

    This application presents a 'console' prompt to the user asking for Who-Is and
    I-Am commands which create the related APDUs, then lines up the coorresponding
    I-Am for incoming traffic and prints out the contents.

    optional arguments:
      -h, --help            show this help message and exit
      --buggers             list the debugging logger names
      --debug [DEBUG [DEBUG ...]]
                            add console log handler to each debugging logger
      --color               use ANSI CSI color codes
      --ini INI             device object configuration file

Listing Debugging Loggers
-------------------------

The BACpypes library and sample applications make extensive use of the 
built-in *logging* module in Python.  Every module in the library, along 
with every class and exported function, has a logging object associated 
with it.  By attaching a log handler to a logger, the log handler is given 
a chance to output the progress of the application.

Because BACpypes modules are deeply interconnected, dumping a complete list 
of all of the logger names is a long list.  Start out focusing on the 
components of the WhoIsIAm.py application::

    $ python WhoIsIAm.py --buggers | grep __main__
    __main__
    __main__.WhoIsIAmApplication
    __main__.WhoIsIAmConsoleCmd

In this sample, the entire application is called __main__ and it defines 
two classes.

Debugging a Module
------------------

Telling the application to debug a module is simple::

    $ python WhoIsIAm.py --debug __main__
    DEBUG:__main__:initialization
    DEBUG:__main__:    - args: Namespace(buggers=False, debug=['__main__'], ini=<class 'bacpypes.consolelogging.ini'>)
    DEBUG:__main__.WhoIsIAmApplication:__init__ (<bacpypes.app.LocalDeviceObject object at 0xb6dd98cc>, '128.253.109.40/24:47808')
    DEBUG:__main__:running
    > 

The output is the severity code of the logger (almost always DEBUG), the name 
of the module, class, or function, then some message about the progress of the 
application.  From the output above you can see that the application is 
beginning its initialization, shows the value of a variable called args,
an instance of the WhoIsIAmApplication class is created with some parameters,
and then the application starts running.

Debugging a Class
-----------------

Debugging all of the classes and functions can generate a lot of output,
so it is useful to focus on a specific function or class::

    $ python WhoIsIAm.py --debug __main__.WhoIsIAmApplication
    DEBUG:__main__.WhoIsIAmApplication:__init__ (<bacpypes.app.LocalDeviceObject object at 0x9bca8ac>, '128.253.109.40/24:47808')
    > 

The same method is used to debug the activity of a BACpypes module, for 
example, there is a class called UDPActor in the UDP module::

    $ python WhoIsIAm.py --ini BAC0.ini --debug bacpypes.udp.UDPActor
    > DEBUG:bacpypes.udp.UDPActor:__init__ <bacpypes.udp.UDPDirector 128.253.109.255:47808 at 0xb6d40d6c> ('128.253.109.254', 47808)
    DEBUG:bacpypes.udp.UDPActor:response <bacpypes.comm.PDU object at 0xb6d433cc>
        <bacpypes.comm.PDU object at 0xb6d433cc>
            pduSource = ('128.253.109.254', 47808)
            pduData = x'81.04.00.37.0A.10.6D.45.BA.C0.01.28.FF.FF.00.00.B6.01.05.FD...'

In this sample, an instance of a UDPActor is created and then its response 
function is called with an instance of a PDU as a parameter.  Following 
the function invocation description, the debugging output continues with the
contents of the PDU.  Notice that the protocol data is printed as a hex 
encoded string, and only the first 20 bytes of the message.

You can debug a function just as easily, and specify as many different 
combinations of logger names as necessary.  Note that you cannot debug a 
specific function within a class.

Changing INI Files
------------------

It is not unusual to have a variety of different INI files specifying 
different port numbers or other BACnet communications paramters.

Rather than swapping INI files, you can simply provide the INI file on the
command line, overriding the default BACpypes.ini file.  For example, I 
have an INI file for port 47808::

    $ python WhoIsIAm.py --ini BAC0.ini

And another one for port 47809::

    $ python WhoIsIAm.py --ini BAC1.ini

And I switch back and forth between them.

