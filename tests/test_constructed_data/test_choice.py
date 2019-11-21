#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test Choice
-----------
"""

import unittest

from bacpypes.basetypes import Scale
from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.primitivedata import Tag, TagList

# some debugging
_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
class TestScaleChoice(unittest.TestCase):
    def test_scale_choice(self):
        if _debug: TestScaleChoice._debug("test_scale_choice")
        taglist = TagList([Tag(1, 1, 1, bytearray(b'\x00'))])
        scale = Scale()
        scale.decode(taglist)
        self.assertDictEqual(scale.dict_contents(), {'integerScale': 0})
