.. BACpypes updating applications

Version 0.14.1 to 0.15.0
========================

This update contains a significant number of changes to the way the project
code is organized.  This is a guide to updating applications that use BACpypes
to fit the new API.

The guide is divided into a series of sections for each type of change.

LocalDeviceObject
-----------------

There is a new `service` sub-package where the functionality to support a
specific type of behavior is in a separate module.  The module names within
the `service` sub-package are inspired by and very similar to the names of
Clauses 13 through 17.

The `bacpypes.service.device` module now contains the definition of the
`LocalDeviceObject` as well as mix-in classes to support Who-Is, I-Am, Who-Has,
and I-Have services.

If your application contained this::

    from bacpypes.app import LocalDeviceObject, BIPSimpleApplication

Update it to contain this::

    from bacpypes.app import BIPSimpleApplication
    from bacpypes.service.device import LocalDeviceObject

Application Subclasses
----------------------

The `Application` class in the `bacpypes.app` module no longer supports
services by default, they are mixed into derived classes as needed.  There
are very few applications that actually took advantage of the `AtomicReadFile`
and `AtomicWriteFile` services, so when these were moved to their own
service module `bacpypes.service.file` it seems natural to move the
implementations of the other services to other modules as well.

Moving this code to separate modules will facilitate BACpypes applications
building additional service modules to mix into the default ones or replace
default implementations with ones more suited to their local application
requirements.

The exception to this is the `BIPSimpleApplication`, is the most commonly used
derived class from `Application` and I anticipated that by having it include
`WhoIsIAmServices` and `ReadWritePropertyServices` allowed existing applications
to run with fewer changes.

If your application contained this::

    class MyApplication(Application):
        ...

And you want to keep the old behavior, replace it with this::

    from bacpypes.service.device import WhoIsIAmServices
    from bacpypes.service.object import ReadWritePropertyServices

    class MyApplication(Application, WhoIsIAmServices, ReadWritePropertyServices):
        ...

Client-only Applications
------------------------

The `Application` class no longer requires a value for the `localDevice` or
`localAddress` parameters.  BACpypes applications like that omit these
parameters will only be able to initiate confirmed or unconfirmed services that
do not require these objects or values.  They would not be able to respond to
Who-Is requests for example.

Client-only applications are useful when it would be advantageous to avoid the
administrative overhead for configuring something as a device, such as
network analysis applications and very simple trend data gather applications.
They are also useful for BACpypes applications that run in a Docker container
or "in the cloud".

Sample client-only applications will be forthcoming.

Simplified Requests
-------------------

Some of the service modules now have additional functions that make it easier
to initiate requests.  For example, in the `WhoIsIAmServices` class there are
functions for initiating a Who-Is request by a simple function::

    def who_is(self, low_limit=None, high_limit=None, address=None):
        ...

Validating the parameters, building the `WhoIsRequest` PDU and sending it
downstream is all handled by the function.

If your application builds common requests then you can use the new
functions or continue without them.  If there are common requests that you
would like to make and have built into the library your suggestions are
always welcome.

