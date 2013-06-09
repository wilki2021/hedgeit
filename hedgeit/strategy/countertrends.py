'''
hedgeit.strategy.strategy

Contains:
  class RSICounterStrategy
'''

from msymfut import MultiSymFuturesBaseStrategy
from hedgeit.feeds.indicators import talibfunc
from hedgeit.feeds.db import InstrumentDb
from hedgeit.strategy.strategy import Strategy
from hedgeit.broker.brokers import BacktestingFuturesBroker
from hedgeit.feeds.indicators.atr import ATR
from hedgeit.common.logger import getLogger
from hedgeit.broker.commissions import FuturesCommission
import numpy
import datetime

logger = getLogger("strategy.macross")

class RSIReversalStrategy(MultiSymFuturesBaseStrategy):
    def __init__(self, barFeed, symbols = None, broker = None, cash = 1000000,\
                 riskFactor = 0.002, period = 7, stop = 2.0, limit = 2.5,
                 intraday = True, tradeStart = None, compounding = True):
        self._period = period
        MultiSymFuturesBaseStrategy.__init__(self, 
                                             barFeed, 
                                             symbols = symbols,
                                             broker = broker,
                                             cash = cash,
                                             riskFactor = riskFactor,
                                             atrPeriod = 2 * period,
                                             stop = stop,
                                             limit = limit,
                                             intraday = intraday,
                                             tradeStart = tradeStart,
                                             compounding = compounding
                                             )
        self._lastRSI = {}
        self._tripped = {}

    def prep_bar_feed(self):
        for sym in self._symbols:
            feed = self._barFeed.get_feed(sym)
            feed.insert( talibfunc.RSI('rsi',feed,self._period) )

    def onSymBar(self, symbol, bar):
        if not self._lastRSI.has_key(symbol):
            self._lastRSI[symbol] = bar.rsi()
                                 
        if not self.hasPosition(symbol):
            '''
            Debug...
            trend = 'up' if bar.short_ma() >= bar.long_ma() else 'down'
            thresh =  bar.max() if trend == 'up' else bar.min()
            print 'trend: %s, close:%s, thresh:%s' % (trend, bar.close(),thresh)
            '''                
            # TODO - if this strategy is worth anything, these thresholds need
            # to be configurable
            if bar.rsi() < 20 or bar.rsi() > 80:
                self._tripped[symbol] = True

            # check for long entry first
            if self._tripped.has_key(symbol) and bar.rsi() > self._lastRSI[symbol]:
                self.enterLongRiskSized(symbol, bar)                
                del self._tripped[symbol]
            # then short entry
            elif self._tripped.has_key(symbol) and bar.rsi() < self._lastRSI[symbol]:
                self.enterShortRiskSized(symbol, bar)
                del self._tripped[symbol]

        self._lastRSI[symbol] = bar.rsi()

class Split7sStrategy(MultiSymFuturesBaseStrategy):
    def __init__(self, barFeed, symbols = None, broker = None, cash = 1000000,\
                 riskFactor = 0.002, period = 7, filter_ = 200, stop = 3.0,
                 intraday = True, tradeStart = None, compounding = True):
        self._period = period
        self._filter = filter_
        MultiSymFuturesBaseStrategy.__init__(self, 
                                             barFeed, 
                                             symbols = symbols,
                                             broker = broker,
                                             cash = cash,
                                             riskFactor = riskFactor,
                                             atrPeriod = filter_,
                                             stop = stop,
                                             limit = None,
                                             intraday = intraday,
                                             tradeStart = tradeStart,
                                             compounding = compounding
                                             )
        self._lastRSI = {}
        self._tripped = {}

    def prep_bar_feed(self):
        for sym in self._symbols:
            feed = self._barFeed.get_feed(sym)
            feed.insert( talibfunc.SMA('filter_ma',feed,2*self._filter) )
            feed.insert( talibfunc.MAX('max',feed,self._period) )
            feed.insert( talibfunc.MIN('min',feed,self._period) )

    def onSymBar(self, symbol, bar):
        if not self.hasPosition(symbol):
            if bar.close() > bar.filter_ma() and bar.close() == bar.min():
                self.enterLongRiskSized(symbol, bar)
            elif bar.close() < bar.filter_ma() and bar.close() == bar.max():
                self.enterShortRiskSized(symbol, bar)
        else:
            (long_, short) = self.getPositions(symbol)
            if long_:
                if bar.close() == bar.max():
                    self.exitPosition(long_, goodTillCanceled=True)
            if short:
                if bar.close() == bar.min():
                    self.exitPosition(short, goodTillCanceled=True)
                    