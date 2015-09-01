# -*- coding: utf-8 -*-
"""
Created on Tue Mar 17 23:13:19 2015

@author: CTremblay
"""
import unittest
from bacpypes.comm import PDU 
from bacpypes.debugging import btox, xtob

class TestPDU(unittest.TestCase):
    def setUp(self):
        self.pdu = PDU(b"hello")
        self.pdu_source_dest = PDU(b"hello", source=1, destination=2)
        self.hexHello = btox(b'hello','.')
        self.pdu1 = PDU(b'hello!!')
        
    def test_simplePDU(self):
        # parse command line options
        self.assertEqual(self.pdu.pduData,b'hello')
        
    
    def test_PDUWithAddress(self):
        # parse command line options
        self.assertEqual(self.pdu_source_dest.pduDestination,2)
        self.assertEqual(self.pdu_source_dest.pduSource,1) 
        self.assertEqual(self.pdu.pduData,b'hello')
        

    def test_strToHex(self):
        self.assertEqual(self.hexHello,'68.65.6c.6c.6f')
        
    def test_HexToStr(self):
        self.assertEqual(xtob('68.65.6c.6c.6f','.'),b'hello')
        
    def test_pduGetAndPut(self):
        self.assertEqual(self.pdu1.get(),104) #get the first letter : h
        #self.assertEqual(self.pdu1.get_short(),25964)
        #self.assertEqual(self.pdu1.get_long(),1819222305)
        self.pdu1.put(105)
        self.assertEqual(self.pdu1.get_short(),25964) 
        self.assertEqual(self.pdu1.get_long(),1819222305)
               
        
    #def test_HexToStr(self):
    #    self.assertEqual(_hex_to_str(self.hexHello),'hello')

        
if __name__ == '__main__':
    unittest.main()