#!/usr/bin/env python

"""
Simple implementation of a Client and Server
"""

from bacpypes.comm import Client, Server, bind


class MyServer(Server):
    def indication(self, arg):
        print('working on', arg)
        self.response(arg.upper())

class MyClient(Client):
    def confirmation(self, pdu):
        print('thanks for the ', pdu)
        
if __name__ == '__main__':
    c = MyClient()
    s = MyServer()
    bind(c, s)
    c.request('hi')