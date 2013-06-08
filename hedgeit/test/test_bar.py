'''
Created on Apr 17, 2013

@author: rtw
'''
import unittest

import datetime
from hedgeit.feeds.bar import Bar
from hedgeit.feeds.bars import Bars
import numpy

class Test(unittest.TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass

    
    def testMinimal(self):
        b = Bar(datetime.datetime(2013,1,23),10.0, 40.0, 5.0, 25.0)
        self.assertEqual(b.open(), 10.0)
        self.assertEqual(b.high(), 40.0)
        self.assertEqual(b.low(), 5.0)
        self.assertEqual(b.close(), 25.0)
        self.assertEqual(b.volume(), None)
        self.assertEqual(b.open_interest(), None)
        self.assertEqual(b.adj_close(), None)
        bstr = '%s' % b
        self.assertEqual(bstr, 'date:2013-01-23 00:00:00,open:10.0,high:40.0,low:5.0,close:25.0')

    def testFull(self):
        b = Bar(datetime.datetime(2013,3,22),15.0, 25.0, 15.0, 20.0, volume=10000, open_interest=500, adj_close=22.5)
        self.assertEqual(b.open(), 15.0)
        self.assertEqual(b.high(), 25.0)
        self.assertEqual(b.low(), 15.0)
        self.assertEqual(b.close(), 20.0)
        self.assertEqual(b.volume(), 10000)
        self.assertEqual(b.open_interest(), 500)
        self.assertEqual(b.adj_close(), 22.5)
        bstr = '%s' % b
        self.assertEqual(bstr, 'date:2013-03-22 00:00:00,open:15.0,high:25.0,low:15.0,close:20.0,volume:10000,open_interest:500,adjusted_close:22.5')

    def testExcep(self):
        with self.assertRaises(AssertionError):
            # high < open
            Bar(datetime.datetime(2013,3,22),15.0, 14.0, 15.0, 20.0)

        with self.assertRaises(AssertionError):
            # open < low
            Bar(datetime.datetime(2013,3,22),15.0, 25.0, 16.0, 20.0)

        with self.assertRaises(AssertionError):
            # close < low
            Bar(datetime.datetime(2013,3,22),15.0, 25.0, 15.0, 12.0)
            
        with self.assertRaises(AssertionError):            
            # close > high
            Bar(datetime.datetime(2013,3,22),15.0, 25.0, 15.0, 30.0)

    def testUserDefined(self):
        b = Bar(datetime.datetime(2013,1,23),10.0, 40.0, 5.0, 25.0)
        b.set_user_defined('foo1', 42)
        b.set_user_defined('foo2', 99.36)
        self.assertEqual(b.foo1(), 42)
        self.assertEqual(b.foo2(), 99.36)
        with self.assertRaisesRegexp(Exception, 'Bar has no user-defined'):
            b.Close()
        self.assertFalse(b.has_nan())
        b.set_user_defined('foonan', numpy.nan)
        self.assertTrue(b.has_nan())

    def testBarsBasic(self):
        b1 = Bar(datetime.datetime(2013,1,23),10.0, 40.0, 5.0, 25.0)
        b2 = Bar(datetime.datetime(2013,1,23),20.0, 30.0, 15.0, 15.0)
        bars = Bars()
        bars.add_bar('AA', b1)
        bars.add_bar('AB', b2)
        self.assertEqual(bars.datetime(), datetime.datetime(2013,1,23))
        self.assertEqual(bars.symbols(), ['AA', 'AB'])
        self.assertEqual(bars.get_bar('AA').open(), 10.0)
        self.assertEqual(bars.get_bar('AB').close(), 15.0)
        
    def testBarsExceptions(self):
        b1 = Bar(datetime.datetime(2013,1,23),10.0, 40.0, 5.0, 25.0)
        b2 = Bar(datetime.datetime(2013,1,24),20.0, 30.0, 15.0, 15.0)
        bars = Bars()
        bars.add_bar('AA', b1)
        with self.assertRaisesRegexp(Exception, 'attempt to add duplicate bar'):
            bars.add_bar('AA', b1)
        with self.assertRaisesRegexp(Exception, '!= current datetime'):
            bars.add_bar('AB', b2)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()