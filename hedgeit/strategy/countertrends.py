'''
hedgeit.strategy.countertrends

Contains:
  class RSIReversalStrategy
  class ConnorsRSIStrategy
  class Split7sStrategy
'''

from msymfut import MultiSymFuturesBaseStrategy
from hedgeit.feeds.indicators import talibfunc
from hedgeit.common.logger import getLogger

logger = getLogger("strategy.macross")

class RSIReversalStrategy(MultiSymFuturesBaseStrategy):
    def __init__(self, barFeed, symbols = None, broker = None, cash = 1000000,\
                 compounding = True, parms = None):
        MultiSymFuturesBaseStrategy.__init__(self, 
                                             barFeed, 
                                             symbols = symbols,
                                             broker = broker,
                                             cash = cash,
                                             compounding = compounding,
                                             parms = parms
                                             )
        self._lastRSI = {}
        self._tripped = {}

    def defaultParms(self):
        ret = MultiSymFuturesBaseStrategy.defaultParms(self)
        ret['atrPeriod']    = 14
        ret['period']       = 7
        ret['stop']         = 3.0
        ret['intradayStop'] = True
        ret['limit']        = 2.5
        return ret

    def prep_bar_feed(self):
        for sym in self._symbols:
            feed = self._barFeed.get_feed(sym)
            feed.insert( talibfunc.RSI('rsi',feed,self._parms['period']) )

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

class ConnorsRSIStrategy(MultiSymFuturesBaseStrategy):
    def __init__(self, barFeed, symbols = None, broker = None, cash = 1000000,\
                 compounding = True, parms = None):
        MultiSymFuturesBaseStrategy.__init__(self, 
                                             barFeed, 
                                             symbols = symbols,
                                             broker = broker,
                                             cash = cash,
                                             compounding = compounding,
                                             parms = parms
                                             )

    def defaultParms(self):
        ret = MultiSymFuturesBaseStrategy.defaultParms(self)
        ret['atrPeriod']    = 45
        ret['period']       = 2
        ret['filterPeriod'] = 100
        ret['stop']         = None
        ret['limit']        = None
        return ret

    def prep_bar_feed(self):
        for sym in self._symbols:
            feed = self._barFeed.get_feed(sym)
            feed.insert( talibfunc.SMA('filter_ma',feed,self._parms['filterPeriod']) )
            feed.insert( talibfunc.RSI('rsi',feed,self._parms['period']) )

    def onSymBar(self, symbol, bar):
        (long_, short) = self.getPositions(symbol)
        if not long_:
            if bar.close() > bar.filter_ma() and bar.rsi() < 10.0:
                self.enterLongRiskSized(symbol, bar)
        else:
            if bar.rsi() > 50.0:
                self.exitPosition(long_, goodTillCanceled=True)
                
        if not short:
            if bar.close() < bar.filter_ma() and bar.rsi() > 85.0:
                self.enterShortRiskSized(symbol, bar)
        else:
            if bar.rsi() < 50.0:
                self.exitPosition(short, goodTillCanceled=True)

class Split7sStrategy(MultiSymFuturesBaseStrategy):
    def __init__(self, barFeed, symbols = None, broker = None, cash = 1000000,\
                 compounding = True, parms = None):
        MultiSymFuturesBaseStrategy.__init__(self, 
                                             barFeed, 
                                             symbols = symbols,
                                             broker = broker,
                                             cash = cash,
                                             compounding = compounding,
                                             parms = parms
                                             )

    def defaultParms(self):
        ret = MultiSymFuturesBaseStrategy.defaultParms(self)
        ret['atrPeriod']    = 45
        ret['period']       = 7
        ret['filterPeriod'] = 200
        ret['stop']         = 3.0
        ret['limit']        = None
        return ret

    def prep_bar_feed(self):
        for sym in self._symbols:
            feed = self._barFeed.get_feed(sym)
            feed.insert( talibfunc.SMA('filter_ma',feed,self._parms['filterPeriod']) )
            feed.insert( talibfunc.MAX('max',feed,self._parms['period']) )
            feed.insert( talibfunc.MIN('min',feed,self._parms['period']) )

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
                    