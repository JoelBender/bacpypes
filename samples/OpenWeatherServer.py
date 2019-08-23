# -*- coding: utf-8 -*-

"""
OpenWeather Server

This sample application uses the https://openweathermap.org/ service to get
weather data and make it available over BACnet.  First sign up for an API
key called APPID and set an environment variable to that value.  You can also
change the units and update interval.
"""

import os
import requests
import time

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser

from bacpypes.core import run, deferred
from bacpypes.task import recurring_function

from bacpypes.basetypes import DateTime
from bacpypes.object import AnalogValueObject, DateTimeValueObject

from bacpypes.app import BIPSimpleApplication
from bacpypes.local.device import LocalDeviceObject

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# application ID is the API key from the service
APPID = os.getenv("APPID")

# units go into the request
APPUNITS = os.getenv("APPUNITS", "metric")

# application interval is refresh time in minutes (default 5)
APPINTERVAL = int(os.getenv("APPINTERVAL", 5)) * 60 * 1000

# request parameters are passed to the API, id is the city identifier
request_parameters = {"id": 7258390, "APPID": APPID, "units": APPUNITS}

# dictionary of names to objects
objects = {}


@bacpypes_debugging
class LocalAnalogValueObject(AnalogValueObject):
    def _set_value(self, value):
        if _debug:
            LocalAnalogValueObject._debug("_set_value %r", value)

        # numeric values are easy to set
        self.presentValue = value


# timezone offset is shared with the date time values
timezone_offset = 0


@bacpypes_debugging
class LocalDateTimeValueObject(DateTimeValueObject):
    def _set_value(self, utc_time):
        if _debug:
            LocalDateTimeValueObject._debug("_set_value %r", utc_time)

        # convert to a time tuple based on timezone offset
        time_tuple = time.gmtime(utc_time + timezone_offset)
        if _debug:
            LocalDateTimeValueObject._debug("    - time_tuple: %r", time_tuple)

        # extra the pieces
        date_quad = (
            time_tuple[0] - 1900,
            time_tuple[1],
            time_tuple[2],
            time_tuple[6] + 1,
        )
        time_quad = (time_tuple[3], time_tuple[4], time_tuple[5], 0)

        date_time = DateTime(date=date_quad, time=time_quad)
        if _debug:
            LocalDateTimeValueObject._debug("    - date_time: %r", date_time)

        self.presentValue = date_time


# result name, object class [, default units [, metric units, imperial units]]
parameters = [
    ("$.clouds.all", LocalAnalogValueObject, "percent"),
    ("$.main.humidity", LocalAnalogValueObject, "percentRelativeHumidity"),
    ("$.main.pressure", LocalAnalogValueObject, "hectopascals"),
    (
        "$.main.temp",
        LocalAnalogValueObject,
        "degreesKelvin",
        "degreesCelsius",
        "degreesFahrenheit",
    ),
    (
        "$.main.temp_max",
        LocalAnalogValueObject,
        "degreesKelvin",
        "degreesCelsius",
        "degreesFahrenheit",
    ),
    (
        "$.main.temp_min",
        LocalAnalogValueObject,
        "degreesKelvin",
        "degreesCelsius",
        "degreesFahrenheit",
    ),
    ("$.sys.sunrise", LocalDateTimeValueObject),
    ("$.sys.sunset", LocalDateTimeValueObject),
    ("$.visibility", LocalAnalogValueObject, "meters"),
    ("$.wind.deg", LocalAnalogValueObject, "degreesAngular"),
    (
        "$.wind.speed",
        LocalAnalogValueObject,
        "metersPerSecond",
        "metersPerSecond",
        "milesPerHour",
    ),
]


@bacpypes_debugging
def create_objects(app):
    """Create the objects that hold the result values."""
    if _debug:
        create_objects._debug("create_objects %r", app)
    global objects

    next_instance = 1
    for parms in parameters:
        if _debug:
            create_objects._debug("    - name: %r", parms[0])

        if len(parms) == 2:
            units = None
        elif len(parms) == 3:
            units = parms[2]
        elif APPUNITS == "metric":
            units = parms[3]
        elif APPUNITS == "imperial":
            units = parms[4]
        else:
            units = parms[2]
        if _debug:
            create_objects._debug("    - units: %r", units)

        # create an object
        obj = parms[1](
            objectName=parms[0], objectIdentifier=(parms[1].objectType, next_instance)
        )
        if _debug:
            create_objects._debug("    - obj: %r", obj)

        # set the units
        if units is not None:
            obj.units = units

        # add it to the application
        app.add_object(obj)

        # keep track of the object by name
        objects[parms[0]] = obj

        # bump the next instance number
        next_instance += 1


def flatten(x, prefix="$"):
    """Turn a JSON object into (key, value) tuples using JSON-Path like names
    for the keys."""
    if type(x) is dict:
        for a in x:
            yield from flatten(x[a], prefix + "." + a)
    elif type(x) is list:
        for i, y in enumerate(x):
            yield from flatten(y, prefix + "[" + str(i) + "]")
    else:
        yield (prefix, x)


@recurring_function(APPINTERVAL)
@bacpypes_debugging
def update_weather_data():
    """Read the current weather data from the API and set the object values."""
    if _debug:
        update_weather_data._debug("update_weather_data")
    global objects, timezone_offset

    # ask the web service
    response = requests.get(
        "http://api.openweathermap.org/data/2.5/weather", request_parameters
    )
    if response.status_code != 200:
        print("Error response: %r" % (response.status_code,))
        return

    # turn the response string into a JSON object
    json_response = response.json()

    # flatten the JSON object into key/value pairs and build a dict
    dict_response = dict(flatten(json_response))

    # extract the timezone offset
    timezone_offset = dict_response.get("$.timezone", 0)
    if _debug:
        update_weather_data._debug("    - timezone_offset: %r", timezone_offset)

    #  set the object values
    for k, v in dict_response.items():
        if _debug:
            update_weather_data._debug("    - k, v: %r, %r", k, v)

        if k in objects:
            objects[k]._set_value(v)


@bacpypes_debugging
def main():
    global vendor_id

    # parse the command line arguments
    args = ConfigArgumentParser(description=__doc__).parse_args()

    if _debug:
        _log.debug("initialization")
    if _debug:
        _log.debug("    - args: %r", args)

    # make a device object
    this_device = LocalDeviceObject(ini=args.ini)
    if _debug:
        _log.debug("    - this_device: %r", this_device)

    # make a sample application
    this_application = BIPSimpleApplication(this_device, args.ini.address)

    # create the objects and add them to the application
    create_objects(this_application)

    # run this update when the stack is ready
    deferred(update_weather_data)

    if _debug:
        _log.debug("running")

    run()

    if _debug:
        _log.debug("fini")


if __name__ == "__main__":
    main()
