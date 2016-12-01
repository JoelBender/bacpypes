.. BACpypes tutorial lesson 6

Command Shell
=============

Debugging small, short lived BACpypes applications is fairly simple with the 
abillity to attach debug handlers to specific components of a stack when it
starts, and then reproducing whatever situation caused the mis-behaviour.

For longer running applications like gateways it might take some time before 
a scenario is ready, in which case it is advantageous to start and stop the debugging 
output, without stopping the application.

For some debugging scenarios it is beneficial to force some values into the 
stack, or delete some values and see how the application performs.  For example,
perhaps deleting a routing path associated with a network.

Python has a `cmd <http://wiki.python.org/moin/CmdModule>`_ module that makes
it easy to embed a command line interpreter in an application.  BACpypes 
extends this interpreter with some commands to assist debugging and runs 
the interpreter in a separate thread so it does not interfere with the BACpypes
:func:`core.run` functionality.

Application Additions
---------------------

Adding the console command shell is as simple as importing it::

    from bacpypes.consolecmd import ConsoleCmd

And creating an instance::

    # console
    ConsoleCmd()

In addition to the other command line options that are typically included in
BACpypes applications, this can be wrapped::

    if '--console' in sys.agv:
        ConsoleCmd()

Command Recall
--------------

The BACpypes command line interpreter maintains a history (text file) 
of the commands executed, which it reloads upon startup. 
Pressing the *previous command* keyboard shortcut (up-arrow key) 
recalls previous commands so they can be executed again.

Basic Commands
--------------

All of the commands supported are listed in the :mod:`consolecmd` documentation.
The simplest way to learn the commands is to try them::

    $ python Tutorial/SampleConsoleCmd.py 
    > hi
    *** Unknown syntax: hi

There is some help::

    > help

    Documented commands (type help <topic>):
    ========================================
    EOF  buggers  bugin  bugout  exit  gc  help  shell

And getting a list of the buggers::

    > buggers
    no handlers
      __main__
      bacpypes
      bacpypes.apdu
      bacpypes.apdu.APCI
      ...
      bacpypes.vlan.Network
      bacpypes.vlan.Node

Attaching a debugger::

    > bugin bacpypes.task.OneShotTask
    handler to bacpypes.task.OneShotTask added

Then removing it later::

    > bugout bacpypes.task.OneShotTask
    handler to bacpypes.task.OneShotTask removed

And finally exiting the application::

    > exit
    Exiting...

Adding Commands
---------------

Adding additional commands is as simple as providing an additional function. 
Add these lines to SampleConsoleCmd.py::

    class SampleConsoleCmd(ConsoleCmd):

        def do_something(self, arg):
            """something <arg> - do something"""
            print("do something", arg)

The ConsoleCmd will trap a help request ``help something`` into printing out
the documnetation string.::

    > help
    
    Documented commands (type help <topic>):
    ========================================
    EOF  buggers  bugin  bugout  exit  gc  help  nothing  shell  **something**
    
    > help something
    something <arg> - do something
    > 



Example Cache Commands
----------------------

Add these functions to **SampleConsoleCmd.py**.  The concept is to force values into an
application cache, delete them, and dump the cache.  First, setting values
is a *set* command::

    class SampleConsoleCmd(ConsoleCmd):

        my_cache= {}
        
        def do_set(self, arg):
            """set <key> <value> - change a cache value"""
            if _debug: SampleConsoleCmd._debug("do_set %r", arg)
    
            key, value = arg.split()
            self.my_cache[key] = value
    
Then delete cache entries with a *del* command::

        def do_del(self, arg):
            """del <key> - delete a cache entry"""
            if _debug: SampleConsoleCmd._debug("do_del %r", arg)
    
            try:
                del self.my_cache[arg]
            except:
                print(arg, "not in cache")
    
And to verify, dump the cache::

        def do_dump(self, arg):
            """dump - nicely print the cache"""
            if _debug: SampleConsoleCmd._debug("do_dump %r", arg)
            print(self.my_cache)


And when the sample application is run, note the new commands
show up in the help list::

    $ python Tutorial/SampleConsoleCmd.py
    > help
    
    Documented commands (type help <topic>):
    ========================================
    EOF      bugin   **del**   exit  help     **set**    something
    buggers  bugout  **dump**  gc    nothing  shell
    

You can get help with the new commands::

    > help set
    set <key> <value> - change a cache value


Lets use these new commands to add some items to the cache and dump it out::

    > set x 12
    > set y 13
    > dump
    {'x': '12', 'y': '13'}


Now add a debugger to the main application, which can generate a lot output
for most applications, but this one is simple::

    > bugin __main__
    handler to __main__ added

Now we'll get some debug output when the cache entry is deleted::

    > del x
    DEBUG:__main__.SampleConsoleCmd:do_del 'x'

We can see a list of buggers and which ones have a debugger attached::

    > buggers __main__
    handlers: __main__
    * __main__
      __main__.SampleApplication
      __main__.SampleConsoleCmd


Check the contents of the cache::

    > dump
    DEBUG:__main__.SampleConsoleCmd:do_dump ''
    {'y': '13'}

All done::

    > exit
    Exiting...
