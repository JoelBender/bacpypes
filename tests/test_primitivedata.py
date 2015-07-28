# -*- coding: utf-8 -*-
"""
Created on Tue Mar 17 23:13:19 2015

@author: CTremblay
"""
import unittest
from bacpypes.comm import PDU
from bacpypes.primitivedata import TagList, Tag,Unsigned, Enumerated  
from bacpypes.debugging import btox, xtob

class TestPrimitive(unittest.TestCase):
    def setUp(self):
        self.hexHello = btox(b'hello','.')
        self.tlist = TagList()
        self.tg = Tag()
        self.p = PDU(b'')
        self.unsigned_1000 = Unsigned(1000)
        self.unsigned_5 = Unsigned(5)
        self.t_1000 = Tag()
        self.t_5 = Tag()
        self.enum = Enumerated(0)
               
    def test_strToHex(self):
        self.assertEqual(self.hexHello,'68.65.6c.6c.6f')     
    def test_HexToStr(self):
        self.assertEqual(xtob('68.65.6c.6c.6f','.'),b'hello')
        
    def test_Unsigned_Values(self):
        self.assertEqual(self.unsigned_1000.value,1000)
        self.assertEqual(self.unsigned_5.value,5)
    
    def test_Unsigned_Encoding(self):
        self.unsigned_1000.encode(self.t_1000)
        self.unsigned_5.encode(self.t_5)
        self.assertEqual(self.t_1000.tagData,b'\x03\xe8')
        self.assertEqual(self.t_5.tagData,b'\x05')
        
    def test_pdu_put_over256(self):
        with self.assertRaises(ValueError):
            self.p.put(257)
        
    def test_Enumerated(self):
        self.assertEqual(self.enum.value,0)
    def test_Enumerated_Encoding(self):
        self.enum.encode(self.tg)
        self.assertEqual(self.tg.tagData,b'\x00')
        

        
if __name__ == '__main__':
    unittest.main()