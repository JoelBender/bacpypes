from functools import wraps, partial

from bacpypes.object import (
    AnalogInputObject,
    AnalogValueObject,
    BinaryValueObject,
    Property,
    register_object_type,
    registered_object_types,
    DatePatternValueObject,
)
from bacpypes.primitivedata import CharacterString, Date, Time, Real, Boolean, Integer
from bacpypes.basetypes import EngineeringUnits, BinaryPV
from bacpypes.local.object import AnalogValueCmdObject, Commandable, MinOnOff

_SHOULD_BE_WRITABLE = ["relinquishDefault", "outOfService", "lowLimit", "highLimit"]

"""
Template

Decorators is an effort to handle object creation without explicitly declare a new class
depending on the properties or features required.



# Usage

## bacnet_properties
This decorator takes a dict as argument defining supplmental properties

## bacnet_property
This decorator takes a simple property and its default value, adds it to object

## Commandable
This decoratore will modify the base class and create a new class that inherit from _commando (see local.object.py)

## Add feature
This decorator works the same than commandable. Could serve as a way to add behaviour like MinOnOff, events, limits, etc...

## Example::

    properties = {"outOfService" : False,
                "relinquishDefault" : 0,
                "units": "degreesCelsius",
                "highLimit": 98}

    @bacnet_properties(properties)
    @commandable()
    def av(instance, objectName, presentValue, description):
        OBJECT_TYPE = AnalogValueObject
        return create(OBJECT_TYPE,instance, objectName, presentValue, description)

    @add_feature(MinOnOff)
    @commandable()
    def bv(instance, objectName, presentValue, description):
        OBJECT_TYPE = BinaryValueObject
        return create(OBJECT_TYPE,instance, objectName, presentValue, description)

    @commandable()
    def datepattern(instance, objectName, presentValue, description):
        OBJECT_TYPE = DatePatternValueObject
        return create(OBJECT_TYPE,instance, objectName, presentValue, description)

    ### The creation takes place when the functions are called
    a = av(1,'AnalogValueName',10,'AnalogValue Description')
    b = bv(1,'BV Name','inactive','BinaryValue Description')
    c = datepattern(1,'My Date Pattern',None,'DatePattern Description')

"""


def _allowed_prop(obj):
    allowed_prop = {}
    for each in type(obj).properties:
        allowed_prop[each.identifier] = each.datatype
    for base in type(obj).__bases__:
        try:
            for each in base.properties:
                allowed_prop[each.identifier] = each.datatype
        except AttributeError:
            pass
    return allowed_prop


def _mutable(property_name, force_mutable=False):
    if property_name in _SHOULD_BE_WRITABLE and not force_mutable:
        mutable = True
    elif force_mutable:
        mutable = force_mutable
    else:
        mutable = False
    return mutable


def commandable():
    def decorate(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if callable(func):
                obj = func(*args, **kwargs)
            else:
                obj = func
            allowed_prop = _allowed_prop(obj)
            _type = allowed_prop["presentValue"]
            _commando = Commandable(_type)
            base_cls = obj.__class__
            base_cls_name = obj.__class__.__name__ + "Cmd"
            new_type = type(base_cls_name, (_commando, base_cls), {})
            register_object_type(new_type, vendor_id=0)
            instance, objectName, presentValue, description = args
            new_object = new_type(
                objectIdentifier=(base_cls.objectType, instance),
                objectName="{}".format(objectName),
                presentValue=presentValue,
                description=CharacterString("{}".format(presentValue)),
            )
            return new_object

        return wrapper

    return decorate


def add_feature(cls):
    def decorate(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if callable(func):
                obj = func(*args, **kwargs)
            else:
                obj = func
            base_cls = obj.__class__
            base_cls_name = obj.__class__.__name__ + cls.__name__
            new_type = type(base_cls_name, (cls, base_cls), {})
            register_object_type(new_type, vendor_id=0)
            instance, objectName, presentValue, description = args
            new_object = new_type(
                objectIdentifier=(base_cls.objectType, instance),
                objectName="{}".format(objectName),
                presentValue=presentValue,
                description=CharacterString("{}".format(presentValue)),
            )
            return new_object

        return wrapper

    return decorate


def bacnet_property(property_name, value, *, force_mutable=None):
    def decorate(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if callable(func):
                obj = func(*args, **kwargs)
            else:
                obj = func
            allowed_prop = _allowed_prop(obj)
            mutable = _mutable(property_name)
            if property_name == "units":
                new_prop = EngineeringUnits.enumerations[value]
                obj.units = new_prop
            else:
                try:
                    new_prop = Property(
                        property_name,
                        allowed_prop[property_name],
                        default=value,
                        mutable=mutable,
                    )
                except KeyError:
                    raise ValueError(
                        "Invalid property ({}) for object".format(property_name)
                    )
                obj.add_property(new_prop)
            return obj

        return wrapper

    return decorate


def bacnet_properties(properties):
    def decorate(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if callable(func):
                obj = func(*args, **kwargs)
            else:
                obj = func
            allowed_prop = _allowed_prop(obj)

            for property_name, value in properties.items():
                if property_name == "units":
                    new_prop = EngineeringUnits.enumerations[value]
                    obj.units = new_prop
                else:
                    try:
                        mutable = _mutable(property_name)
                        new_prop = Property(
                            property_name,
                            allowed_prop[property_name],
                            default=value,
                            mutable=mutable,
                        )
                    except KeyError:
                        raise ValueError(
                            "Invalid property ({}) for object".format(property_name)
                        )
                    obj.add_property(new_prop)
            return obj

        return wrapper

    return decorate


def create(object_type, instance, objectName, presentValue, description):
    new_object = object_type(
        objectIdentifier=(object_type.objectType, instance),
        objectName="{}".format(objectName),
        presentValue=presentValue,
        description=CharacterString("{}".format(presentValue)),
    )
    return new_object
