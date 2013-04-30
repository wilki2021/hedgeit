'''
Created on Jan 21, 2013

@author: rtw
'''
import unittest
import os, datetime, numpy
from hedgeit.feeds.feed import Feed
from hedgeit.feeds.indicators.atr import ATR
from hedgeit.feeds.indicators.pvelocity import PriceVelocity
from hedgeit.feeds.indicators import talibfunc
from hedgeit.feeds.instrument import Instrument
import math

import test_util

class Test(unittest.TestCase):


    def setUp(self):
        datafile = '%s/data/AC___CCB.csv' % os.path.dirname(__file__)
        self._inst = Instrument('AC',datafile)


    def tearDown(self):
        pass


    def testDup(self):
        w = Feed(self._inst)
        
        w.insert( ATR() )
        with self.assertRaisesRegexp(Exception,"Workspace already has an indicator.*"):        
            w.insert( ATR() )
            
    def testNeg(self):
        w = Feed(self._inst)
        with self.assertRaisesRegexp(Exception,"Workspace does not have a.*series in"):        
            w.get_series('notexist')
        
    def testBasic(self):
        w = Feed(self._inst)
        
        w.insert( ATR() )
        w.insert( talibfunc.SMA('SMA10',w,10))
        self.assertEqual( len(w.values()), 8 )
        self.assertEqual( len(w.values()[0]), 252 )
        self.assertEqual( w.values()[0][251], datetime.datetime(2013,1,18,0,0) )
        self.assertTrue( math.isnan(w.get_series('ATR')[5]))
        self.assertTrue( math.isnan(w.get_series('ATR')[98]))
        self.assertAlmostEqual( w.get_series('ATR')[99], 0.03493, places=5 )
        self.assertAlmostEqual( w.get_series('ATR')[251], 0.03307, places=5 )
        self.assertAlmostEqual( w.get_series('SMA10')[251], 2.2921 )
        self.assertAlmostEqual( w.get_series('SMA10')[188], 2.3989 )
        
    def testBasic2(self):
        w = Feed(self._inst)
        
        w.insert( talibfunc.MAX('MAX50',w,50) )
        w.insert( talibfunc.MAX('MAX25',w,25) )
        w.insert( talibfunc.MIN('MIN50',w,50) )
        w.insert( talibfunc.MIN('MIN25',w,25) )
        self.assertEqual( len(w.values()), 10 )
        self.assertEqual( len(w.values()[0]), 252 )
        self.assertAlmostEqual( w.get_series('MAX50')[232], 2.459 )
        self.assertAlmostEqual( w.get_series('MAX25')[231], 2.448 )
        self.assertAlmostEqual( w.get_series('MIN50')[230], 2.267 )
        self.assertAlmostEqual( w.get_series('MIN25')[229], 2.289 )

    def testBasic3(self):
        w = Feed(self._inst)
        
        w.insert( talibfunc.ATR('ATR10',w,10) )
        self.assertEqual( len(w.values()), 7 )
        self.assertEqual( len(w.values()[0]), 252 )
        self.assertAlmostEqual( w.get_series('ATR10')[251], 0.031196, places=6 )
        
    def testCursor(self):
        w = Feed(self._inst)        
        w.insert( talibfunc.ATR('ATR10',w,10) )
        w.set_cursor(None)
        self.assertEqual(w.get_last_close(), 0.0 )
        b = w.get_current_bar()
        self.assertEqual(b.datetime(), datetime.datetime(2012,1,23,0,0))
        self.assertTrue(math.isnan(b.ATR10()))
        self.assertEqual(w.get_next_bar_date(), datetime.datetime(2012,1,24,0,0))
        count = 1
        while w.get_next_bar_date()!= None:
            count += 1
            lastbar = w.get_current_bar()
        self.assertEqual(count, 252)
        self.assertEqual(lastbar.datetime(),datetime.datetime(2013,1,18,0,0))
        
    def testCursor2(self):
        w = Feed(self._inst)
        w.set_cursor(datetime.datetime(2012,6,29,0,0))
        self.assertEqual(w.get_next_bar_date(), datetime.datetime(2012,6,29,0,0))
        self.assertEqual(w.get_last_close(), 2.182 )

    def testBadNewSeries(self):
        w = Feed(self._inst)
        # this add_series should fail because the length doesn't match
        with self.assertRaisesRegexp(Exception,"Error adding new series.*"):        
            w._add_series('foobar', [1,2,3,4,5])
                        
    def testPriceVelocity(self):
        w = Feed(self._inst)
        w.insert( talibfunc.SMA('SMA50',w,50))        
        w.insert( PriceVelocity('PVEL',period=10,baseIndicator='SMA50') )
        self.assertEqual( len(w.values()), 8 )
        self.assertEqual( len(w.values()[0]), 252 )
        self.assertAlmostEqual( w.get_series('PVEL')[251], -0.001576, places=4 )

        feedout = '%s/writefeed.csv' % os.path.dirname(__file__)
        
        wf = open(feedout,'w')
        w.write_csv(wf)
        wf.close()
        
        self.assertTrue(test_util.file_compare('%s/writefeed.refcsv' % os.path.dirname(__file__), feedout))
        os.system('rm %s' % feedout)

        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testBasic']
    unittest.main()