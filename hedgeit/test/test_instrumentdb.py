'''
Created on Apr 22, 2013

@author: rtw
'''
import unittest

import os
from hedgeit.feeds.db import InstrumentDb

class Test(unittest.TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass


    def testBasic(self):
        manifest = '%s/data/manifest.csv' % os.path.dirname(__file__)
        
        idb = InstrumentDb.Instance()
        idb.load(manifest)
        self.assertEqual(idb.get_symbols(), ['AC', 'C', 'CT', 'LB', 'LC', 'LH', 'O', 'RR'])
        self.assertEqual(idb.get('CT').point_value(), 50)
        self.assertEqual(idb.get('C').currency(), 'USD')
        self.assertEqual(idb.get('C').description(), 'Corn')
        self.assertEqual(idb.get('LB').exchange(), 'CME')
        self.assertEqual(idb.get('LC').initial_margin(), 1350.0)
        self.assertEqual(idb.get('LH').maint_margin(), 1050.0)
        self.assertEqual(idb.get('O').sector(), 'Agricultural')


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()