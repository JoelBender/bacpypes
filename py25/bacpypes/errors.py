#!/usr/bin/python

#
#   ConfigurationError
#

class ConfigurationError(ValueError):

    """ This error is raised when there is a configuration problem such as
        bindings between layers or required parameters that are missing. """

    def __init__(self, *args):
        self.args = args

#
#   EncodingError
#

class EncodingError(ValueError):

    """ This error is raised if there is a problem during encoding. """

    def __init__(self, *args):
        self.args = args

#
#   DecodingError
#

class DecodingError(ValueError):

    """ This error is raised if there is a problem during decoding. """

    def __init__(self, *args):
        self.args = args

#
#   ExecutionError
#

class ExecutionError(RuntimeError):

    """ This error is raised for if there is an error during the execution of
        a service or function at the application layer of stack and the error
        translated into an ErrorPDU. """

    def __init__(self, errorClass, errorCode):
        self.errorClass = errorClass
        self.errorCode = errorCode
        self.args = (errorClass, errorCode)
