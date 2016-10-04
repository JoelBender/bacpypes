.. BACpypes file services

File Services
=============

.. class:: FileServices(Capability)

    This class provides the capability to read from and write to file objects.

    .. method:: do_AtomicReadFileRequest(apdu)

        :param AtomicReadFileRequest apdu: request from the network

        This method looks for a local file object by the object identifier
        and and passes the request parameters to the implementation of
        the record or stream support class instances.

    .. method:: do_AtomicWriteFileRequest(apdu)

        :param AtomicWriteFileRequest apdu: request from the network

        This method looks for a local file object by the object identifier
        and and passes the request parameters to the implementation of
        the record or stream support class instances.

Support Classes
---------------

.. class:: LocalRecordAccessFileObject(FileObject)

    This abstract class provides a simplified API for implementing a local
    record access file.  A derived class must provide implementations of
    these methods for the object to be used by the `FileServices`.

    .. method:: __len__()

        Return the length of the file in records.

    .. method:: read_record(start_record, record_count)

        :param int start_record: starting record
        :param int record_count: number of records

        Return a tuple (eof, record_data) where the `record_data` is an
        array of octet strings.

    .. method:: write_record(start_record, record_count, record_data)

        :param int start_record: starting record
        :param int record_count: number of records
        :param record_data: array of octet strings

        Update the file with the new records.

.. class:: LocalStreamAccessFileObject(FileObject)

    This abstract class provides a simplified API for implementing a local
    stream access file.  A derived class must provide implementations of
    these methods for the object to be used by the `FileServices`.

    .. method:: __len__()

        Return the length of the file in octets.

    .. method:: read_stream(start_position, octet_count)

        :param int start_position: starting position
        :param int octet_count: number of octets

        Return a tuple (eof, record_data) where the `record_data` is an
        array of octet strings.

    .. method:: write_stream(start_position, data)

        :param int start_position: starting position
        :param data: octet string

        Update the file with the new records.

.. class:: FileServicesClient(Capability)

    This class adds a set of functions to the application that provides a
    simplified client API for reading and writing to files.  It is not currently
    implemented.
