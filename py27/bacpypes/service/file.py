#!/usr/bin/env python

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.object import FileObject

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

        if 'fileAccessMethod' in kwargs:
            if kwargs['fileAccessMethod'] != 'recordAccess':
                raise ValueError("inconsistent file access method")

        FileObject.__init__(self,
            fileAccessMethod='recordAccess',
             **kwargs
             )

    def __len__(self):
        """ Return the number of records. """
        raise NotImplementedError("__len__")

    def read_file(self, start_record, record_count):
        """ Read a number of records starting at a specific record. """
        raise NotImplementedError("read_file")

    def write_file(self, start_record, record_count, record_data):
        """ Write a number of records, starting at a specific record. """
        raise NotImplementedError("write_file")

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

        if 'fileAccessMethod' in kwargs:
            if kwargs['fileAccessMethod'] != 'streamAccess':
                raise ValueError("inconsistent file access method")

        FileObject.__init__(self,
            fileAccessMethod='streamAccess',
             **kwargs
             )

    def __len__(self):
        """ Return the number of octets in the file. """
        raise NotImplementedError("write_file")

    def read_file(self, start_position, octet_count):
        """ Read a chunk of data out of the file. """
        raise NotImplementedError("write_file")

    def write_file(self, start_position, data):
        """ Write a number of octets, starting at a specific offset. """
        raise NotImplementedError("write_file")

#
#   File Application Mixin
#

