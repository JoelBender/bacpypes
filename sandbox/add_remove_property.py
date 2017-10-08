
from bacpypes.basetypes import PropertyIdentifier
from bacpypes.constructeddata import ArrayOf
from bacpypes.object import AnalogValueObject

# create an array of property identifiers datatype
ArrayOfPropertyIdentifier = ArrayOf(PropertyIdentifier)

aopi = ArrayOfPropertyIdentifier()
aopi.append('objectName')
aopi.append('objectType')
aopi.append('description')
aopi.debug_contents()

aopi.remove('objectType')
aopi.debug_contents()

print("Create an Analog Value Object")
av = AnalogValueObject(
    objectName='av-sample',
    objectIdentifier=('analogValue', 1),
    description="sample",
    )
av.debug_contents()
print("")

print("Change the description")
av.description = "something else"
av.debug_contents()
print("")


# get the description property by the attribute name
description_property = av._attr_to_property('description')
print("description_property = %r" % (description_property,))
print("")

print("Delete the property")
av.delete_property(description_property)
print("...property deleted")

try:
    av.description = "this raises an exception"
except Exception as err:
    print(repr(err))
av.debug_contents()
print("")

print("===== Add the property")
av.add_property(description_property)
print("...property added")

try:
    av.description = "this works"
except Exception as err:
    print(repr(err))
av.debug_contents()
print("")

