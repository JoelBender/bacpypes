#!/usr/bin/python

"""
ExtendedTagList
===============

An extended tag list adds a loads() function which takes a blob of text
and parses it into a list of tags using the following mini language:

    opening [tag] [context] n
    closing [tag] [context] n
    null  [ [context] n ]
    boolean (false | true) [ [context] n ]
    unsigned [0-9]+ [ [context] n ]
    integer [+-][0-9]+ [ [context] n ]
    real [+-][0-9]+([.][0-9]+)? [ [context] n ]
    double [+-][0-9]+([.][0-9]+)? [ [context] n ]
    octet [string] OCTETSTR [ [context] n ]
    [character] string ([0-9]+)? CHARSTR [ [context] n ]
    bit [string] BITSTR [ [context] n ]
    enumerated [0-9]+ [ [context] n ]
    date DATESTR [ [context] n ]
    time TIMESTR [ [context] n ]
    object [identifier] OBJTYPE [,] OBJINST [ [context] n ]

Blank lines and everything after the comment '#' is ignored.

The OCTETSTR is an optional sequence of pairs of hex characters.

The CHARSTR can be single quoted (') or double quoted (").

The BITSTR is an optional sequence of 0 or 1 digits.

The DATESTR and TIMESTR are patterns matched by associated primitive data
type classes Date and Time.

The OBJTYPE can be a name such as analogInput, or an unsigned integer, the
OBJINST is an unsigned integer.
"""

import sys
import re

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, xtob
from bacpypes.consolelogging import ArgumentParser

from bacpypes.primitivedata import Tag, TagList, OpeningTag, ClosingTag, \
    Atomic, Null, Boolean, Unsigned, Integer, \
    Real, Double, OctetString, CharacterString, BitString, Enumerated, \
    Date, Time, ObjectIdentifier

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
statements = []

statement_pattern = r"""
    ^
    \s*                                         # leading white space
    (%s)                                        # keyword
    ( (\s+context)? \s+ (?P<context>[0-9]+))?   # optional context
    ([#].*)?                                    # optional comment
    $"""

statement_value_pattern = r"""
    ^
    \s*                                         # leading white space
    (%s) \s+ (?P<value>%s)                      # keyword and value
    ( (\s+context)? \s+ (?P<context>[0-9]+))?   # optional context
    \s* ([#].*)?                                # optional comment
    $"""

#
#   blank lines
#

blank_line_pattern = r"""
    ^ \s*                                       # leading white space
    ([#].*)? $                                  # optional comment
    """

def blank_line_statement(value):
    return None

statements.append((blank_line_statement,
        re.compile(blank_line_pattern, re.VERBOSE + re.IGNORECASE),
        ))

#
#   SyntaxError
#

class SyntaxError(RuntimeError):

    pass

#
#   statement decorator
#

@bacpypes_debugging
def statement(pattern):
    if _debug: statement._debug("statement %r", pattern)

    @bacpypes_debugging
    def compile(fn):
        if _debug: statement._debug("compile %r", fn)

        # build a pattern
        if ' ' in pattern:
            fn_pattern = statement_value_pattern % tuple(pattern.split())
        else:
            fn_pattern = statement_pattern % (pattern,)
        if _debug: statement._debug("    - fn_pattern: %s", fn_pattern)

        # compile it
        fn_re = re.compile(fn_pattern, re.VERBOSE + re.IGNORECASE)

        statements.append((fn, fn_re))

        return fn

    return compile

#
#   statements
#

@statement(r"opening(\s+tag)?(\s+context)? [0-9]+")
@bacpypes_debugging
def opening_tag_statement(value):
    if _debug: opening_tag_statement._debug("opening_tag_statement %r", value)

    return OpeningTag(int(value))

@statement(r"closing(\s+tag)?(\s+context)? [0-9]+")
@bacpypes_debugging
def closing_tag_statement(value):
    if _debug: closing_tag_statement._debug("closing_tag_statement %r", value)

    return ClosingTag(int(value))

@statement(r"null")
@bacpypes_debugging
def null_statement(value):
    if _debug: null_statement._debug("null_statement %r", value)

    return Null()

@statement(r"boolean false|true")
@bacpypes_debugging
def boolean_statement(value):
    if _debug: boolean_statement._debug("boolean_statement %r", value)

    return Boolean(value)

@statement(r"unsigned [0-9]+")
@bacpypes_debugging
def unsigned_statement(value):
    if _debug: unsigned_statement._debug("unsigned_statement %r", value)

    return Unsigned(int(value))

@statement(r"integer [+-]?[0-9]+")
@bacpypes_debugging
def integer_statement(value):
    if _debug: integer_statement._debug("integer_statement %r", value)

    return Integer(int(value))

@statement(r"real [+-]?[0-9]+([.][0-9]+)?|nan")
@bacpypes_debugging
def real_statement(value):
    if _debug: real_statement._debug("real_statement %r", value)

    return Real(float(value))

@statement(r"double [+-]?[0-9]+([.][0-9]+)?|nan")
@bacpypes_debugging
def double_statement(value):
    if _debug: double_statement._debug("double_statement %r", value)

    return Double(float(value))

