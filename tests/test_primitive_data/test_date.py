#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test date
----------------------------
"""

import unittest

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.primitivedata import Date

# some debugging
_debug = 0
_log = ModuleLogger(globals())


@bacpypes_debugging
class TestDate(unittest.TestCase):
    def setUp(self):
    # test_values are tuple with str, year, month, date, dow
    # year, month, day, dayOfWeek are expected reaulsts
    
        self.test_values = [
            #('1/2/3', 1903, 2, 1, 0),
            #('1/2/3', 1903, 2, 1, 0),
            ("1/2/2003", 2003, 2, 1, 6),
            ("1/20/2003", 2003, 1, 20, 1),
            ("01/20/2004", 2004, 1, 20, 2),
            ("11/12/2005", 2005, 12, 11, 7),
            ("30/1/2006", 2006, 1, 30, 1),
            ("30/1/1230", 1230, 1, 30, 255),
            ("30/1/98", 1998, 1, 30, 5),
            ("2015/8/31", 2015, 8, 31, 1),
            ("2015/08/30", 2015, 8, 30, 7),
            ("2015/*/30", 2015,255,30,255),
            ("2015/1/*",2015,1,255,255),
            ("*/1/*", 255,1,255,255),
            ("*/*/*",255,255,255,255),
            ("1-2-2003", 2003, 2, 1, 6),
            ("1-20-2003", 2003, 1, 20, 1),
            ("01-20-2004", 2004, 1, 20, 2),
            ("11-12-2005", 2005, 12, 11, 7),
            ("30-1-2006", 2006, 1, 30, 1),
            ("30-1-1230", 1230, 1, 30, 255),
            ("30-1-98", 1998, 1, 30, 5),
            ("2015-8-31", 2015, 8, 31, 1),
            ("2015-08-30", 2015, 8, 30, 7),
            ("2015-*-30", 2015,255,30,255),
            ("2015-1-*",2015,1,255,255),
            ("*-1-*", 255,1,255,255),
            ("*-*-*",255,255,255,255)
        ]
        
        self.notEnoughPreciseOrWrong = [
            ('1/31/1'),
            ('0/1/4'),
            ('99/13/41'),
            ("2015/30/*")        
        ]
        
        
    def test_Date_from_str(self):
        for each in self.test_values:
            new_date = Date(each[0])
            y, m, d, dow = new_date.value
            self.assertEqual(y,each[1])
            self.assertEqual(m,each[2])
            self.assertEqual(d,each[3])
            self.assertEqual(dow,each[4])
            
    def test_Wrong(self):
        with self.assertRaises(ValueError):        
            for each in self.notEnoughPreciseOrWrong:
                new_date = Date(each[0])
            
            
            