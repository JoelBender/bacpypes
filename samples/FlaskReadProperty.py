#!/usr/bin/env python

"""
A web server based on flask that reads properties from objects and returns an
HTML page of the results.
"""

from flask import Flask
from jinja2 import Template
from threading import Thread

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser

from bacpypes.core import run, stop, enable_sleeping
from bacpypes.iocb import IOCB

from bacpypes.pdu import Address
from bacpypes.apdu import ReadPropertyRequest, ReadPropertyACK
from bacpypes.primitivedata import Unsigned, ObjectIdentifier
from bacpypes.constructeddata import Array

from bacpypes.app import BIPSimpleApplication
from bacpypes.object import get_datatype
from bacpypes.local.device import LocalDeviceObject

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
this_application = None
flask_app = Flask(__name__)

# template point name, device address, object identifier, property
point_list = [
    ('some_point', '10.0.1.14', 'analogValue:1', 'presentValue'),
    ('another_point', '10.0.1.14', 'analogValue:2', 'presentValue'),
    ]

result_template = Template("""
<!DOCTYPE html>
<html>
  <head>
    <title>Flask Template Example</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
  </head>
  <body>
    <div>
      <p>Read results:</p>
      <ul>
        {% for point_name, point_value in result_values %}
        <li>{{point_name}} = {{point_value}}</li>
        {% endfor %}
      </ul>
    </div>
  </body>
</html>
    """)


@flask_app.route('/')
@bacpypes_debugging
def hello():
    if _debug: hello._debug("hello")

    result_values = []

    for point_name, device_address, obj_id, prop_id in point_list:
        try:
            obj_id = ObjectIdentifier(obj_id).value
            datatype = get_datatype(obj_id[0], prop_id)
            if not datatype:
                raise ValueError("invalid property for object type")

            # build a request
            request = ReadPropertyRequest(
                objectIdentifier=obj_id,
                propertyIdentifier=prop_id,
                )
            request.pduDestination = Address(device_address)
            if _debug: hello._debug("    - request: %r", request)

            # make an IOCB
            iocb = IOCB(request)
            if _debug: hello._debug("    - iocb: %r", iocb)

            # give it to the application
            this_application.request_io(iocb)

            # wait for it to complete
            iocb.wait()

            # do something for error/reject/abort
            if iocb.ioError:
                result_values.append((point_name, str(iocb.ioError)))

            # do something for success
            elif iocb.ioResponse:
                apdu = iocb.ioResponse

                # should be an ack
                if not isinstance(apdu, ReadPropertyACK):
                    if _debug: hello._debug("    - not an ack")
                    return

                # find the datatype
                datatype = get_datatype(apdu.objectIdentifier[0], apdu.propertyIdentifier)
                if _debug: hello._debug("    - datatype: %r", datatype)
                if not datatype:
                    raise TypeError("unknown datatype")

                # special case for array parts, others are managed by cast_out
                if issubclass(datatype, Array) and (apdu.propertyArrayIndex is not None):
                    if apdu.propertyArrayIndex == 0:
                        value = apdu.propertyValue.cast_out(Unsigned)
                    else:
                        value = apdu.propertyValue.cast_out(datatype.subtype)
                else:
                    value = apdu.propertyValue.cast_out(datatype)
                if _debug: hello._debug("    - value: %r", value)

                result_values.append((point_name, str(value)))

            # do something with nothing?
            else:
                if _debug: hello._debug("    - ioError or ioResponse expected")

        except Exception as error:
            hello._exception("exception: %r", error)
            result_values.append((point_name, str(error)))

    # render the results with the template
    return result_template.render(result_values=result_values)


#
#   __main__
#

def main():
    global this_application

    # parse the command line arguments
    args = ConfigArgumentParser(description=__doc__).parse_args()

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("    - args: %r", args)

    # make a device object
    this_device = LocalDeviceObject(ini=args.ini)
    if _debug: _log.debug("    - this_device: %r", this_device)

    # make a simple application
    this_application = BIPSimpleApplication(this_device, args.ini.address)

    _log.debug("running")

    # set up the core to be a little happier with threads
    enable_sleeping()

    # create a thread for the core and start it
    bacpypes_thread = Thread(target=run)
    bacpypes_thread.start()

    flask_app.run(threaded=False)

    if _debug: _log.debug("stopping")

    # terminate the BACpypes thread
    stop()
    bacpypes_thread.join()

    _log.debug("fini")

if __name__ == "__main__":
    main()

