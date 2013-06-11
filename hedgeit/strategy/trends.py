'''
hedgeit.strategy.trends

Contains:
    class 
'''

from msymfut import MultiSymFuturesBaseStrategy
from hedgeit.feeds.indicators import talibfunc

class BreakoutStrategy(MultiSymFuturesBaseStrategy):
    def __init__(self, barFeed, symbols = None, broker = None, cash = 1000000,\
                 riskFactor = 0.002, period = 50, stop = 3.0, intraday = True, 
                 tradeStart = None, compounding = True):
        self._period = period
        MultiSymFuturesBaseStrategy.__init__(self, 
                                             barFeed, 
                                             symbols = symbols,
                                             broker = broker,
                                             cash = cash,
                                             riskFactor = riskFactor,
                                             atrPeriod = 2 * period,
                                             stop = stop,
                                             intraday = intraday,
                                             tradeStart = tradeStart,
                                             compounding = compounding
                                             )

    def prep_bar_feed(self):
        for sym in self._symbols:
            feed = self._barFeed.get_feed(sym)
            feed.insert( talibfunc.SMA('short_ma',feed,self._period) )
            feed.insert( talibfunc.SMA('long_ma',feed,2*self._period) )
            feed.insert( talibfunc.MAX('max',feed,self._period) )
            feed.insert( talibfunc.MIN('min',feed,self._period) )

    def onSymBar(self, symbol, bar):
        # only consider a new trade if we don't already have one
        if not self.hasPosition(symbol):
            if bar.short_ma() >= bar.long_ma() and bar.close() >= bar.max():
                self.enterLongRiskSized(symbol, bar)
            elif bar.short_ma() <= bar.long_ma() and bar.close() <= bar.min():
                self.enterShortRiskSized(symbol, bar)
        # our exits for this strategy are purely handled by stops


class MACrossStrategy(MultiSymFuturesBaseStrategy):
    def __init__(self, barFeed, symbols = None, broker = None, cash = 1000000,\
                 riskFactor = 0.002, shortPeriod = 20, longPeriod = 200, stop = None, 
                 intraday = True, tradeStart = None, compounding = True):
        self._shortPeriod = shortPeriod
        self._longPeriod = longPeriod
        MultiSymFuturesBaseStrategy.__init__(self, 
                                             barFeed, 
                                             symbols = symbols,
                                             broker = broker,
                                             cash = cash,
                                             riskFactor = riskFactor,
                                             atrPeriod = longPeriod / 2,
                                             stop = stop,
                                             intraday = intraday,
                                             tradeStart = tradeStart,
                                             compounding = compounding
                                             )

    def prep_bar_feed(self):
        for sym in self._symbols:
            feed = self._barFeed.get_feed(sym)
            feed.insert( talibfunc.SMA('short_ma',feed,self._shortPeriod) )
            feed.insert( talibfunc.SMA('long_ma',feed,self._longPeriod) )

    def onSymBar(self, symbol, bar):
        (poslong, posshort) = self.getPositions(symbol)
        if bar.short_ma() >= bar.long_ma() and posshort:
            self.exitPosition(posshort, goodTillCanceled=True)
        elif bar.short_ma() < bar.long_ma() and poslong:
            self.exitPosition(poslong, goodTillCanceled=True)

        # now see if we need to enter a new postion.
        if bar.short_ma() >= bar.long_ma():                        
            # ok - we are supposed to have a long position
            if not poslong:
                # no long position - open one...
                self.enterLongRiskSized(symbol, bar)            
                    
        # now check short
        if bar.short_ma() < bar.long_ma():
            # ok - we are supposed to have a short position
            if not posshort:
                # no short position - open one...
                self.enterShortRiskSized(symbol, bar)
