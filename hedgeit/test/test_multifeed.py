'''
Created on Apr 16, 2013

@author: rtw
'''
import unittest
from hedgeit.feeds.instrument import Instrument
from hedgeit.feeds.feed import Feed
from hedgeit.feeds.multifeed import MultiFeed
import os
import sets
import datetime

class Test(unittest.TestCase):


    def setUp(self):
        datafile = '%s/data/AC___CCB.csv' % os.path.dirname(__file__)
        self._inst1 = Instrument('AC',datafile)
        
        datafile = '%s/data/ACM__CCB.csv' % os.path.dirname(__file__)
        self._inst2 = Instrument('ACM',datafile)

        # these are dates where only one of the two feeds above traded and has data.
        # we use this in the on_bars_basic as part of the start/emit() test
        self._special_dates = sets.Set()
        self._special_dates.add(datetime.datetime(2012, 2, 20, 0 ,0))
        self._special_dates.add(datetime.datetime(2012, 4, 9, 0 ,0))
        self._special_dates.add(datetime.datetime(2012, 5, 28, 0 ,0))
        self._special_dates.add(datetime.datetime(2012, 7, 4, 0 ,0))
        self._special_dates.add(datetime.datetime(2012, 9, 3, 0 ,0))
        self._special_dates.add(datetime.datetime(2012, 11, 22, 0 ,0))
        self._special_dates.add(datetime.datetime(2012, 12, 26, 0 ,0))

    def tearDown(self):
        pass


    def on_bars_basic(self, bars):
        if len(bars.symbols()) != 2:
            for symbol in bars.symbols():
                self.assertTrue(bars.get_bar(symbol).datetime() in self._special_dates, '%s' % bars)
        self._count += 1
        
    def testBasic(self):
        f1 = Feed(self._inst1)
        f2 = Feed(self._inst2)
        mf = MultiFeed()
        mf.register_feed(f1)
        mf.register_feed(f2)
        
        self.assertEqual(f1, mf.get_feed('AC'))
        
        self._count = 0
        mf.subscribe(self.on_bars_basic)
        mf.start()
        self.assertEqual(self._count, 257)
        
    def testNeg(self):
        f1 = Feed(self._inst1)
        f2 = Feed(self._inst1)
        mf = MultiFeed()
        mf.register_feed(f1)
        # this should fail because both feeds are for the same symbol
        with self.assertRaises(Exception):
            mf.register_feed(f2)
        
    def testFirstOption(self):
        f1 = Feed(self._inst1)
        f2 = Feed(self._inst2)
        mf = MultiFeed()
        mf.register_feed(f1)
        mf.register_feed(f2)
        
        self._count = 0
        mf.subscribe(self.on_bars_basic)
        mf.start(first=datetime.datetime(2012,7,1))
        self.assertEqual(self._count, 143)

    def testFirstLast(self):
        f1 = Feed(self._inst1)
        f2 = Feed(self._inst2)
        mf = MultiFeed()
        mf.register_feed(f1)
        mf.register_feed(f2)
        
        self._count = 0
        mf.subscribe(self.on_bars_basic)
        mf.start(first=datetime.datetime(2012,7,1),last=datetime.datetime(2012,7,31))
        self.assertEqual(self._count, 22)
        self.assertEqual(mf.get_last_close('AC'), 2.565)

    def testFirstLastBoundary(self):
        f1 = Feed(self._inst1)
        f2 = Feed(self._inst2)
        mf = MultiFeed()
        mf.register_feed(f1)
        mf.register_feed(f2)
        
        mf.subscribe(self.on_bars_basic)
        self._count = 0
        mf.start(first=datetime.datetime(2012,7,2),last=datetime.datetime(2012,7,2))
        self.assertEqual(self._count, 1)
        self.assertEqual(mf.get_next_bars_date(), datetime.datetime(2012,7,3))
        self._count = 0
        mf.start(first=datetime.datetime(2012,7,1),last=datetime.datetime(2012,7,2))
        self.assertEqual(self._count, 1)
        self.assertEqual(mf.get_next_bars_date(), datetime.datetime(2012,7,3))

        # 7/1 is not a trading day so first bar is actually 7/2 which is after last
        self._count = 0
        mf.start(first=datetime.datetime(2012,7,1),last=datetime.datetime(2012,7,1))
        self.assertEqual(self._count, 0)
        self.assertEqual(mf.get_next_bars_date(), datetime.datetime(2012,7,2))

    def testLastPastEnd(self):
        f1 = Feed(self._inst1)
        f2 = Feed(self._inst2)
        mf = MultiFeed()
        mf.register_feed(f1)
        mf.register_feed(f2)
        
        self._count = 0
        mf.subscribe(self.on_bars_basic)
        mf.start(first=datetime.datetime(2012,7,1),last=datetime.datetime(2013,7,31))
        self.assertEqual(self._count, 143)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()