@statement(r"octet(\s+string)? ([0-9A-Fa-f][0-9A-Fa-f][.]?)*")
@bacpypes_debugging
def octet_string_statement(value):
    if _debug: octet_string_statement._debug("octet_string_statement %r", value)

    return OctetString(xtob(value.replace('.', '')))

@statement(r"""(character\s+)?string ([0-9]+\s+)?(?P<q>['"]).*(?P=q)""")
@bacpypes_debugging
def character_string_statement(value):
    if _debug: character_string_statement._debug("character_string_statement %r", value)

    # chop off the encoding
    encoding = None
    if value and value[0].isdigit():
        encoding, value = value.split(' ', 1)
        value = value.strip()
        if _debug: ExtendedTagList._debug("    - encoding: %r", encoding)

    # chop off the quotes
    if value:
        value = value[1:-1]

    element = CharacterString(value)
    if encoding:
        element.strEncoding = int(encoding)

    return element

@statement(r"bit(\s+string)? [01]*")
@bacpypes_debugging
def bit_string_statement(value):
    if _debug: bit_string_statement._debug("bit_string_statement %r", value)

    return BitString([int(c) for c in value])

@statement(r"enumerated [0-9]+")
@bacpypes_debugging
def enumerated_statement(value):
    if _debug: enumerated_statement._debug("enumerated_statement %r", value)

    return Enumerated(int(value))

@statement(r"date [*\w/-]+(\s+[*\w]+)?")
@bacpypes_debugging
def date_statement(value):
    if _debug: date_statement._debug("date_statement %r", value)

    return Date(value)

@statement(r"time [*\d:.]+")
@bacpypes_debugging
def time_statement(value):
    if _debug: time_statement._debug("time_statement %r", value)

    return Time(value)

@statement(r"object(\s+identifier)? [\w]+(\s+|\s*[,]\s*)[\d]+")
@bacpypes_debugging
def object_identifier_statement(value):
    if _debug: object_identifier_statement._debug("object_identifier_statement %r", value)

    # split into two pieces
    object_type, object_instance = re.split('[, ]+', value)

    if object_type.isdigit():
        object_type = int(object_type)
    if _debug: object_identifier_statement._debug("    - object_type: %r", object_type)

    object_instance = int(object_instance)
    if _debug: object_identifier_statement._debug("    - object_instance: %r", object_instance)

    return ObjectIdentifier(object_type, object_instance)

#
#   statement_to_tag
#

@bacpypes_debugging
def statement_to_tag(line):
    """Parse a line of text and return the appropriate tag."""
    if _debug: statement_to_tag._debug("statement_to_tag %r", line)

    # look for a matching statement pattern
    for stmt_fn, stmt_re in statements:
        match = stmt_re.match(line)
        if match:
            break
    else:
        raise SyntaxError("syntax error: %r" % (line,))

    # extract the pieces captured by the pattern
    match_groups = match.groupdict()
    value = match_groups.get('value', None)
    context = match_groups.get('context', None)
    if _debug: statement_to_tag._debug("    - value: %r", value)
    if _debug: statement_to_tag._debug("    - context: %r", context)

    # let the function work on the value, skip blank lines
    element = stmt_fn(value)
    if not element:
        return None

    # check for element already a tag
    if isinstance(element, Tag):
        tag = element
        if context is not None:
            raise SyntaxError("syntax error: %r" % (line,))

    elif isinstance(element, Atomic):
        tag = Tag()
        element.encode(tag)
        if _debug: statement_to_tag._debug("    - encoded tag: %r", tag)

        if context is not None:
            tag = tag.app_to_context(int(context))
            if _debug: statement_to_tag._debug("    - with context: %r", tag)

    else:
        raise TypeError("element must be a tag or atomic")
    if _debug: statement_to_tag._debug("    - tag: %r", tag)

    return tag

#
#   ExtendedTagList
#

@bacpypes_debugging
class ExtendedTagList(TagList):

    def __init__(self, text=""):
        if _debug: ExtendedTagList._debug("__init__ %r", text)
        TagList.__init__(self)

        # if it was given, load it
        if text:
            self.loads(text)

    def loads(self, text):
        if _debug: ExtendedTagList._debug("loads '%s...'", text[:20])

        # split the text into lines
        lines = re.split('[\r\n]+', text)

        # load each line
        for line in lines:
            tag = statement_to_tag(line)

            # no tag is a blank line
            if not tag:
                continue

            self.append(tag)

    def dumps(self):
        return ''

#
#   __main__
#

@bacpypes_debugging
def main():
    if _debug: main._debug("main")

    # parse the command line arguments
    args = ArgumentParser(description=__doc__).parse_args()
    if _debug: main._debug("    - args: %r", args)

    # suck in the test content
    text = sys.stdin.read()

    # parse it
    tag_list = ExtendedTagList(text)

    # dump it back out
    for tag in tag_list:
        tag.debug_contents()

if __name__ == "__main__":
    main()
