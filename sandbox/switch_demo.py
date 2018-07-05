#!/usr/bin/python

"""
"""

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ArgumentParser
from bacpypes.consolecmd import ConsoleCmd

from bacpypes.comm import Client, Server, Debug, bind
from bacpypes.core import run, enable_sleeping

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
this_console = None
this_switch = None

#
#   DebugTerm
#

class DebugTerm(Debug):

    """
    A simple wrapper around the Debug class that prints out when it has been
    activated and deactivated by the switch.
    """

    def activate(self):
        print(self.label + " activated")

    def deactivate(self):
        print(self.label + " deactivated")

#
#    Switch
#

@bacpypes_debugging
class Switch(Client, Server):

    """
    A Switch is a client and server that wraps around clients and/or servers
    and provides a way to switch between them without unbinding and rebinding
    the stack.
    """

    class TerminalWrapper(Client, Server):

        def __init__(self, switch, terminal):
            self.switch = switch
            self.terminal = terminal

            if isinstance(terminal, Server):
                bind(self, terminal)
            if isinstance(terminal, Client):
                bind(terminal, self)

        def indication(self, *args, **kwargs):
            self.switch.request(*args, **kwargs)

        def confirmation(self, *args, **kwargs):
            self.switch.response(*args, **kwargs)

    def __init__(self, **terminals):
        if _debug: Switch._debug("__init__ %r", terminals)

        Client.__init__(self)
        Server.__init__(self)

        # wrap the terminals
        self.terminals = {k:Switch.TerminalWrapper(self, v) for k, v in terminals.items()}
        self.current_terminal = None

    def __getitem__(self, key):
        if key not in self.terminals:
            raise KeyError("%r not a terminal" % (key,))

        # return the terminal, not the wrapper
        return self.terminals[key].terminal

    def __setitem__(self, key, term):
        if key in self.terminals:
            raise KeyError("%r already a terminal" % (key,))

        # build a wrapper and map it
        self.terminals[key] = Switch.TerminalWrapper(self, term)

    def __delitem__(self, key):
        if key not in self.terminals:
            raise KeyError("%r not a terminal" % (key,))

        # if deleting current terminal, deactivate it
        term = self.terminals[key].terminal
        if term is self.current_terminal:
            terminal_deactivate = getattr(self.current_terminal, 'deactivate', None)
            if terminal_deactivate:
                terminal_deactivate()
            self.current_terminal = None

        del self.terminals[key]

    def switch_terminal(self, key):
        if key not in self.terminals:
            raise KeyError("%r not a terminal" % (key,))

        if self.current_terminal:
            terminal_deactivate = getattr(self.current_terminal, 'deactivate', None)
            if terminal_deactivate:
                terminal_deactivate()

        if key is None:
            self.current_terminal = None
        else:
            self.current_terminal = self.terminals[key].terminal
            terminal_activate = getattr(self.current_terminal, 'activate', None)
            if terminal_activate:
                terminal_activate()

    def indication(self, *args, **kwargs):
        """Downstream packet, send to current terminal."""
        if not self.current_terminal:
            raise RuntimeError("no active terminal")
        if not isinstance(self.current_terminal, Server):
            raise RuntimeError("current terminal not a server")

        self.current_terminal.indication(*args, **kwargs)

    def confirmation(self, *args, **kwargs):
        """Upstream packet, send to current terminal."""
        if not self.current_terminal:
            raise RuntimeError("no active terminal")
        if not isinstance(self.current_terminal, Client):
            raise RuntimeError("current terminal not a client")

        self.current_terminal.confirmation(*args, **kwargs)

#
#   TestConsoleCmd
#

@bacpypes_debugging
class TestConsoleCmd(Client, Server, ConsoleCmd):

    def __init__(self):
        Client.__init__(self)
        Server.__init__(self)
        ConsoleCmd.__init__(self)

    def do_request(self, args):
        """request <msg>"""
        args = args.split()
        if _debug: TestConsoleCmd._debug("do_request %r", args)

        # send the request down the stack
        self.request(args[0])

    def do_response(self, args):
        """response <msg>"""
        args = args.split()
        if _debug: TestConsoleCmd._debug("do_response %r", args)

        # send the response up the stack
        self.response(args[0])

    def do_switch(self, args):
        """switch <arg>"""
        args = args.split()
        if _debug: TestConsoleCmd._debug("do_switch %r", args)
        global this_switch

        this_switch.switch_terminal(args[0])
        print("switched")

    def do_add(self, args):
        args = args.split()
        if _debug: TestConsoleCmd._debug("do_add %r", args)
        global this_switch

        # make a new terminal
        this_switch[args[0]] = DebugTerm(args[0])

    def do_del(self, args):
        args = args.split()
        if _debug: TestConsoleCmd._debug("do_del %r", args)
        global this_switch

        # delete the terminal
        del this_switch[args[0]]

    def indication(self, arg):
        """Got a request, echo it back up the stack."""
        print("indication: {}".format(arg))

    def confirmation(self, arg):
        print("confirmation: {}".format(arg))

#
#   main
#

@bacpypes_debugging
def main():
    # parse the command line arguments
    args = ArgumentParser(description=__doc__).parse_args()
    global this_switch, this_console

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("    - args: %r", args)

    # make some debugging terminals
    debug1 = DebugTerm("a")
    debug2 = DebugTerm("b")

    # make a switch with them
    this_switch = Switch(a=debug1, b=debug2)
    if _debug: _log.debug("    this_switch: %r", this_switch)

    # make a test console
    this_console = TestConsoleCmd()
    if _debug: _log.debug("    this_console: %r", this_console)

    # bind the console to the top and bottom of the switch
    bind(this_console, this_switch, this_console)

    # enable sleeping will help with threads
    enable_sleeping()

    _log.debug("running")

    run()

    _log.debug("fini")

if __name__ == "__main__":
    main()

