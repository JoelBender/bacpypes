#!/bin/bash python

"""
This simple application takes a string form of a BACnet address from the
command line and attempts to interpret it.
"""

import sys

from bacpypes.consolelogging import ArgumentParser
from bacpypes.pdu import Address

# build a parser for the command line arguments
parser = ArgumentParser(description=__doc__)
parser.add_argument("address",
    help="address to interpret",
    )

# parse the command line arguments
args = parser.parse_args()

# try to interpret the address
try:
    addr = Address(args.address)
except Exception as err:
    print(err)
    sys.exit(1)

# print the string form
print(addr)

# print the various components
for attr in [
        'addrType', 'addrNet', 'addrAddr', 'addrLen',   # universal
        'addrTuple', 'addrBroadcastTuple',              # IPv4
    ]:
    if hasattr(addr, attr):
        print("%s: %r" % (attr, getattr(addr, attr)))

