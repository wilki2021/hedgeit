'''
Created on Apr 16, 2013

@author: rtw
'''
import unittest

import time
import datetime
import pytz
import hedgeit.common.dt as dt

class Test(unittest.TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass


    def testBasic(self):
        d = datetime.datetime(2013, 4, 16, 12, 0, 0)
        self.assertTrue(dt.datetime_is_naive(d))
        
        d1 = dt.timestamp_to_datetime(time.time())
        self.assertFalse(dt.datetime_is_naive(d1))
        
        eastern = pytz.timezone('US/Eastern')
        central = pytz.timezone('US/Central')
        d2 = dt.localize(d,eastern)                
        self.assertFalse(dt.datetime_is_naive(d2))
        d3 = dt.localize(d2, central)
        self.assertEqual(d3.hour, 11)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testBasic']
    unittest.main()