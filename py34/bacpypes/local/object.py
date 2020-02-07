#!/usr/bin/env python

import re

from ..debugging import bacpypes_debugging, ModuleLogger

from ..task import OneShotTask
from ..primitivedata import Atomic, Null, BitString, CharacterString, \
    Date, Integer, Double, Enumerated, OctetString, Real, Time, Unsigned
from ..basetypes import PropertyIdentifier, DateTime, NameValue, BinaryPV, \
    ChannelValue, DoorValue, PriorityValue, PriorityArray
from ..constructeddata import Array, ArrayOf, SequenceOf

from ..errors import ExecutionError
from ..object import Property, ReadableProperty, WritableProperty, OptionalProperty, Object, \
    AccessDoorObject, AnalogOutputObject, AnalogValueObject, \
    BinaryOutputObject, BinaryValueObject, BitStringValueObject, CharacterStringValueObject, \
    DateValueObject, DatePatternValueObject, DateTimePatternValueObject, \
    DateTimeValueObject, IntegerValueObject, \
    LargeAnalogValueObject, LightingOutputObject, MultiStateOutputObject, \
    MultiStateValueObject, OctetStringValueObject, PositiveIntegerValueObject, \
    TimeValueObject, TimePatternValueObject, ChannelObject


# some debugging
_debug = 0
_log = ModuleLogger(globals())

# handy reference
ArrayOfPropertyIdentifier = ArrayOf(PropertyIdentifier)

#
#   CurrentPropertyList
#

@bacpypes_debugging
class CurrentPropertyList(Property):

    def __init__(self):
        if _debug: CurrentPropertyList._debug("__init__")
        Property.__init__(self, 'propertyList', ArrayOfPropertyIdentifier, default=None, optional=True, mutable=False)

    def ReadProperty(self, obj, arrayIndex=None):
        if _debug: CurrentPropertyList._debug("ReadProperty %r %r", obj, arrayIndex)

        # make a list of the properties that have values
        property_list = [k for k, v in obj._values.items()
            if v is not None
                and k not in ('objectName', 'objectType', 'objectIdentifier', 'propertyList')
            ]
        if _debug: CurrentPropertyList._debug("    - property_list: %r", property_list)

        # sort the list so it's stable
        property_list.sort()

        # asking for the whole thing
        if arrayIndex is None:
            return ArrayOfPropertyIdentifier(property_list)

        # asking for the length
        if arrayIndex == 0:
            return len(property_list)

        # asking for an index
        if arrayIndex > len(property_list):
            raise ExecutionError(errorClass='property', errorCode='invalidArrayIndex')
        return property_list[arrayIndex - 1]

    def WriteProperty(self, obj, value, arrayIndex=None, priority=None, direct=False):
        raise ExecutionError(errorClass='property', errorCode='writeAccessDenied')

#
#   CurrentPropertyListMixIn
#

@bacpypes_debugging
class CurrentPropertyListMixIn(Object):

    properties = [
        CurrentPropertyList(),
        ]

#
#   Turtle Reference Patterns
#

# character reference patterns
HEX = u"[0-9A-Fa-f]"
PERCENT = u"%" + HEX + HEX
UCHAR = u"[\\\]u" + HEX * 4 + "|" + u"[\\\]U" + HEX * 8

# character sets
PN_CHARS_BASE = (
    u"A-Za-z"
    u"\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u02FF\u0370-\u037D\u037F-\u1FFF"
    u"\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF"
    u"\uFDF0-\uFFFD\U00010000-\U000EFFFF"
)

PN_CHARS_U = PN_CHARS_BASE + u"_"
PN_CHARS = u"-" + PN_CHARS_U + u"0-9\u00B7\u0300-\u036F\u203F-\u2040"

# patterns
IRIREF = u'[<]([^\u0000-\u0020<>"{}|^`\\\]|' + UCHAR + u")*[>]"
PN_PREFIX = u"[" + PN_CHARS_BASE + u"](([." + PN_CHARS + u"])*[" + PN_CHARS + u"])?"

PN_LOCAL_ESC = u"[-\\_~.!$&'()*+,;=/?#@%]"
PLX = u"(" + PERCENT + u"|" + PN_LOCAL_ESC + u")"

# non-prefixed names
PN_LOCAL = (
    u"(["
    + PN_CHARS_U
    + u":0-9]|"
    + PLX
    + u")((["
    + PN_CHARS
    + u".:]|"
    + PLX
    + u")*(["
    + PN_CHARS
    + u":]|"
    + PLX
    + u"))?"
)

