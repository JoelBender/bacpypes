#!/usr/bin/env python

"""
This sample application is a BACnet device that has one record access file
('file', 1) and one stream access file ('file', 2).
"""

import os
import random
import string

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser

from bacpypes.core import run

from bacpypes.app import BIPSimpleApplication
from bacpypes.service.device import LocalDeviceObject
from bacpypes.service.file import FileServices, \
    LocalRecordAccessFileObject, LocalStreamAccessFileObject

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# configuration
RECORD_LEN = int(os.getenv('RECORD_LEN', 128))
RECORD_COUNT = int(os.getenv('RECORD_COUNT', 100))
OCTET_COUNT = int(os.getenv('OCTET_COUNT', 4096))

#
#   Local Record Access File Object Type
#

@bacpypes_debugging
class TestRecordFile(LocalRecordAccessFileObject):

    def __init__(self, **kwargs):
        """ Initialize a record accessed file object. """
        if _debug:
            TestRecordFile._debug("__init__ %r",
                kwargs,
                )
        LocalRecordAccessFileObject.__init__(self, **kwargs)

        # create some test data
        self._record_data = [
            ''.join(random.choice(string.ascii_letters)
            for i in range(RECORD_LEN)).encode('utf-8')
            for j in range(RECORD_COUNT)
            ]
        if _debug: LocalRecordAccessFileObject._debug("    - %d records",
                len(self._record_data),
                )

    def __len__(self):
        """ Return the number of records. """
        if _debug: TestRecordFile._debug("__len__")

        return len(self._record_data)

    def read_record(self, start_record, record_count):
        """ Read a number of records starting at a specific record. """
        if _debug: TestRecordFile._debug("read_record %r %r",
                start_record, record_count,
                )

        # end of file is true if last record is returned
        end_of_file = (start_record+record_count) >= len(self._record_data)

        return end_of_file, \
            self._record_data[start_record:start_record + record_count]

    def write_record(self, start_record, record_count, record_data):
        """ Write a number of records, starting at a specific record. """
        if _debug: TestRecordFile._debug("write_record %r %r %r",
                start_record, record_count, record_data,
                )

        # check for append
        if (start_record < 0):
            start_record = len(self._record_data)
            self._record_data.extend(record_data)

        # check to extend the file out to start_record records
        elif (start_record > len(self._record_data)):
            self._record_data.extend(['' for i in range(start_record - len(self._record_data))])
            start_record = len(self._record_data)
            self._record_data.extend(record_data)

        # slice operation works for other cases
        else:
            self._record_data[start_record:start_record + record_count] = record_data

        # return where the 'writing' actually started
        return start_record

#
#   Local Stream Access File Object Type
#

@bacpypes_debugging
class TestStreamFile(LocalStreamAccessFileObject):

    def __init__(self, **kwargs):
        """ Initialize a stream accessed file object. """
        if _debug:
            TestStreamFile._debug("__init__ %r",
                kwargs,
                )
        LocalStreamAccessFileObject.__init__(self, **kwargs)

        # create some test data
        self._file_data = ''.join(random.choice(string.ascii_letters)
            for i in range(OCTET_COUNT)).encode('utf-8')
        if _debug: TestStreamFile._debug("    - %d octets",
                len(self._file_data),
                )

    def __len__(self):
        """ Return the number of octets in the file. """
        if _debug: TestStreamFile._debug("__len__")

        return len(self._file_data)

    def read_stream(self, start_position, octet_count):
        """ Read a chunk of data out of the file. """
        if _debug: TestStreamFile._debug("read_stream %r %r",
                start_position, octet_count,
                )

        # end of file is true if last record is returned
        end_of_file = (start_position+octet_count) >= len(self._file_data)

        return end_of_file, \
            self._file_data[start_position:start_position + octet_count]

    def write_stream(self, start_position, data):
        """ Write a number of octets, starting at a specific offset. """
        if _debug: TestStreamFile._debug("write_stream %r %r",
                start_position, data,
                )

        # check for append
        if (start_position < 0):
            start_position = len(self._file_data)
            self._file_data += data

        # check to extend the file out to start_record records
        elif (start_position > len(self._file_data)):
            self._file_data += '\0' * (start_position - len(self._file_data))
            start_position = len(self._file_data)
            self._file_data += data

        # no slice assignment, strings are immutable
        else:
            data_len = len(data)
            prechunk = self._file_data[:start_position]
            postchunk = self._file_data[start_position + data_len:]
            self._file_data = prechunk + data + postchunk

        # return where the 'writing' actually started
        return start_position

#
#   __main__
#

def main():
    # parse the command line arguments
    args = ConfigArgumentParser(description=__doc__).parse_args()

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("    - args: %r", args)

    # make a device object
    this_device = LocalDeviceObject(
        objectName=args.ini.objectname,
        objectIdentifier=int(args.ini.objectidentifier),
        maxApduLengthAccepted=int(args.ini.maxapdulengthaccepted),
        segmentationSupported=args.ini.segmentationsupported,
        vendorIdentifier=int(args.ini.vendoridentifier),
        )

    # make a sample application
    this_application = BIPSimpleApplication(this_device, args.ini.address)

    # add the capability to server file content
    this_application.add_capability(FileServices)

    # get the services supported
    services_supported = this_application.get_services_supported()
    if _debug: _log.debug("    - services_supported: %r", services_supported)

    # let the device object know
    this_device.protocolServicesSupported = services_supported.value

    # make a record access file, add to the device
    f1 = TestRecordFile(
        objectIdentifier=('file', 1),
        objectName='RecordAccessFile1'
        )
    _log.debug("    - f1: %r", f1)
    this_application.add_object(f1)

    # make a stream access file, add to the device
    f2 = TestStreamFile(
        objectIdentifier=('file', 2),
        objectName='StreamAccessFile2'
        )
    _log.debug("    - f2: %r", f2)
    this_application.add_object(f2)

    _log.debug("running")

    run()

    _log.debug("fini")

if __name__ == "__main__":
    main()
