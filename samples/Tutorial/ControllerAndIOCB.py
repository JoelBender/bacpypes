#!/usr/bin/env python

"""
The IO Control Block (IOCB) is an object that holds the parameters 
for some kind of operation or function and a place for the result. 
The IOController processes the IOCBs it is given and returns the 
IOCB back to the caller.
"""

import bacpypes
from bacpypes.iocb import IOCB, IOController


class SomeController(IOController):
    def process_io(self, iocb):
        self.complete_io(iocb, iocb.args[0] + iocb.args[1] * iocb.kwargs['a'])
        
def call_me(iocb):
    """
    When a controller completes the processing of a request, 
    the IOCB can contain one or more functions to be called. 
    """
    print("call me, %r or %r" % (iocb.ioResponse, iocb.ioError))        
        
if __name__ == '__main__':
    iocb = IOCB(1, 2, a=3)
    iocb.add_callback(call_me)
    some_controller = SomeController()
    some_controller.request_io(iocb)
    iocb.ioComplete.wait()
    
    print(iocb.ioComplete)
    print(iocb.ioComplete.is_set())
    print(iocb.ioState == bacpypes.iocb.COMPLETED)
    print(iocb.ioState == bacpypes.iocb.ABORTED)
    print(iocb.ioResponse)