# namespace prefix declaration
PNAME_NS = u"(" + PN_PREFIX + u")?:"

# prefixed names
PNAME_LN = PNAME_NS + PN_LOCAL

# blank nodes
BLANK_NODE_LABEL = (
    u"_:[" + PN_CHARS_U + u"0-9]([" + PN_CHARS + u".]*[" + PN_CHARS + u"])?"
)

# see https://www.w3.org/TR/turtle/#sec-parsing-terms
iriref_re = re.compile(u"^" + IRIREF + u"$", re.UNICODE)
local_name_re = re.compile(u"^" + PN_LOCAL + u"$", re.UNICODE)
namespace_prefix_re = re.compile(u"^" + PNAME_NS + u"$", re.UNICODE)
prefixed_name_re = re.compile(u"^" + PNAME_LN + u"$", re.UNICODE)
blank_node_re = re.compile(u"^" + BLANK_NODE_LABEL + u"$", re.UNICODE)

# see https://tools.ietf.org/html/bcp47#section-2.1 for better syntax
language_tag_re = re.compile(u"^[A-Za-z0-9-]+$", re.UNICODE)

class IRI:
    # regex from RFC 3986
    _e = r"^(?:([^:/?#]+):)?(?://([^/?#]*))?([^?#]*)(?:\?([^#]*))?(?:#(.*))?"
    _p = re.compile(_e)
    _default_ports = (("http", ":80"), ("https", ":443"))

    def __init__(self, iri=None):
        self.iri = iri

        if not iri:
            g = (None, None, None, None, None)
        else:
            m = IRI._p.match(iri)
            if not m:
                raise ValueError("not an IRI")

            # remove default http and https ports
            g = list(m.groups())
            for scheme, suffix in IRI._default_ports:
                if (g[0] == scheme) and g[1] and g[1].endswith(suffix):
                    g[1] = g[1][: g[1].rfind(":")]
                    break

        self.scheme, self.authority, self.path, self.query, self.fragment = g

    def __str__(self):
        rval = ""
        if self.scheme:
            rval += self.scheme + ":"
        if self.authority is not None:
            rval += "//" + self.authority
        if self.path is not None:
            rval += self.path
        if self.query is not None:
            rval += "?" + self.query
        if self.fragment is not None:
            rval += "#" + self.fragment
        return rval

    def is_local_name(self):
        if not all(
            (
                self.scheme is None,
                self.authority is None,
                self.path,
                self.query is None,
                self.fragment is None,
            )
        ):
            return False
        if self.path.startswith(":") or "/" in self.path:  # term is not ':x'
            return False
        return True

    def is_prefix(self):
        if not all((self.authority is None, self.query is None, self.fragment is None)):
            return False
        if self.scheme:
            return self.path == ""  # term is 'x:'
        else:
            return self.path == ":"  # term is ':'

    def is_prefixed_name(self):
        if not all((self.authority is None, self.query is None, self.fragment is None)):
            return False
        if self.scheme:
            return self.path != ""  # term is 'x:y'
        else:  # term is ':y' but not ':'
            return self.path and (self.path != ":") and self.path.startswith(":")

    def resolve(self, iri):
        """Resolve a relative IRI to this IRI as a base."""
        # parse the IRI if necessary
        if isinstance(iri, str):
            iri = IRI(iri)
        elif not isinstance(iri, IRI):
            raise TypeError("iri must be an IRI or a string")

        # return an IRI object
        rslt = IRI()

        if iri.scheme and iri.scheme != self.scheme:
            rslt.scheme = iri.scheme
            rslt.authority = iri.authority
            rslt.path = iri.path
            rslt.query = iri.query
        else:
            rslt.scheme = self.scheme

            if iri.authority is not None:
                rslt.authority = iri.authority
                rslt.path = iri.path
                rslt.query = iri.query
            else:
                rslt.authority = self.authority

                if not iri.path:
                    rslt.path = self.path
                    if iri.query is not None:
                        rslt.query = iri.query
                    else:
                        rslt.query = self.query
                else:
                    if iri.path.startswith("/"):
                        # IRI represents an absolute path
                        rslt.path = iri.path
                    else:
                        # merge paths
                        path = self.path

                        # append relative path to the end of the last
                        # directory from base
                        path = path[0 : path.rfind("/") + 1]
                        if len(path) > 0 and not path.endswith("/"):
                            path += "/"
                        path += iri.path

                        rslt.path = path

                    rslt.query = iri.query

            # normalize path
            if rslt.path != "":
                rslt.remove_dot_segments()

        rslt.fragment = iri.fragment

        return rslt

    def remove_dot_segments(self):
        # empty path shortcut
        if len(self.path) == 0:
            return

        input_ = self.path.split("/")
        output_ = []

        while len(input_) > 0:
            next = input_.pop(0)
            done = len(input_) == 0

            if next == ".":
                if done:
                    # ensure output has trailing /
                    output_.append("")
                continue

            if next == "..":
                if len(output_) > 0:
                    output_.pop()
                if done:
                    # ensure output has trailing /
                    output_.append("")
                continue

            output_.append(next)

        # ensure output has leading /
        if len(output_) > 0 and output_[0] != "":
            output_.insert(0, "")
        if len(output_) == 1 and output_[0] == "":
            return "/"

        self.path = "/".join(output_)


