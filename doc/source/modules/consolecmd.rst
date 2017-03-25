.. BACpypes console command module

.. module:: consolecmd

Console Command
===============

Python has a `cmd <http://wiki.python.org/moin/CmdModule>`_ module that makes
it easy to embed a command line interpreter in an application.  BACpypes 
extends this interpreter with some commands to assist debugging and runs 
the interpreter in a separate thread so it does not interfere with the BACpypes
:func:`core.run` functionality.

Functions
---------

.. function:: console_interrupt(*args)

    :param args:

Classes
-------

.. class:: ConsoleCmd(cmd.Cmd, Thread)


    .. method:: __init__(prompt="> ", allow_exec=False)

        :param string prompt: prompt for commands
        :param boolean allow_exec: allow non-commands to be executed


    .. method:: run()

        Begin execution of the application's main event loop.  Place this after the 
        the initialization statements. 

    .. method:: do_something(args)

        :param args: commands

        Template of a function implementing a console command.
        

Commands
--------

.. option:: help

    List an application's console commands::

        > help
        Documented commands (type help <topic>):
        ========================================
        EOF  buggers  bugin  bugout  exit  gc  help  nothing  shell
    
.. option:: gc

    Print out garbage collection information::

        > gc
        Module                         Type                            Count dCount   dRef
        bacpypes.object                OptionalProperty                  787      0      0
        bacpypes.constructeddata       Element                           651      0      0
        bacpypes.object                ReadableProperty                  362      0      0
        bacpypes.object                WritableProperty                   44      0      0
        __future__                     _Feature                            7      0      0
        Queue                          Queue                               2      0      0
        bacpypes.pdu                   Address                             2      0      0
        bacpypes.udp                   UDPActor                            2      1      4
        bacpypes.bvllservice           UDPMultiplexer                      1      0      0
        bacpypes.app                   DeviceInfoCache                     1      0      0
        
        Module                         Type                            Count dCount   dRef
        bacpypes.udp                   UDPActor                            2      1      4
    
.. option:: bugin <name>

    Attach a debugger.::
    
        > bugin bacpypes.task.OneShotTask
        handler to bacpypes.task.OneShotTask added

.. option:: bugout <name>

    Detach a debugger.::

        > bugout bacpypes.task.OneShotTask
        handler to bacpypes.task.OneShotTask removed

.. option:: buggers

    Get a list of the available buggers.::

        > buggers
        no handlers
        __main__
        bacpypes
        bacpypes.apdu
        bacpypes.apdu.APCI
        ...
        bacpypes.vlan.Network
        bacpypes.vlan.Node
      
.. option:: exit

    Exit a BACpypes Console application.::

        > exit
        Exiting...
