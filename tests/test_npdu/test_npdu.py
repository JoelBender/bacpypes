# -*- coding: utf-8 -*-
"""
Created on Tue Mar 17 23:13:19 2015

@author: CTremblay
"""
import unittest
from bacpypes.debugging import btox
from bacpypes.comm import PDU

class TestNPDU(unittest.TestCase):
    def setUp(self):
        self.pdu = PDU(b"hello")
        self.pdu_source_dest = PDU(b"hello", source=1, destination=2)
        self.hexHello = btox(b'hello','.')
        self.pdu1 = PDU(b'hello!!')
        
        

    def test_byteToHex(self):
        self.assertEqual(self.hexHello,'68.65.6c.6c.6f')
        
        
if __name__ == '__main__':
    unittest.main()