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
    def __init__(self, barFeed, symbols = None, broker = None, cash = 1000000,\
                 riskFactor = 0.002, period=50, stop=3.0, tradeStart=None,
                 compounding = True):
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
        self._period = period
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
        self._startingCash = cash
        self._compounding = compounding
        
    def getPositions(self):
        return self._positions
    
    def __prep_bar_feed(self):
        for sym in self._symbols:
            feed = self.__barFeed.get_feed(sym)
            feed.insert( talibfunc.SMA('short_ma',feed,self._period) )
            feed.insert( talibfunc.SMA('long_ma',feed,2*self._period) )
            feed.insert( talibfunc.MAX('max',feed,self._period) )
            feed.insert( talibfunc.MIN('min',feed,self._period) )
            feed.insert( ATR( name='atr', period=2*self._period ) )
    
    def onExitOk(self, position):
        if self._positions.has_key(position.getInstrument()):
            del self._positions[position.getInstrument()]
        else:
            logger.error('unknown position exit for %s, positions are: %s' % (position.getInstrument(),self._positions)) 
        
    def _calc_position_size(self, instrument, atr):
        #print 'atr = %f,equity = %0.2f,point_vaue = %0.2f,risk_factor = %f' % \
        #    (atr, self.getBroker().getCash(), self._db.get(instrument).point_value(), self._riskfactor )
        equity = self.getBroker().getCash() if self._compounding else self._startingCash
        target_quant = equity * self._riskfactor / \
                        (self._db.get(instrument).point_value() * atr)
        if target_quant < 1:
            logger.warning('Insufficient equity to meet risk target for %s, risk multiple %0.3f' % (instrument,1.0/target_quant))
            ret = 1
        else:
            ret = round(target_quant)
        return (ret, ret * atr * self._db.get(instrument).point_value() / self.getBroker().getCash())
        
    def enterLong(self, instrument, quantity, impliedRisk, limit=None, stop=None, goodTillCanceled = False):
        ret = Strategy.enterLong(self, instrument, quantity, limit, stop, goodTillCanceled)
        ret.setImpliedRisk(impliedRisk)
        return ret

    def enterShort(self, instrument, quantity, impliedRisk, limit=None, stop=None, goodTillCanceled = False):
        ret = Strategy.enterShort(self, instrument, quantity, limit, stop, goodTillCanceled)
        ret.setImpliedRisk(impliedRisk)
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
                        (pos_size, risk) = self._calc_position_size(sym, bar.atr())
                        self._positions[sym] = self.enterLong(sym, pos_size, risk, goodTillCanceled=True)
                        # set up our exit order
                        self._tradeHigh[sym] = bar.close()
                        self.exitPosition(self._positions[sym], stopPrice=self._tradeHigh[sym]-self._stop*bar.atr(), goodTillCanceled=True)
                    # then short entry
                    elif bar.short_ma() <= bar.long_ma() and bar.close() <= bar.min():
                        (pos_size, risk) = self._calc_position_size(sym, bar.atr())
                        self._positions[sym] = self.enterShort(sym, pos_size, risk, goodTillCanceled=True)
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
         
    def getExitOrders(self):
        ret = []
        for sym in self._positions:
            if self._positions[sym].entryFilled():
                ret.append(self._positions[sym].getExitOrder())
            
        return ret
            
    def exitPositions(self):
        for sym in self._positions:
            # we have two cases to detect/handle.  If the position has been entered
            # then we want to enter a new market order to close it so that the trade
            # reflects the proper p/l.  If the position has not been entered then 
            # this is a new trade that needs to be executed on the next bar and we
            # don't actually want to report it as a trade, but rather a trade alert
            if self._positions[sym].entryFilled():
                self.exitPosition(self._positions[sym])
            else:
                self.getBroker().cancelOrder(self._positions[sym].getEntryOrder())
        self.getBroker().executeSessionClose()    
        
    def tradeAlerts(self):
        ret = []
        for sym in self._positions:
            if not self._positions[sym].entryFilled():
                ret.append((self._positions[sym].getEntryOrder(), self._positions[sym].getImpliedRisk()))
        return ret  
        
        
class ClenowBreakoutNoIntraDayStopStrategy(ClenowBreakoutStrategy):
    def __init__(self, barFeed, symbols = None, broker = None, cash = 1000000,\
                 riskFactor = 0.002, period=50, stop=3.0, tradeStart=None,
                 compounding = True):
        ClenowBreakoutStrategy.__init__(self, barFeed, symbols, broker, cash,\
                                        riskFactor, period, stop, tradeStart,
                                        compounding)

    def onBars(self, bars):
        #print 'On date %s, cash = %f' % (bars[bars.keys()[0]]['Datetime'], self.getBroker().getCash())
        for sym in self._symbols:
            if sym in bars.symbols():
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
                        (pos_size, risk) = self._calc_position_size(sym, bar.atr())
                        self._positions[sym] = self.enterLong(sym, pos_size, risk, goodTillCanceled=True)
                        # set up our exit order
                        self._tradeHigh[sym] = bar.close()
                    # then short entry
                    elif bar.short_ma() <= bar.long_ma() and bar.close() <= bar.min():
                        (pos_size, risk) = self._calc_position_size(sym, bar.atr())
                        self._positions[sym] = self.enterShort(sym, pos_size, risk, goodTillCanceled=True)
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
        