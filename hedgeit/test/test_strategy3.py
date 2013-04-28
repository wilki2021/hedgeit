'''
Created on Apr 17, 2013

@author: rtw
'''
import unittest

from hedgeit.feeds.feed import Feed
from hedgeit.feeds.instrument import Instrument
from hedgeit.feeds.db import InstrumentDb
from hedgeit.feeds.multifeed import MultiFeed
from hedgeit.strategy.strategy import Strategy
from hedgeit.analyzer import returns
from hedgeit.analyzer import drawdown
from hedgeit.analyzer import sharpe
from hedgeit.analyzer import trades
from hedgeit.feeds.indicators import talibfunc
from hedgeit.broker.brokers import BacktestingFuturesBroker
import numpy
import test_util

import os

class MyStrategy(Strategy):
    def __init__(self, barFeed, cash = 1000000):
        broker_ = BacktestingFuturesBroker(cash, barFeed)
        Strategy.__init__(self, barFeed, cash, broker_)
        self._position = None
        self._started = False
        self._db = InstrumentDb.Instance()
        self._riskfactor = 0.002
        
    def onExitOk(self, position):
        self._position = None
        
    def calc_position_size(self, instrument, atr):
        #print 'atr = %f,equity = %0.2f,point_vaue = %0.2f,risk_factor = %f' % \
        #    (atr, self.getBroker().getCash(), self._db.get(instrument).point_value(), self._riskfactor )
        target_quant = self.getBroker().getCash() * self._riskfactor / \
                        (self._db.get(instrument).point_value() * atr)
        return round(target_quant)
        
    def onBars(self, bars):
        #print 'On date %s, cash = %f' % (bars[bars.keys()[0]]['Datetime'], self.getBroker().getCash())
        acbar = bars.get_bar('RR')
        if not self._started:
            # need to check all of our indicators to see when they have data
            # we know that the 100d SMA will be last so just check it
            if not numpy.isnan(acbar.SMA100()):
                self._started = True
                
        if self._started and self._position == None:
            '''
            Debug...
            trend = 'up' if acbar.SMA50() >= acbar.SMA100() else 'down'
            thresh =  acbar.MAX50() if trend == 'up' else acbar.MIN50()
            print 'trend: %s, close:%s, thresh:%s' % (trend, acbar.close(),thresh)
            '''
            
            # check for long entry first
            if acbar.SMA50() >= acbar.SMA100() and acbar.close() >= acbar.MAX50():
                pos_size = self.calc_position_size('RR', acbar.ATR10())
                self._position = self.enterLong('RR', pos_size, goodTillCanceled=True)
                # set up our exit order
                self._tradeHigh = acbar.close()
                self.exitPosition(self._position, stopPrice=self._tradeHigh-3*acbar.ATR10(), goodTillCanceled=True)
            # then short entry
            elif acbar.SMA50() <= acbar.SMA100() and acbar.close() <= acbar.MIN50():
                pos_size = self.calc_position_size('RR', acbar.ATR10())
                self._position = self.enterShort('RR', pos_size, goodTillCanceled=True)
                self._tradeLow = acbar.close()
                self.exitPosition(self._position, stopPrice=self._tradeLow+3*acbar.ATR10(), goodTillCanceled=True)
        elif self._position:
            # we need to adjust our exit daily 
            if self._position.isLong():
                if acbar.close() > self._tradeHigh:
                    self._tradeHigh = acbar.close()
                self.exitPosition(self._position, stopPrice=self._tradeHigh-3*acbar.ATR10(), goodTillCanceled=True)
            else:
                if acbar.close() < self._tradeLow:
                    self._tradeLow = acbar.close()
                self.exitPosition(self._position, stopPrice=self._tradeLow+3*acbar.ATR10(), goodTillCanceled=True)
         
    def exitPositions(self):
        if self._position != None:
            self.exitPosition(self._position)  
        self.getBroker().executeSessionClose()      
                
            
class Test(unittest.TestCase):


    def setUp(self):
        manifest = '%s/data/manifest1.csv' % os.path.dirname(__file__)        
        self._db = InstrumentDb.Instance()
        self._db.load(manifest)
        self._feed = Feed(self._db.get('RR'))
        self._feed.insert( talibfunc.SMA('SMA50',self._feed,50) )
        self._feed.insert( talibfunc.SMA('SMA100',self._feed,100) )
        self._feed.insert( talibfunc.MAX('MAX50',self._feed,50) )
        self._feed.insert( talibfunc.MIN('MIN50',self._feed,50) )
        self._feed.insert( talibfunc.ATR('ATR10',self._feed,10) )


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
        strat.exitPositions()
        
        self.assertAlmostEqual(strat.getResult(),996193.19,places=2)
        
        self.assertEqual(tradesAnalyzer.getCount(),2)
        self.assertEqual(tradesAnalyzer.getProfitableCount(),0)
        self.assertEqual(tradesAnalyzer.getUnprofitableCount(),2)
        
        tlog = '%s/trade.log' % os.path.dirname(__file__)
        tradesAnalyzer.writeTradeLog(tlog)
        self.assertTrue(test_util.file_compare('%s/trade1.reflog' % os.path.dirname(__file__), tlog))
        os.system('rm %s' % tlog)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testBasic']
    unittest.main()