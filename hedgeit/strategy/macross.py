'''
hedgeit.strategy.strategy

Contains:
  class MACrossStrategy
'''

from hedgeit.feeds.db import InstrumentDb
from hedgeit.strategy.strategy import Strategy
from hedgeit.broker.brokers import BacktestingFuturesBroker
from hedgeit.feeds.indicators import talibfunc
from hedgeit.feeds.indicators.atr import ATR
from hedgeit.common.logger import getLogger
from hedgeit.broker.commissions import FuturesCommission
import numpy
import datetime

logger = getLogger("strategy.macross")

class MACrossStrategy(Strategy):
    def __init__(self, barFeed, symbols = None, broker = None, cash = 1000000,
                 riskFactor = 0.002, shortPeriod=20, longPeriod=200, stop=3.0, 
                 tradeStart=None):
        if broker is None:
            broker = BacktestingFuturesBroker(cash, barFeed, commission=FuturesCommission(2.50))
        if symbols is None:
            self._symbols = barFeed.symbols()
        else:
            self._symbols = symbols
        Strategy.__init__(self, barFeed, cash, broker)
        self.__barFeed = barFeed
        self._positions = {}
        self._started = False
        self._db = InstrumentDb.Instance()
        self._riskfactor = riskFactor
        self._short_period = shortPeriod
        self._long_period = longPeriod
        self._stop = stop
        self._tradeHigh = {}
        self._tradeLow = {}
        if tradeStart != None:
            self._tradeStart = tradeStart
        else:
            # set this to an arbitrarily early date so we can compare 
            # directly in the onBars method below
            self._tradeStart = datetime.datetime(1900,1,1)
        self.__prep_bar_feed()
        
    def getPositions(self):
        return self._positions
    
    def __prep_bar_feed(self):
        for sym in self._symbols:
            feed = self.__barFeed.get_feed(sym)
            feed.insert( talibfunc.SMA('short_ma',feed,self._short_period) )
            feed.insert( talibfunc.SMA('long_ma',feed,self._long_period) )
            feed.insert( ATR( name='atr', period=self._long_period ) )
    
    def onExitOk(self, position):
        longshort = 'long' if position.isLong() else 'short'
        poskey = '%s-%s' % (position.getInstrument(), longshort)
        if self._positions.has_key(poskey):
            del self._positions[poskey]
        else:
            logger.error('unknown position exit for %s, positions are: %s' % (position.getInstrument(),self._positions)) 
        
    def _calc_position_size(self, instrument, atr):
        #print 'atr = %f,equity = %0.2f,point_vaue = %0.2f,risk_factor = %f' % \
        #    (atr, self.getBroker().getCash(), self._db.get(instrument).point_value(), self._riskfactor )
        target_quant = self.getBroker().getCash() * self._riskfactor / \
                        (self._db.get(instrument).point_value() * atr)
        if target_quant < 1:
            logger.warning('Insufficient equity to meet risk target for %s, risk multiple %0.3f' % (instrument,1.0/target_quant))
            ret = 1
        else:
            ret = round(target_quant)
        return ret
        
    def onBars(self, bars):
        for sym in self._symbols:
            if sym in bars.symbols():
                bar = bars.get_bar(sym)
                if not self._started:
                    # need to check all of our indicators to see when they have data
                    # we know that the 100d SMA will be last so just check it
                    if not numpy.isnan(bar.long_ma()) and bars.datetime() >= self._tradeStart:
                        self._started = True
                        
                if self._started:
                    '''
                    # debug
                    print '%s,position:%s,short_ma:%0.2f,long_ma:%0.2f,close:%0.2f,max:%0.2f,atr:%0.2f,trade_high:%0.2f,trade_low:%0.2f' % \
                            (bar.datetime(),
                             self._positions.has_key(sym),
                             bar.short_ma(),
                             bar.long_ma(),
                             bar.atr(),
                             0.0 if not self._tradeHigh.has_key(sym) else self._tradeHigh[sym],
                             0.0 if not self._tradeLow.has_key(sym) else self._tradeLow[sym])
                    '''
                        
                if self._started:
                    # first check if any position needs to be exited
                    poslong = '%s-long' % sym
                    posshort = '%s-short' % sym                    
                    if bar.short_ma() >= bar.long_ma() and self._positions.has_key(posshort):
                        self.exitPosition(self._positions[posshort], goodTillCanceled=True)
                    elif bar.short_ma() < bar.long_ma() and self._positions.has_key(poslong):
                        self.exitPosition(self._positions[poslong], goodTillCanceled=True)

                    # now see if we need to enter a new postion.
                    if bar.short_ma() >= bar.long_ma():                        
                        # ok - we are supposed to have a long position
                        if not self._positions.has_key(poslong):
                            # no long position - open one...
                            pos_size = self._calc_position_size(sym, bar.atr())
                            self._positions[poslong] = self.enterLong(sym, pos_size, goodTillCanceled=True)
                            self._tradeHigh[sym] = bar.close()
                        else:
                            # model is long and we already have long position 
                            if bar.close() > self._tradeHigh[sym]:
                                self._tradeHigh[sym] = bar.close()
                        
                                
                    # now check short
                    if bar.short_ma() < bar.long_ma():
                        # ok - we are supposed to have a long position
                        if not self._positions.has_key(posshort):
                            # no long position - open one...
                            pos_size = self._calc_position_size(sym, bar.atr())
                            self._positions[posshort] = self.enterShort(sym, pos_size, goodTillCanceled=True)
                            self._tradeLow[sym] = bar.close()
                        else:
                            # model is long and we already have long position 
                            if bar.close() < self._tradeLow[sym]:
                                self._tradeLow[sym] = bar.close()
                             
    def exitPositions(self):
        for sym in self._positions:
            self.exitPosition(self._positions[sym])  
        self.getBroker().executeSessionClose()    