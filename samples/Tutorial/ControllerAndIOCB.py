#!/usr/bin/env python

"""
The IO Control Block (IOCB) is an object that holds the parameters 
for some kind of operation or function and a place for the result. 
The IOController processes the IOCBs it is given and returns the 
IOCB back to the caller.
"""

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ArgumentParser

from bacpypes.iocb import IOCB, IOController, COMPLETED, ABORTED

# some debugging
_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
class SomeController(IOController):

    def process_io(self, iocb):
        if _debug: SomeController._debug("process_io", iocb)

        # try to complete the request
        try:
            response = iocb.args[0] + iocb.args[1] * iocb.kwargs['a']
            self.complete_io(iocb, response)
        except Exception as err:
            self.abort_io(iocb, err)


@bacpypes_debugging
def call_me(iocb):
    """
    When a controller completes the processing of a request, 
    the IOCB can contain one or more functions to be called. 
    """
    if _debug: call_me._debug("callback_function %r", iocb)

    # it will be successful or have an error
    print("call me, %r or %r" % (iocb.ioResponse, iocb.ioError))        


def main():
    # parse the command line arguments
    args = ArgumentParser(description=__doc__).parse_args()

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("    - args: %r", args)

    # create a controller
    some_controller = SomeController()
    if _debug: _log.debug("    - some_controller: %r", some_controller)

    # test set
    tests = [
        ( (1,2,), {'a':3} ),
        ( (4,5,), {} ),
        ( (6,), {'a':7} ),
        ]

    for test_args, test_kwargs in tests:
        print("test_args, test_kwargs: %r, %r" % (test_args, test_kwargs))

        # create a request with some args and kwargs
        iocb = IOCB(*test_args, **test_kwargs)

        # add a callback function , called when the request has been processed
        iocb.add_callback(call_me)

        # give the request to the controller
        some_controller.request_io(iocb)

        # wait for the request to be processed
        iocb.ioComplete.wait()
        if _debug: _log.debug("    - iocb: %r", iocb)

        # dump the contents
        print("iocb completion event set: %r" % (iocb.ioComplete.is_set(),))
        print("")

        print("iocb successful: %r" % (iocb.ioState == COMPLETED,))
        print("iocb response: %r" % (iocb.ioResponse,))
        print("")

        print("iocb aborted: %r" % (iocb.ioState == ABORTED,))
        print("iocb error: %r" % (iocb.ioError,))
        print("")

if __name__ == '__main__':
    main()

