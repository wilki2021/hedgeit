'''
Created on Apr 17, 2013

@author: rtw
'''
import unittest

from hedgeit.feeds.feed import Feed
from hedgeit.feeds.db import InstrumentDb
from hedgeit.feeds.multifeed import MultiFeed
from hedgeit.analyzer import returns
from hedgeit.analyzer import drawdown
from hedgeit.analyzer import sharpe
from hedgeit.analyzer import trades
from hedgeit.strategy.clenow import ClenowBreakoutStrategy
import datetime
import test_util

import os

class Test(unittest.TestCase):


    def setUp(self):
        manifest = '%s/data/manifest1.csv' % os.path.dirname(__file__)        
        self._db = InstrumentDb.Instance()
        self._db.load(manifest)
        
    def setupFeed(self, barFeed):
        barFeed.register_feed(Feed(self._db.get('RR')))
        barFeed.register_feed(Feed(self._db.get('LH')))
        barFeed.register_feed(Feed(self._db.get('O')))

    def tearDown(self):
        pass


    def testClenow(self):
        mf = MultiFeed()
        self.setupFeed(mf)
        strat = ClenowBreakoutStrategy(mf)
        
        # Attach a few analyzers to the strategy before executing it.
        retAnalyzer = returns.Returns()
        strat.attachAnalyzer(retAnalyzer)
        sharpeRatioAnalyzer = sharpe.SharpeRatio()
        strat.attachAnalyzer(sharpeRatioAnalyzer)
        drawDownAnalyzer = drawdown.DrawDown()
        strat.attachAnalyzer(drawDownAnalyzer)
        tradesAnalyzer = trades.Trades()
        strat.attachAnalyzer(tradesAnalyzer)
        
        mf.start()
        strat.exitPositions()

        tlog = '%s/trade2.log' % os.path.dirname(__file__)
        tradesAnalyzer.writeTradeLog(tlog)
        
        self.assertAlmostEqual(strat.getResult(),982554.90,places=2)
        self.assertEqual(tradesAnalyzer.getCount(),6)
        self.assertEqual(tradesAnalyzer.getProfitableCount(),1)
        self.assertEqual(tradesAnalyzer.getUnprofitableCount(),5)
        
        self.assertTrue(test_util.file_compare('%s/trade2.reflog' % os.path.dirname(__file__), tlog))
        os.system('rm %s' % tlog)

    def testClenowTradeStart(self):
        mf = MultiFeed()
        self.setupFeed(mf)
        strat = ClenowBreakoutStrategy(mf,tradeStart=datetime.datetime(2012,8,11))
        
        # Attach a few analyzers to the strategy before executing it.
        retAnalyzer = returns.Returns()
        strat.attachAnalyzer(retAnalyzer)
        sharpeRatioAnalyzer = sharpe.SharpeRatio()
        strat.attachAnalyzer(sharpeRatioAnalyzer)
        drawDownAnalyzer = drawdown.DrawDown()
        strat.attachAnalyzer(drawDownAnalyzer)
        tradesAnalyzer = trades.Trades()
        strat.attachAnalyzer(tradesAnalyzer)
        
        mf.start()
        strat.exitPositions()

        tlog = '%s/trade3.log' % os.path.dirname(__file__)
        tradesAnalyzer.writeTradeLog(tlog)
        
        self.assertAlmostEqual(strat.getResult(),986794.67,places=2)
        self.assertEqual(tradesAnalyzer.getCount(),5)
        self.assertEqual(tradesAnalyzer.getProfitableCount(),1)
        self.assertEqual(tradesAnalyzer.getUnprofitableCount(),4)
        
        self.assertTrue(test_util.file_compare('%s/trade3.reflog' % os.path.dirname(__file__), tlog))
        os.system('rm %s' % tlog)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testBasic']
    unittest.main()