@bacpypes_debugging
class TagSet:
    def index(self, name, value=None):
        """Find the first name with dictionary semantics or (name, value) with
        list semantics."""
        if _debug: TagSet._debug("index %r %r", name, value)

        # if this is a NameValue rip it apart first
        if isinstance(name, NameValue):
            name, value = name.name, name.value

        # no value then look for first matching name
        if value is None:
            for i, v in enumerate(self.value):
                if isinstance(v, int):
                    continue
                if name == v.name:
                    return i
            else:
                raise KeyError(name)

        # skip int values, it is the zeroth element of an array but does
        # not exist for a list
        for i, v in enumerate(self.value):
            if isinstance(v, int):
                continue
            if (
                name == v.name
                and isinstance(value, type(v.value))
                and value.value == v.value.value
            ):
                return i
        else:
            raise ValueError((name, value))

    def add(self, name, value=None):
        """Add a (name, value) with mutable set semantics."""
        if _debug: TagSet._debug("add %r %r", name, value)

        # provide a Null if you are adding a is-a relationship, wrap strings
        # to be friendly
        if value is None:
            value = Null()
        elif isinstance(value, str):
            value = CharacterString(value)

        # name is a string
        if not isinstance(name, str):
            raise TypeError("name must be a string, got %r" % (type(name),))

        # reserved directive names
        if name.startswith("@"):
            if name == "@base":
                if not isinstance(value, CharacterString):
                    raise TypeError("value must be an string")

                v = self.get('@base')
                if v and v.value == value.value:
                    pass
                else:
                    raise ValueError("@base exists")

#               if not iriref_re.match(value.value):
#                   raise ValueError("value must be an IRI")

            elif name == "@id":
                if not isinstance(value, CharacterString):
                    raise TypeError("value must be an string")

                v = self.get('@id')
                if v and v.value == value.value:
                    pass
                else:
                    raise ValueError("@id exists")

#               # check the patterns
#               for pattern in (blank_node_re, prefixed_name_re, local_name_re, iriref_re):
#                   if pattern.match(value.value):
#                       break
#               else:
#                   raise ValueError("invalid value for @id")

            elif name == "@language":
                if not isinstance(value, CharacterString):
                    raise TypeError("value must be an string")

                v = self.get("@language")
                if v and v.value == value.value:
                    pass
                else:
                    raise ValueError("@language exists")

                if not language_tag_re.match(value.value):
                    raise ValueError("value must be a language tag")

            elif name == "@vocab":
                if not isinstance(value, CharacterString):
                    raise TypeError("value must be an string")

                v = self.get('@vocab')
                if v and v.value == value.value:
                    pass
                else:
                    raise ValueError("@vocab exists")

            else:
                raise ValueError("invalid directive name")

        elif name.endswith(":"):
            if not isinstance(value, CharacterString):
                raise TypeError("value must be an string")

            v = self.get(name)
            if v and v.value == value.value:
                pass
            else:
                raise ValueError("prefix exists: %r" % (name,))

#           if not iriref_re.match(value.value):
#               raise ValueError("value must be an IRI")

        else:
