.. BACpypes command logging module

.. module:: commandlogging

Command Logging
===============

The follow set of classes are used to provide access to the defined loggers as
a client or a service.  For example, instances of these classes can be stacked
on top of a UDP or TCP director to provide debugging to remote devices or to 
BACpypes applications running as a daemon where there is no interactive command
capability.

.. class:: CommandLoggingHandler(logging.Handler)

    This is a long line of text.

    .. method:: __init__(self, commander, destination, loggerName)

        :param commander: record to format
        :param destination: record to format
        :param loggerName: record to format

        This is a long line of text.

    .. method:: emit(self, record)

        :param commander: record to format

        This is a long line of text.

.. class:: CommandLogging(Logging)

    This is a long line of text.

    .. attribute:: handlers

        This is a long line of text.

    .. method:: process_command(self, cmd, addr)

        :param cmd: command message to be processed
        :param addr: address of source of request/response

        This is a long line of text.

    .. method:: emit(self, msg, addr)

        :param msg: message to send
        :param addr: address to send request/response

        This is a long line of text.

.. class:: CommandLoggingServer(CommandLogging, Server, Logging)

    This is a long line of text.

    .. method:: indication(pdu)

        :param pdu: command message to be processed

        This is a long line of text.

    .. method:: emit(self, msg, addr)

        :param msg: message to send
        :param addr: address to send response

        This is a long line of text.

.. class:: CommandLoggingClient(CommandLogging, Client, Logging)

    This is a long line of text.

    .. method:: confirmation(pdu)

        :param pdu: command message to be processed

        This is a long line of text.

    .. method:: emit(self, msg, addr)

        :param msg: message to send
        :param addr: address to send request

        This is a long line of text.
