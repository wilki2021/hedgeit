'''
Created on Apr 17, 2013

@author: rtw
'''
import unittest

from hedgeit.feeds.feed import Feed
from hedgeit.feeds.instrument import Instrument
from hedgeit.feeds.multifeed import MultiFeed
from hedgeit.strategy.strategy import Strategy
from hedgeit.analyzer import returns
from hedgeit.analyzer import drawdown
from hedgeit.analyzer import sharpe
from hedgeit.analyzer import trades
from hedgeit.feeds.db import InstrumentDb

import os

class MyStrategy(Strategy):
    def __init__(self, barFeed, cash = 1000000, broker_ = None):
        Strategy.__init__(self, barFeed, cash, broker_)
        self._position = None
        
    def onBars(self, bars):
        if not self._position:
            self._position = self.enterLong('AC', 100000)

class MyStrategy2(Strategy):
    def __init__(self, barFeed, cash = 1000000, broker_ = None):
        Strategy.__init__(self, barFeed, cash, broker_)
        self._position = None
        
    def onBars(self, bars):
        if not self._position:
            self._position = self.enterLong('AC', 100000)
            self.exitPosition(self._position, stopPrice=2.2, goodTillCanceled=True)
        
class Test(unittest.TestCase):


    def setUp(self):
        manifest = '%s/data/manifest.csv' % os.path.dirname(__file__)        
        self._db = InstrumentDb.Instance()
        self._db.load(manifest)
        self._feed = Feed(self._db.get('AC'))


    def tearDown(self):
        pass


    def testBasic(self):
        mf = MultiFeed()
        mf.register_feed(self._feed)
        strat = MyStrategy(mf)
        
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
        
        self.assertEqual(strat.getResult(),1000300.0)
        self.assertEqual(tradesAnalyzer.getCount(),0)
        self.assertEqual(tradesAnalyzer.getProfitableCount(),0)
        self.assertEqual(tradesAnalyzer.getUnprofitableCount(),0)

    def testBasic2(self):
        mf = MultiFeed()
        mf.register_feed(self._feed)
        strat = MyStrategy2(mf)
        
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
        
        self.assertEqual(strat.getResult(),998500.0)
        self.assertEqual(tradesAnalyzer.getCount(),1)
        self.assertEqual(tradesAnalyzer.getProfitableCount(),0)
        self.assertEqual(tradesAnalyzer.getUnprofitableCount(),1)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testBasic']
    unittest.main()