@bacpypes_debugging
class FileApplicationMixin(object):

    def __init__(self, *args, **kwargs):
        if _debug: FileApplicationMixin._debug("__init__")
        super(FileApplicationMixin, self).__init__(*args, **kwargs)

    def do_AtomicReadFileRequest(self, apdu):
        """Return one of our records."""
        if _debug: FileApplicationMixin._debug("do_AtomicReadFileRequest %r", apdu)

        if (apdu.fileIdentifier[0] != 'file'):
            resp = Error(errorClass='services', errorCode='inconsistentObjectType', context=apdu)
            if _debug: FileApplicationMixin._debug("    - error resp: %r", resp)
            self.response(resp)
            return

        # get the object
        obj = self.get_object_id(apdu.fileIdentifier)
        if _debug: FileApplicationMixin._debug("    - object: %r", obj)

        if not obj:
            resp = Error(errorClass='object', errorCode='unknownObject', context=apdu)
        elif apdu.accessMethod.recordAccess:
            # check against the object
            if obj.fileAccessMethod != 'recordAccess':
                resp = Error(errorClass='services',
                    errorCode='invalidFileAccessMethod',
                    context=apdu
                    )
            ### verify start is valid - double check this (empty files?)
            elif (apdu.accessMethod.recordAccess.fileStartRecord < 0) or \
                    (apdu.accessMethod.recordAccess.fileStartRecord >= len(obj)):
                resp = Error(errorClass='services',
                    errorCode='invalidFileStartPosition',
                    context=apdu
                    )
            else:
                # pass along to the object
                end_of_file, record_data = obj.ReadFile(
                    apdu.accessMethod.recordAccess.fileStartRecord,
                    apdu.accessMethod.recordAccess.requestedRecordCount,
                    )
                if _debug: FileApplicationMixin._debug("    - record_data: %r", record_data)

                # this is an ack
                resp = AtomicReadFileACK(context=apdu,
                    endOfFile=end_of_file,
                    accessMethod=AtomicReadFileACKAccessMethodChoice(
                        recordAccess=AtomicReadFileACKAccessMethodRecordAccess(
                            fileStartRecord=apdu.accessMethod.recordAccess.fileStartRecord,
                            returnedRecordCount=len(record_data),
                            fileRecordData=record_data,
                            ),
                        ),
                    )

        elif apdu.accessMethod.streamAccess:
            # check against the object
            if obj.fileAccessMethod != 'streamAccess':
                resp = Error(errorClass='services',
                    errorCode='invalidFileAccessMethod',
                    context=apdu
                    )
            ### verify start is valid - double check this (empty files?)
            elif (apdu.accessMethod.streamAccess.fileStartPosition < 0) or \
                    (apdu.accessMethod.streamAccess.fileStartPosition >= len(obj)):
                resp = Error(errorClass='services',
                    errorCode='invalidFileStartPosition',
                    context=apdu
                    )
            else:
                # pass along to the object
                end_of_file, record_data = obj.ReadFile(
                    apdu.accessMethod.streamAccess.fileStartPosition,
                    apdu.accessMethod.streamAccess.requestedOctetCount,
                    )
                if _debug: FileApplicationMixin._debug("    - record_data: %r", record_data)

                # this is an ack
                resp = AtomicReadFileACK(context=apdu,
                    endOfFile=end_of_file,
                    accessMethod=AtomicReadFileACKAccessMethodChoice(
                        streamAccess=AtomicReadFileACKAccessMethodStreamAccess(
                            fileStartPosition=apdu.accessMethod.streamAccess.fileStartPosition,
                            fileData=record_data,
                            ),
                        ),
                    )

        if _debug: FileApplicationMixin._debug("    - resp: %r", resp)

        # return the result
        self.response(resp)

    def do_AtomicWriteFileRequest(self, apdu):
        """Return one of our records."""
        if _debug: FileApplicationMixin._debug("do_AtomicWriteFileRequest %r", apdu)

        if (apdu.fileIdentifier[0] != 'file'):
            resp = Error(errorClass='services', errorCode='inconsistentObjectType', context=apdu)
            if _debug: FileApplicationMixin._debug("    - error resp: %r", resp)
            self.response(resp)
            return

        # get the object
        obj = self.get_object_id(apdu.fileIdentifier)
        if _debug: FileApplicationMixin._debug("    - object: %r", obj)

        if not obj:
            resp = Error(errorClass='object', errorCode='unknownObject', context=apdu)
        elif apdu.accessMethod.recordAccess:
            # check against the object
            if obj.fileAccessMethod != 'recordAccess':
                resp = Error(errorClass='services',
                    errorCode='invalidFileAccessMethod',
                    context=apdu
                    )
                if _debug: FileApplicationMixin._debug("    - error resp: %r", resp)
                self.response(resp)
                return

            # check for read-only
            if obj.readOnly:
                resp = Error(errorClass='services',
                    errorCode='fileAccessDenied',
                    context=apdu
                    )
                if _debug: FileApplicationMixin._debug("    - error resp: %r", resp)
                self.response(resp)
                return

            # pass along to the object
            start_record = obj.WriteFile(
                apdu.accessMethod.recordAccess.fileStartRecord,
                apdu.accessMethod.recordAccess.recordCount,
                apdu.accessMethod.recordAccess.fileRecordData,
                )
            if _debug: FileApplicationMixin._debug("    - start_record: %r", start_record)

            # this is an ack
            resp = AtomicWriteFileACK(context=apdu,
                fileStartRecord=start_record,
                )

        elif apdu.accessMethod.streamAccess:
            # check against the object
            if obj.fileAccessMethod != 'streamAccess':
                resp = Error(errorClass='services',
                    errorCode='invalidFileAccessMethod',
                    context=apdu
                    )
                if _debug: FileApplicationMixin._debug("    - error resp: %r", resp)
                self.response(resp)
                return

            # check for read-only
            if obj.readOnly:
                resp = Error(errorClass='services',
                    errorCode='fileAccessDenied',
                    context=apdu
                    )
                if _debug: FileApplicationMixin._debug("    - error resp: %r", resp)
                self.response(resp)
                return

            # pass along to the object
            start_position = obj.WriteFile(
                apdu.accessMethod.streamAccess.fileStartPosition,
                apdu.accessMethod.streamAccess.fileData,
                )
            if _debug: FileApplicationMixin._debug("    - start_position: %r", start_position)

            # this is an ack
            resp = AtomicWriteFileACK(context=apdu,
                fileStartPosition=start_position,
                )

        if _debug: FileApplicationMixin._debug("    - resp: %r", resp)

        # return the result
        self.response(resp)