#           # check the patterns
#           for pattern in (prefixed_name_re, local_name_re, iriref_re):
#               if pattern.match(name):
#                   break
#           else:
#               raise ValueError("invalid name")
            pass

        # check the value
        if not isinstance(value, (Atomic, DateTime)):
            raise TypeError("invalid value")

        # see if the (name, value) already exists
        try:
            self.index(name, value)
        except ValueError:
            super(TagSet, self).append(NameValue(name=name, value=value))

    def discard(self, name, value=None):
        """Discard a (name, value) with mutable set semantics."""
        if _debug: TagSet._debug("discard %r %r", name, value)

        # provide a Null if you are adding a is-a relationship, wrap strings
        # to be friendly
        if value is None:
            value = Null()
        elif isinstance(value, str):
            value = CharacterString(value)

        indx = self.index(name, value)
        return super(TagSet, self).__delitem__(indx)

    def append(self, name_value):
        """Override the append operation for mutable set semantics."""
        if _debug: TagSet._debug("append %r", name_value)

        if not isinstance(name_value, NameValue):
            raise TypeError

        # turn this into an add operation
        self.add(name_value.name, name_value.value)

    def get(self, key, default=None):
        """Get the value of a key or default value if the key was not found,
        dictionary semantics."""
        if _debug: TagSet._debug("get %r %r", key, default)

        try:
            if not isinstance(key, str):
                raise TypeError(key)
            return self.value[self.index(key)].value
        except KeyError:
            return default

    def __getitem__(self, item):
        """If item is an integer, return the value of the NameValue element
        with array/sequence semantics. If the item is a string, return the
        value with dictionary semantics."""
        if _debug: TagSet._debug("__getitem__ %r", item)

        # integers imply index
        if isinstance(item, int):
            return super(TagSet, self).__getitem__(item)

        return self.value[self.index(item)]

    def __setitem__(self, item, value):
        """If item is an integer, change the value of the NameValue element
        with array/sequence semantics. If the item is a string, change the
        current value or add a new value with dictionary semantics."""
        if _debug: TagSet._debug("__setitem__ %r %r", item, value)

        # integers imply index
        if isinstance(item, int):
            indx = item
            if indx < 0:
                raise IndexError("assignment index out of range")
            elif isinstance(self, Array):
                if indx == 0 or indx > len(self.value):
                    raise IndexError
            elif indx >= len(self.value):
                raise IndexError
        elif isinstance(item, str):
            try:
                indx = self.index(item)
            except KeyError:
                self.add(item, value)
                return
        else:
            raise TypeError(repr(item))

        # check the value
        if value is None:
            value = Null()
        elif not isinstance(value, (Atomic, DateTime)):
            raise TypeError("invalid value")

        # now we're good to go
        self.value[indx].value = value

    def __delitem__(self, item):
        """If the item is a integer, delete the element with array semantics, or
        if the item is a string, delete the element with dictionary semantics,
        or (name, value) with mutable set semantics."""
        if _debug: TagSet._debug("__delitem__ %r", item)

        # integers imply index
        if isinstance(item, int):
            indx = item
        elif isinstance(item, str):
            indx = self.index(item)
        elif isinstance(item, tuple):
            indx = self.index(*item)
        else:
            raise TypeError(item)

        return super(TagSet, self).__delitem__(indx)

    def __contains__(self, key):
        if _debug: TagSet._debug("__contains__ %r", key)

        try:
            if isinstance(key, tuple):
                self.index(*key)
            elif isinstance(key, str):
                self.index(key)
            else:
                raise TypeError(key)

            return True
        except (KeyError, ValueError):
            return False


class ArrayOfNameValue(TagSet, ArrayOf(NameValue)):
    pass


class SequenceOfNameValue(TagSet, SequenceOf(NameValue)):
    pass


class TagsMixIn(Object):
    properties = \
        [ OptionalProperty('tags', ArrayOfNameValue)
        ]


