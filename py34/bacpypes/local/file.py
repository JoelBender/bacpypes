#!/usr/bin/env python

from ..debugging import bacpypes_debugging, ModuleLogger

from ..object import FileObject

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

        # verify the file access method or provide it
        if 'fileAccessMethod' in kwargs:
            if kwargs['fileAccessMethod'] != 'recordAccess':
                raise ValueError("inconsistent file access method")
        else:
            kwargs['fileAccessMethod'] = 'recordAccess'

        # continue with initialization
        FileObject.__init__(self, **kwargs)

    def __len__(self):
        """ Return the number of records. """
        raise NotImplementedError("__len__")

    def read_record(self, start_record, record_count):
        """ Read a number of records starting at a specific record. """
        raise NotImplementedError("read_record")

    def write_record(self, start_record, record_count, record_data):
        """ Write a number of records, starting at a specific record. """
        raise NotImplementedError("write_record")

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

        # verify the file access method or provide it
        if 'fileAccessMethod' in kwargs:
            if kwargs['fileAccessMethod'] != 'streamAccess':
                raise ValueError("inconsistent file access method")
        else:
            kwargs['fileAccessMethod'] = 'streamAccess'

        # continue with initialization
        FileObject.__init__(self, **kwargs)

    def __len__(self):
        """ Return the number of octets in the file. """
        raise NotImplementedError("write_file")

    def read_stream(self, start_position, octet_count):
        """ Read a chunk of data out of the file. """
        raise NotImplementedError("read_stream")

    def write_stream(self, start_position, data):
        """ Write a number of octets, starting at a specific offset. """
        raise NotImplementedError("write_stream")

