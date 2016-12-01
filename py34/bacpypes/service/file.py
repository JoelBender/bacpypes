#!/usr/bin/env python

from ..debugging import bacpypes_debugging, ModuleLogger
from ..capability import Capability

from ..object import FileObject

from ..apdu import AtomicReadFileACK, AtomicReadFileACKAccessMethodChoice, \
    AtomicReadFileACKAccessMethodRecordAccess, \
    AtomicReadFileACKAccessMethodStreamAccess, \
    AtomicWriteFileACK
from ..errors import ExecutionError, MissingRequiredParameter

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

#
#   File Application Mixin
#

@bacpypes_debugging
class FileServices(Capability):

    def __init__(self):
        if _debug: FileServices._debug("__init__")
        Capability.__init__(self)

    def do_AtomicReadFileRequest(self, apdu):
        """Return one of our records."""
        if _debug: FileServices._debug("do_AtomicReadFileRequest %r", apdu)

        if (apdu.fileIdentifier[0] != 'file'):
            raise ExecutionError('services', 'inconsistentObjectType')

        # get the object
        obj = self.get_object_id(apdu.fileIdentifier)
        if _debug: FileServices._debug("    - object: %r", obj)

        if not obj:
            raise ExecutionError('object', 'unknownObject')

        if apdu.accessMethod.recordAccess:
            # check against the object
            if obj.fileAccessMethod != 'recordAccess':
                raise ExecutionError('services', 'invalidFileAccessMethod')

            # simplify
            record_access = apdu.accessMethod.recordAccess

            # check for required parameters
            if record_access.fileStartRecord is None:
                raise MissingRequiredParameter("fileStartRecord required")
            if record_access.requestedRecordCount is None:
                raise MissingRequiredParameter("requestedRecordCount required")

            ### verify start is valid - double check this (empty files?)
            if (record_access.fileStartRecord < 0) or \
                    (record_access.fileStartRecord >= len(obj)):
                raise ExecutionError('services', 'invalidFileStartPosition')

            # pass along to the object
            end_of_file, record_data = obj.read_record(
                record_access.fileStartRecord,
                record_access.requestedRecordCount,
                )
            if _debug: FileServices._debug("    - record_data: %r", record_data)

            # this is an ack
            resp = AtomicReadFileACK(context=apdu,
                endOfFile=end_of_file,
                accessMethod=AtomicReadFileACKAccessMethodChoice(
                    recordAccess=AtomicReadFileACKAccessMethodRecordAccess(
                        fileStartRecord=record_access.fileStartRecord,
                        returnedRecordCount=len(record_data),
                        fileRecordData=record_data,
                        ),
                    ),
                )

        elif apdu.accessMethod.streamAccess:
            # check against the object
            if obj.fileAccessMethod != 'streamAccess':
                raise ExecutionError('services', 'invalidFileAccessMethod')

            # simplify
            stream_access = apdu.accessMethod.streamAccess

            # check for required parameters
            if stream_access.fileStartPosition is None:
                raise MissingRequiredParameter("fileStartPosition required")
            if stream_access.requestedOctetCount is None:
                raise MissingRequiredParameter("requestedOctetCount required")

            ### verify start is valid - double check this (empty files?)
            if (stream_access.fileStartPosition < 0) or \
                    (stream_access.fileStartPosition >= len(obj)):
                raise ExecutionError('services', 'invalidFileStartPosition')

            # pass along to the object
            end_of_file, record_data = obj.read_stream(
                stream_access.fileStartPosition,
                stream_access.requestedOctetCount,
                )
            if _debug: FileServices._debug("    - record_data: %r", record_data)

            # this is an ack
            resp = AtomicReadFileACK(context=apdu,
                endOfFile=end_of_file,
                accessMethod=AtomicReadFileACKAccessMethodChoice(
                    streamAccess=AtomicReadFileACKAccessMethodStreamAccess(
                        fileStartPosition=stream_access.fileStartPosition,
                        fileData=record_data,
                        ),
                    ),
                )

        if _debug: FileServices._debug("    - resp: %r", resp)

        # return the result
        self.response(resp)

    def do_AtomicWriteFileRequest(self, apdu):
        """Return one of our records."""
        if _debug: FileServices._debug("do_AtomicWriteFileRequest %r", apdu)

        if (apdu.fileIdentifier[0] != 'file'):
            raise ExecutionError('services', 'inconsistentObjectType')

        # get the object
        obj = self.get_object_id(apdu.fileIdentifier)
        if _debug: FileServices._debug("    - object: %r", obj)

        if not obj:
            raise ExecutionError('object', 'unknownObject')

        if apdu.accessMethod.recordAccess:
            # check against the object
            if obj.fileAccessMethod != 'recordAccess':
                raise ExecutionError('services', 'invalidFileAccessMethod')

            # simplify
            record_access = apdu.accessMethod.recordAccess

            # check for required parameters
            if record_access.fileStartRecord is None:
                raise MissingRequiredParameter("fileStartRecord required")
            if record_access.recordCount is None:
                raise MissingRequiredParameter("recordCount required")
            if record_access.fileRecordData is None:
                raise MissingRequiredParameter("fileRecordData required")

            # check for read-only
            if obj.readOnly:
                raise ExecutionError('services', 'fileAccessDenied')

            # pass along to the object
            start_record = obj.write_record(
                record_access.fileStartRecord,
                record_access.recordCount,
                record_access.fileRecordData,
                )
            if _debug: FileServices._debug("    - start_record: %r", start_record)

            # this is an ack
            resp = AtomicWriteFileACK(context=apdu,
                fileStartRecord=start_record,
                )

        elif apdu.accessMethod.streamAccess:
            # check against the object
            if obj.fileAccessMethod != 'streamAccess':
                raise ExecutionError('services', 'invalidFileAccessMethod')

            # simplify
            stream_access = apdu.accessMethod.streamAccess

            # check for required parameters
            if stream_access.fileStartPosition is None:
                raise MissingRequiredParameter("fileStartPosition required")
            if stream_access.fileData is None:
                raise MissingRequiredParameter("fileData required")

            # check for read-only
            if obj.readOnly:
                raise ExecutionError('services', 'fileAccessDenied')

            # pass along to the object
            start_position = obj.write_stream(
                stream_access.fileStartPosition,
                stream_access.fileData,
                )
            if _debug: FileServices._debug("    - start_position: %r", start_position)

            # this is an ack
            resp = AtomicWriteFileACK(context=apdu,
                fileStartPosition=start_position,
                )

        if _debug: FileServices._debug("    - resp: %r", resp)

        # return the result
        self.response(resp)

#
#   FileServicesClient
#

class FileServicesClient(Capability):

    def read_record(self, address, fileIdentifier, start_record, record_count):
        """ Read a number of records starting at a specific record. """
        raise NotImplementedError("read_record")

    def write_record(self, address, fileIdentifier, start_record, record_count, record_data):
        """ Write a number of records, starting at a specific record. """
        raise NotImplementedError("write_record")

    def read_stream(self, address, fileIdentifier, start_position, octet_count):
        """ Read a chunk of data out of the file. """
        raise NotImplementedError("read_stream")

    def write_stream(self, address, fileIdentifier, start_position, data):
        """ Write a number of octets, starting at a specific offset. """
        raise NotImplementedError("write_stream")