@bacpypes_debugging
def Commandable(datatype, presentValue='presentValue', priorityArray='priorityArray', relinquishDefault='relinquishDefault'):
    if _debug: Commandable._debug("Commandable %r ...", datatype)

    class _Commando(object):

        properties = [
            WritableProperty(presentValue, datatype),
            ReadableProperty(priorityArray, PriorityArray),
            ReadableProperty(relinquishDefault, datatype),
            ]

        _pv_choice = None

        def __init__(self, **kwargs):
            if _debug: Commandable._debug("_Commando.__init__(%r, %r, %r, %r) %r", datatype, presentValue, priorityArray, relinquishDefault, kwargs)
            super(_Commando, self).__init__(**kwargs)

            # build a default value in case one is needed
            default_value = datatype().value
            if issubclass(datatype, Enumerated):
                default_value = datatype._xlate_table[default_value]
            if _debug: Commandable._debug("    - default_value: %r", default_value)

            # see if a present value was provided
            if (presentValue not in kwargs):
                setattr(self, presentValue, default_value)

            # see if a priority array was provided
            if (priorityArray not in kwargs):
                setattr(self, priorityArray, PriorityArray())

            # see if a present value was provided
            if (relinquishDefault not in kwargs):
                setattr(self, relinquishDefault, default_value)

        def _highest_priority_value(self):
            if _debug: Commandable._debug("_highest_priority_value")

            priority_array = getattr(self, priorityArray)
            for i in range(1, 17):
                priority_value = priority_array[i]
                if priority_value.null is None:
                    if _debug: Commandable._debug("    - found at index: %r", i)

                    value = getattr(priority_value, _Commando._pv_choice)
                    value_source = "###"

                    if issubclass(datatype, Enumerated):
                        value = datatype._xlate_table[value]
                        if _debug: Commandable._debug("    - remapped enumeration: %r", value)

                    break
            else:
                value = getattr(self, relinquishDefault)
                value_source = None

            if _debug: Commandable._debug("    - value, value_source: %r, %r", value, value_source)

            # return what you found
            return value, value_source

        def WriteProperty(self, property, value, arrayIndex=None, priority=None, direct=False):
            if _debug: Commandable._debug("WriteProperty %r %r arrayIndex=%r priority=%r direct=%r", property, value, arrayIndex, priority, direct)

            # when writing to the presentValue with a priority
            if (property == presentValue):
                if _debug: Commandable._debug("    - writing to %s, priority %r", presentValue, priority)

                # default (lowest) priority
                if priority is None:
                    priority = 16
                if _debug: Commandable._debug("    - translate to priority array, index %d", priority)

                # translate to updating the priority array
                property = priorityArray
                arrayIndex = priority
                priority = None

            # update the priority array entry
            if (property == priorityArray):
                if (arrayIndex is None):
                    if _debug: Commandable._debug("    - writing entire %s", priorityArray)

                    # pass along the request
                    super(_Commando, self).WriteProperty(
                        property, value,
                        arrayIndex=arrayIndex, priority=priority, direct=direct,
                        )
                else:
                    if _debug: Commandable._debug("    - writing to %s, array index %d", priorityArray, arrayIndex)

                    # check the bounds
                    if arrayIndex == 0:
                        raise ExecutionError(errorClass='property', errorCode='writeAccessDenied')
                    if (arrayIndex < 1) or (arrayIndex > 16):
                        raise ExecutionError(errorClass='property', errorCode='invalidArrayIndex')

                    # update the specific priorty value element
                    priority_value = getattr(self, priorityArray)[arrayIndex]
                    if _debug: Commandable._debug("    - priority_value: %r", priority_value)

                    # the null or the choice has to be set, the other clear
                    if value == ():
                        if _debug: Commandable._debug("    - write a null")
                        priority_value.null = value
                        setattr(priority_value, _Commando._pv_choice, None)
                    else:
                        if _debug: Commandable._debug("    - write a value")

                        if issubclass(datatype, Enumerated):
                            value = datatype._xlate_table[value]
                            if _debug: Commandable._debug("    - remapped enumeration: %r", value)

                        priority_value.null = None
                        setattr(priority_value, _Commando._pv_choice, value)

                # look for the highest priority value
                value, value_source = self._highest_priority_value()

                # compare with the current value
                current_value = getattr(self, presentValue)
                if value == current_value:
                    if _debug: Commandable._debug("    - no present value change")
                    return

                # turn this into a present value change
                property = presentValue
                arrayIndex = priority = None

            # allow the request to pass through
            if _debug: Commandable._debug("    - super: %r %r arrayIndex=%r priority=%r", property, value, arrayIndex, priority)

            super(_Commando, self).WriteProperty(
                property, value,
                arrayIndex=arrayIndex, priority=priority, direct=direct,
                )

    # look up a matching priority value choice
    for element in PriorityValue.choiceElements:
        if issubclass(datatype, element.klass):
            _Commando._pv_choice = element.name
            break
    else:
        _Commando._pv_choice = 'constructedValue'
    if _debug: Commandable._debug("    - _pv_choice: %r", _Commando._pv_choice)

    # return the class
    return _Commando

#
#   MinOnOffTask
#

