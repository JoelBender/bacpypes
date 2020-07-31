from bacpypes.local.decorator import bacnet_properties, commandable, add_feature, create
from bacpypes.local.object import MinOnOff


from bacpypes.object import (
    AnalogInputObject,
    AnalogValueObject,
    BinaryValueObject,
    DatePatternValueObject,
)
from bacpypes.primitivedata import CharacterString, Date, Time, Real, Boolean, Integer
from bacpypes.basetypes import EngineeringUnits, BinaryPV
from bacpypes.local.object import AnalogValueCmdObject, Commandable, MinOnOff

properties = {
    "outOfService": False,
    "relinquishDefault": 0,
    "units": "degreesCelsius",
    "highLimit": 98,
}


@bacnet_properties(properties)
@commandable()
def av(instance, objectName, presentValue, description):
    OBJECT_TYPE = AnalogValueObject
    return create(OBJECT_TYPE, instance, objectName, presentValue, description)


def av_ro(instance, objectName, presentValue, description):
    OBJECT_TYPE = AnalogValueObject
    return create(OBJECT_TYPE, instance, objectName, presentValue, description)


@add_feature(MinOnOff)
@commandable()
def bv(instance, objectName, presentValue, description):
    OBJECT_TYPE = BinaryValueObject
    return create(OBJECT_TYPE, instance, objectName, presentValue, description)


@commandable()
def bv_noMinOnOff(instance, objectName, presentValue, description):
    OBJECT_TYPE = BinaryValueObject
    return create(OBJECT_TYPE, instance, objectName, presentValue, description)


@commandable()
def datepattern(instance, objectName, presentValue, description):
    OBJECT_TYPE = DatePatternValueObject
    return create(OBJECT_TYPE, instance, objectName, presentValue, description)


def test_commandable():
    read_only_av = av_ro(1, "AV1", 0, "Read-Only AV")
    commandable_av = av(2, "AV2", 0, "Commandable AV")
    assert commandable_av.__dict__["_values"]["priorityArray"] is not None
    assert read_only_av.__dict__["_values"]["priorityArray"] is None


def test_added_properties():
    read_only_av = av_ro(1, "AV1", 0, "Read-Only AV")
    commandable_av = av(2, "AV2", 0, "Commandable AV")
    assert commandable_av.highLimit == 98
    assert read_only_av.highLimit is None


def test_MinOnOffAdded_to_bv():
    binary_value = bv(1, "BV1", "inactive", "New BV")
    assert MinOnOff in type(binary_value).__bases__
    binary_value = bv_noMinOnOff(1, "BV1", "inactive", "New BV")
    assert MinOnOff not in type(binary_value).__bases__
