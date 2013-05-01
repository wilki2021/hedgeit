'''
hedgeit.strategy.strategy

Contains:
  class RSICounterStrategy
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

class RSICounterStrategy(Strategy):
    def __init__(self, barFeed, symbols = None, broker = None, cash = 1000000,
                 riskFactor = 0.002, period=14, stop=2.0, tradeStart=None):
        if broker is None:
            broker = BacktestingFuturesBroker(cash, barFeed, commission=FuturesCommission(2.50))
        if symbols is None:
            self._symbols = barFeed.symbols()
        else:
            self._symbols = symbols
        Strategy.__init__(self, barFeed, cash, broker)
        self.__barFeed = barFeed
        self._positions = {}
        self._started = {}
        self._db = InstrumentDb.Instance()
        self._riskfactor = riskFactor
        self._period = period
        self._stop = stop
        self._tradeEntry = {}
        self._tradeExit = {}
        self._lastRSI = {}
        self._tripped = {}
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
            feed.insert( talibfunc.RSI('rsi',feed,self._period) )
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
                if not self._started.has_key(sym):
                    # need to check all of our indicators to see when they have data
                    # we know that the 100d SMA will be last so just check it
                    if not numpy.isnan(bar.atr()) and bars.datetime() >= self._tradeStart:
                        self._started[sym] = True
                        
                if self._started.has_key(sym):
                    '''
                    # debug
                    print '%s,%s,position:%s,close:%0.2f,rsi:%0.2f,atr:%0.2f' % \
                            (bar.datetime(),
                             sym,
                             self._positions.has_key(sym),
                             bar.close(),
                             bar.rsi(),
                             bar.atr())
                    '''

                if not self._lastRSI.has_key(sym):
                    self._lastRSI[sym] = bar.rsi()
                                         
                if self._started.has_key(sym) and not self._positions.has_key(sym):
                    '''
                    Debug...
                    trend = 'up' if bar.short_ma() >= bar.long_ma() else 'down'
                    thresh =  bar.max() if trend == 'up' else bar.min()
                    print 'trend: %s, close:%s, thresh:%s' % (trend, bar.close(),thresh)
                    '''
                    if bar.rsi() < 20 or bar.rsi() > 80:
                        self._tripped[sym] = True
                        
                    # check for long entry first
                    if self._tripped.has_key(sym) and bar.rsi() > self._lastRSI[sym]:
                        pos_size = self._calc_position_size(sym, bar.atr())
                        if numpy.isnan(pos_size):
                            print bar
                            assert(False)
                        self._positions[sym] = self.enterLong(sym, pos_size, goodTillCanceled=True)
                        # set up our exit order
                        self._tradeEntry[sym] = bar.close()
                        self._tradeExit[sym] = bar.close() + 2.5 * bar.atr()
                        self.exitPosition(self._positions[sym], stopPrice=bar.close()-self._stop*bar.atr(), goodTillCanceled=True)
                        del self._tripped[sym]
                    # then short entry
                    elif self._tripped.has_key(sym) and bar.rsi() < self._lastRSI[sym]:
                        pos_size = self._calc_position_size(sym, bar.atr())
                        if numpy.isnan(pos_size):
                            print bar
                            outfile = open('%s-feed.csv' % sym,'w')
                            self.__barFeed.get_feed(sym).write_csv(outfile)
                            outfile.close()
                            assert(False)
                        self._positions[sym] = self.enterShort(sym, pos_size, goodTillCanceled=True)
                        self._tradeEntry[sym] = bar.close()
                        self._tradeExit[sym] = bar.close() - 2.5 * bar.atr()
                        self.exitPosition(self._positions[sym], stopPrice=bar.close()+self._stop*bar.atr(), goodTillCanceled=True)
                        del self._tripped[sym]
                elif self._positions.has_key(sym):
                    # we need to adjust our exit daily 
                    if self._positions[sym].isLong():
                        if bar.close() > self._tradeExit[sym]:
                            self.exitPosition(self._positions[sym], goodTillCanceled=True)
                    else:
                        if bar.close() < self._tradeExit[sym]:
                            self.exitPosition(self._positions[sym], goodTillCanceled=True)
                self._lastRSI[sym] = bar.rsi()
                             
    def exitPositions(self):
        for sym in self._positions:
            self.exitPosition(self._positions[sym])  
        self.getBroker().executeSessionClose()    