@bacpypes_debugging
class MinOnOffTask(OneShotTask):

    def __init__(self, binary_obj):
        if _debug: MinOnOffTask._debug("__init__ %s", repr(binary_obj))
        OneShotTask.__init__(self)

        # save a reference to the object
        self.binary_obj = binary_obj

        # listen for changes to the present value
        self.binary_obj._property_monitors['presentValue'].append(self.present_value_change)

    def present_value_change(self, old_value, new_value):
        if _debug: MinOnOffTask._debug("present_value_change %r %r", old_value, new_value)

        # if there's no value change, skip all this
        if old_value == new_value:
            if _debug: MinOnOffTask._debug("    - no state change")
            return

        # get the minimum on/off time
        if new_value == 'inactive':
            task_delay = getattr(self.binary_obj, 'minimumOnTime') or 0
            if _debug: MinOnOffTask._debug("    - minimum on: %r", task_delay)
        elif new_value == 'active':
            task_delay = getattr(self.binary_obj, 'minimumOffTime') or 0
            if _debug: MinOnOffTask._debug("    - minimum off: %r", task_delay)
        else:
            raise ValueError("unrecognized present value for %r: %r" % (self.binary_obj.objectIdentifier, new_value))

        # if there's no delay, don't bother
        if not task_delay:
            if _debug: MinOnOffTask._debug("    - no delay")
            return

        # set the value at priority 6
        self.binary_obj.WriteProperty('presentValue', new_value, priority=6)

        # install this to run, if there is a delay
        self.install_task(delta=task_delay)

    def process_task(self):
        if _debug: MinOnOffTask._debug("process_task(%s)", self.binary_obj.objectName)

        # clear the value at priority 6
        self.binary_obj.WriteProperty('presentValue', (), priority=6)

#
#   MinOnOff
#

@bacpypes_debugging
class MinOnOff(object):

    def __init__(self, **kwargs):
        if _debug: MinOnOff._debug("__init__ ...")
        super(MinOnOff, self).__init__(**kwargs)

        # create the timer task
        self._min_on_off_task = MinOnOffTask(self)

#
#   Commandable Standard Objects
#

class AccessDoorCmdObject(Commandable(DoorValue), AccessDoorObject):
    pass

class AnalogOutputCmdObject(Commandable(Real), AnalogOutputObject):
    pass

class AnalogValueCmdObject(Commandable(Real), AnalogValueObject):
    pass

### class BinaryLightingOutputCmdObject(Commandable(Real), BinaryLightingOutputObject):
###     pass

class BinaryOutputCmdObject(Commandable(BinaryPV), MinOnOff, BinaryOutputObject):
    pass

class BinaryValueCmdObject(Commandable(BinaryPV), MinOnOff, BinaryValueObject):
    pass

class BitStringValueCmdObject(Commandable(BitString), BitStringValueObject):
    pass

class CharacterStringValueCmdObject(Commandable(CharacterString), CharacterStringValueObject):
    pass

class DateValueCmdObject(Commandable(Date), DateValueObject):
    pass

class DatePatternValueCmdObject(Commandable(Date), DatePatternValueObject):
    pass

class DateTimeValueCmdObject(Commandable(DateTime), DateTimeValueObject):
    pass

class DateTimePatternValueCmdObject(Commandable(DateTime), DateTimePatternValueObject):
    pass

class IntegerValueCmdObject(Commandable(Integer), IntegerValueObject):
    pass

class LargeAnalogValueCmdObject(Commandable(Double), LargeAnalogValueObject):
    pass

class LightingOutputCmdObject(Commandable(Real), LightingOutputObject):
    pass

class MultiStateOutputCmdObject(Commandable(Unsigned), MultiStateOutputObject):
    pass

class MultiStateValueCmdObject(Commandable(Unsigned), MultiStateValueObject):
    pass

class OctetStringValueCmdObject(Commandable(OctetString), OctetStringValueObject):
    pass

class PositiveIntegerValueCmdObject(Commandable(Unsigned), PositiveIntegerValueObject):
    pass

class TimeValueCmdObject(Commandable(Time), TimeValueObject):
    pass

class TimePatternValueCmdObject(Commandable(Time), TimePatternValueObject):
    pass

@bacpypes_debugging
class ChannelValueProperty(Property):

    def __init__(self):
        if _debug: ChannelValueProperty._debug("__init__")
        Property.__init__(self, 'presentValue', ChannelValue, default=None, optional=False, mutable=True)

    def WriteProperty(self, obj, value, arrayIndex=None, priority=None, direct=False):
        if _debug: ChannelValueProperty._debug("WriteProperty %r %r arrayIndex=%r priority=%r direct=%r", obj, value, arrayIndex, priority, direct)

        ### Clause 12.53.5, page 487
        raise NotImplementedError()

class ChannelCmdObject(ChannelObject):

    properties = [
        ChannelValueProperty(),
        ]
