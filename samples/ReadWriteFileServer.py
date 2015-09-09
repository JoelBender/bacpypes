#!/usr/bin/python

"""
ReadWriteFileServer.py

This sample application is a BACnet device that has one record access file at
('file', 1) and one stream access file at ('file', 2).
"""

import random
import string

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser

from bacpypes.core import run

from bacpypes.app import LocalDeviceObject, BIPSimpleApplication
from bacpypes.object import FileObject, register_object_type

from bacpypes.basetypes import ServicesSupported

# some debugging
_debug = 0
_log = ModuleLogger(globals())

#
#   Local Record Access File Object Type
#

@bacpypes_debugging
class LocalRecordAccessFileObject(FileObject):

    def __init__(self, **kwargs):
        """ Initialize a record accessed file object. """
        if _debug:
            LocalRecordAccessFileObject._debug("__init__ %r",
                kwargs,
                )
        FileObject.__init__(self,
            fileAccessMethod='recordAccess',
             **kwargs
             )

        self._record_data = [
            ''.join(random.choice(string.ascii_letters)
            for i in range(random.randint(10, 20)))
            for j in range(random.randint(10, 20))
            ]
        if _debug: LocalRecordAccessFileObject._debug("    - %d records",
                len(self._record_data),
                )

    def __len__(self):
        """ Return the number of records. """
        if _debug: LocalRecordAccessFileObject._debug("__len__")

        return len(self._record_data)

    def ReadFile(self, start_record, record_count):
        """ Read a number of records starting at a specific record. """
        if _debug: LocalRecordAccessFileObject._debug("ReadFile %r %r",
                start_record, record_count,
                )

        # end of file is true if last record is returned
        end_of_file = (start_record+record_count) >= len(self._record_data)

        return end_of_file, \
            self._record_data[start_record:start_record + record_count]

    def WriteFile(self, start_record, record_count, record_data):
        """ Write a number of records, starting at a specific record. """
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

register_object_type(LocalRecordAccessFileObject)

#
#   Local Stream Access File Object Type
#

@bacpypes_debugging
class LocalStreamAccessFileObject(FileObject):

    def __init__(self, **kwargs):
        """ Initialize a stream accessed file object. """
        if _debug:
            LocalStreamAccessFileObject._debug("__init__ %r",
                kwargs,
                )
        FileObject.__init__(self,
            fileAccessMethod='streamAccess',
             **kwargs
             )

        self._file_data = ''.join(random.choice(string.ascii_letters)
            for i in range(random.randint(100, 200)))
        if _debug: LocalRecordAccessFileObject._debug("    - %d octets",
                len(self._file_data),
                )

    def __len__(self):
        """ Return the number of octets in the file. """
        if _debug: LocalStreamAccessFileObject._debug("__len__")

        return len(self._file_data)

    def ReadFile(self, start_position, octet_count):
        """ Read a chunk of data out of the file. """
        if _debug: LocalStreamAccessFileObject._debug("ReadFile %r %r",
                start_position, octet_count,
                )

        # end of file is true if last record is returned
        end_of_file = (start_position+octet_count) >= len(self._file_data)

        return end_of_file, \
            self._file_data[start_position:start_position + octet_count]

    def WriteFile(self, start_position, data):
        """ Write a number of octets, starting at a specific offset. """
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

register_object_type(LocalStreamAccessFileObject)

#
#   __main__
#

try:
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

    # build a bit string that knows about the bit names
    pss = ServicesSupported()
    pss['whoIs'] = 1
    pss['iAm'] = 1
    pss['readProperty'] = 1
    pss['writeProperty'] = 1
    pss['atomicReadFile'] = 1
    pss['atomicWriteFile'] = 1

    # set the property value to be just the bits
    this_device.protocolServicesSupported = pss.value

    # make a sample application
    this_application = BIPSimpleApplication(this_device, args.ini.address)

    # make a record access file, add to the device
    f1 = LocalRecordAccessFileObject(
        objectIdentifier=('file', 1),
        objectName='RecordAccessFile1'
        )
    _log.debug("    - f1: %r", f1)
    this_application.add_object(f1)

    # make a stream access file, add to the device
    f2 = LocalStreamAccessFileObject(
        objectIdentifier=('file', 2),
        objectName='StreamAccessFile2'
        )
    _log.debug("    - f2: %r", f2)
    this_application.add_object(f2)

    _log.debug("running")

    run()

except Exception, e:
    _log.exception("an error has occurred: %s", e)
finally:
    _log.debug("finally")
