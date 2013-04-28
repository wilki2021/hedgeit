'''
hedgeit.strategy.strategy

Contains:
  class ClenowStrategy
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

logger = getLogger("strategy.clenow")

class ClenowBreakoutStrategy(Strategy):
    def __init__(self, barFeed, cash = 1000000, riskFactor = 0.002, breakout=50, stop=3.0, tradeStart=None):
        broker_ = BacktestingFuturesBroker(cash, barFeed, commission=FuturesCommission(2.50))
        Strategy.__init__(self, barFeed, cash, broker_)
        self.__barFeed = barFeed
        self._positions = {}
        self._started = False
        self._db = InstrumentDb.Instance()
        self._riskfactor = riskFactor
        self._breakout = breakout
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
        for sym in self.__barFeed.symbols():
            feed = self.__barFeed.get_feed(sym)
            feed.insert( talibfunc.SMA('short_ma',feed,50) )
            feed.insert( talibfunc.SMA('long_ma',feed,100) )
            feed.insert( talibfunc.MAX('max',feed,self._breakout) )
            feed.insert( talibfunc.MIN('min',feed,self._breakout) )
            feed.insert( ATR( name='atr', period=100 ) )
    
    def onExitOk(self, position):
        if self._positions.has_key(position.getInstrument()):
            del self._positions[position.getInstrument()]
        else:
            logger.error('unknown position exit for %s, positions are: %s' % (position.getInstrument(),self._positions)) 
        
    def _calc_position_size(self, instrument, atr):
        #print 'atr = %f,equity = %0.2f,point_vaue = %0.2f,risk_factor = %f' % \
        #    (atr, self.getBroker().getCash(), self._db.get(instrument).point_value(), self._riskfactor )
        target_quant = self.getBroker().getCash() * self._riskfactor / \
                        (self._db.get(instrument).point_value() * atr)
        ret = round(target_quant)
        if ret < 1:
            ret = 1
        return ret
        
    def onBars(self, bars):
        #print 'On date %s, cash = %f' % (bars[bars.keys()[0]]['Datetime'], self.getBroker().getCash())
        for sym in bars.symbols():
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
                         bar.close(),
                         bar.max(),
                         bar.atr(),
                         0.0 if not self._tradeHigh.has_key(sym) else self._tradeHigh[sym],
                         0.0 if not self._tradeLow.has_key(sym) else self._tradeLow[sym])
                '''
                    
            if self._started and not self._positions.has_key(sym):
                '''
                Debug...
                trend = 'up' if bar.short_ma() >= bar.long_ma() else 'down'
                thresh =  bar.max() if trend == 'up' else bar.min()
                print 'trend: %s, close:%s, thresh:%s' % (trend, bar.close(),thresh)
                '''
                
                # check for long entry first
                if bar.short_ma() >= bar.long_ma() and bar.close() >= bar.max():
                    pos_size = self._calc_position_size(sym, bar.atr())
                    self._positions[sym] = self.enterLong(sym, pos_size, goodTillCanceled=True)
                    # set up our exit order
                    self._tradeHigh[sym] = bar.close()
                    self.exitPosition(self._positions[sym], stopPrice=self._tradeHigh[sym]-self._stop*bar.atr(), goodTillCanceled=True)
                # then short entry
                elif bar.short_ma() <= bar.long_ma() and bar.close() <= bar.min():
                    pos_size = self._calc_position_size(sym, bar.atr())
                    self._positions[sym] = self.enterShort(sym, pos_size, goodTillCanceled=True)
                    self._tradeLow[sym] = bar.close()
                    self.exitPosition(self._positions[sym], stopPrice=self._tradeLow[sym]+self._stop*bar.atr(), goodTillCanceled=True)
            elif self._positions.has_key(sym):
                # we need to adjust our exit daily 
                if self._positions[sym].isLong():
                    if bar.close() > self._tradeHigh[sym]:
                        self._tradeHigh[sym] = bar.close()
                    self.exitPosition(self._positions[sym], stopPrice=self._tradeHigh[sym]-self._stop*bar.atr(), goodTillCanceled=True)
                else:
                    if bar.close() < self._tradeLow[sym]:
                        self._tradeLow[sym] = bar.close()
                    self.exitPosition(self._positions[sym], stopPrice=self._tradeLow[sym]+self._stop*bar.atr(), goodTillCanceled=True)
         
    def exitPositions(self):
        for sym in self._positions:
            self.exitPosition(self._positions[sym])  
        self.getBroker().executeSessionClose()    
        
class ClenowBreakoutNoIntraDayStopStrategy(ClenowBreakoutStrategy):
    def __init__(self, barFeed, cash = 1000000, riskFactor = 0.002, breakout=50, stop=3.0, tradeStart=None):
        ClenowBreakoutStrategy.__init__(self, barFeed, cash, riskFactor, breakout, stop, tradeStart)

    def onBars(self, bars):
        #print 'On date %s, cash = %f' % (bars[bars.keys()[0]]['Datetime'], self.getBroker().getCash())
        for sym in bars.symbols():
            bar = bars.get_bar(sym)
            if not self._started:
                # need to check all of our indicators to see when they have data
                # we know that the 100d SMA will be last so just check it
                if not numpy.isnan(bar.long_ma()) and bars.datetime() >= self._tradeStart:
                    self._started = True
                                        
            if self._started and not self._positions.has_key(sym):
                '''
                Debug...
                trend = 'up' if bar.short_ma() >= bar.long_ma() else 'down'
                thresh =  bar.max() if trend == 'up' else bar.min()
                print 'trend: %s, close:%s, thresh:%s' % (trend, bar.close(),thresh)
                '''
                
                # check for long entry first
                if bar.short_ma() >= bar.long_ma() and bar.close() >= bar.max():
                    pos_size = self._calc_position_size(sym, bar.atr())
                    self._positions[sym] = self.enterLong(sym, pos_size, goodTillCanceled=True)
                    # set up our exit order
                    self._tradeHigh[sym] = bar.close()
                # then short entry
                elif bar.short_ma() <= bar.long_ma() and bar.close() <= bar.min():
                    pos_size = self._calc_position_size(sym, bar.atr())
                    self._positions[sym] = self.enterShort(sym, pos_size, goodTillCanceled=True)
                    self._tradeLow[sym] = bar.close()
            elif self._positions.has_key(sym):
                # we need to check our exit daily 
                if self._positions[sym].isLong():
                    if bar.close() > self._tradeHigh[sym]:
                        self._tradeHigh[sym] = bar.close()
                    elif bar.close() < self._tradeHigh[sym] - self._stop*bar.atr():
                        self.exitPosition(self._positions[sym], goodTillCanceled=True)
                else:
                    if bar.close() < self._tradeLow[sym]:
                        self._tradeLow[sym] = bar.close()
                    elif bar.close() > self._tradeLow[sym] + self._stop*bar.atr():
                        self.exitPosition(self._positions[sym], goodTillCanceled=True)
        