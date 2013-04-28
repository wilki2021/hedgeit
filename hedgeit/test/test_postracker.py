'''
Created on Apr 23, 2013

@author: rtw
'''
import unittest
from hedgeit.feeds.instrument import Instrument
from hedgeit.analyzer.postracker import PositionTracker
import os
import datetime
class Test(unittest.TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass


    def testStock(self):
        datafile = '%s/data/AC___CCB.csv' % os.path.dirname(__file__)
        i = Instrument('AC',datafile)
        
        pos = PositionTracker(i)
        pos.buy(datetime.datetime(2012,12,31),100, 25.0, 7.95)
        self.assertEqual(pos.getBasis(), 2500.0)
        self.assertEqual(pos.getNetProfit(26.0, includeCommissions=True), 92.05)
        self.assertEqual(pos.getEntryDate(), datetime.datetime(2012,12,31))
        pos.sell(datetime.datetime(2013,1,1),100, 26.0, 7.95)
        self.assertEqual(pos.getBasis(), 2500.0)
        self.assertEqual(pos.getNetProfit(0.0, includeCommissions=True), 84.1)
        self.assertEqual(pos.getNetProfit(0.0, includeCommissions=False), 100.0)
        self.assertEqual(pos.getCommissions(), 15.90)
        self.assertEqual(pos.getExitDate(), datetime.datetime(2013,1,1))
        self.assertAlmostEqual(pos.getReturn(0.0, includeCommissions=True), 0.0336, places=4)        
        self.assertEqual(pos.getTradeSize(),100)
        self.assertEqual(pos.getEntryPrice(),25.0)
        self.assertEqual(pos.getExitPrice(),26.0)
        
        pos.reset()
        
        pos.buy(datetime.datetime(2013,1,6),100, 27.0, 7.95)
        self.assertEqual(pos.getBasis(), 2700.0)
        self.assertEqual(pos.getNetProfit(26.0, includeCommissions=True), -107.95)
        pos.sell(datetime.datetime(2013,1,7),100, 26.0, 7.95)
        self.assertEqual(pos.getBasis(), 2700.0)
        self.assertEqual(pos.getNetProfit(0.0, includeCommissions=True), -115.90)
        self.assertAlmostEqual(pos.getReturn(0.0, includeCommissions=True), -0.0429, places=4)

        pos.reset()

        pos.sell(datetime.datetime(2013,1,10),100, 28.0, 7.95)
        pos.buy(datetime.datetime(2013,1,11),100, 26.0, 7.95)
        self.assertEqual(pos.getTradeSize(),-100)
        self.assertEqual(pos.getEntryPrice(),28.0)
        self.assertEqual(pos.getExitPrice(),26.0)
        

    def testFutures(self):
        datafile = '%s/data/AC___CCB.csv' % os.path.dirname(__file__)
        i = Instrument('AC',datafile,pointValue=50)
        
        pos = PositionTracker(i)
        pos.buy(datetime.datetime(2012,12,31),100, 25.0, 7.95)
        self.assertEqual(pos.getBasis(), 125000.0)
        self.assertEqual(pos.getNetProfit(26.0, includeCommissions=True), 4992.05)
        self.assertEqual(pos.getEntryDate(), datetime.datetime(2012,12,31))
        pos.sell(datetime.datetime(2013,1,1),100, 26.0, 7.95)
        self.assertEqual(pos.getBasis(), 125000.0)
        self.assertEqual(pos.getNetProfit(0.0, includeCommissions=True), 4984.1)
        self.assertEqual(pos.getNetProfit(0.0, includeCommissions=False), 5000.0)
        self.assertEqual(pos.getCommissions(), 15.90)
        self.assertEqual(pos.getExitDate(), datetime.datetime(2013,1,1))
        
        pos.reset()
        
        pos.buy(datetime.datetime(2013,1,6),100, 27.0, 7.95)
        self.assertEqual(pos.getBasis(), 135000.0)
        self.assertEqual(pos.getNetProfit(26.0, includeCommissions=True), -5007.95)
        pos.sell(datetime.datetime(2013,1,7),100, 26.0, 7.95)
        self.assertEqual(pos.getBasis(), 135000.0)
        self.assertEqual(pos.getNetProfit(0.0, includeCommissions=True), -5015.90)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()