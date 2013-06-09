'''
hedgeit.strategy.msymfut

Contains:
  class MultiSymFuturesBaseStrategy
'''

from hedgeit.feeds.db import InstrumentDb
from hedgeit.strategy.strategy import Strategy
from hedgeit.broker.brokers import BacktestingFuturesBroker
from hedgeit.feeds.indicators.atr import ATR
from hedgeit.common.logger import getLogger
from hedgeit.broker.commissions import FuturesCommission
from hedgeit.broker.orders import Order
import numpy
import datetime

logger = getLogger("strategy.msymfut")

class MultiSymFuturesBaseStrategy(Strategy):
    def __init__(self, barFeed, symbols = None, broker = None, cash = 1000000,\
                 riskFactor = 0.002, atrPeriod = 100, dynamic = True, 
                 stop = None, limit = None, intraday = True, 
                 tradeStart = None, compounding = True):
        if broker is None:
            broker = BacktestingFuturesBroker(cash, barFeed, commission=FuturesCommission(2.50))
        Strategy.__init__(self, barFeed, cash, broker)
        if symbols is None:
            self._symbols = barFeed.symbols()
        else:
            self._symbols = symbols
        self._barFeed = barFeed
        self._positions = {}
        self._started = {}
        for sym in self._symbols:
            feed = self._barFeed.get_feed(sym)
            self._started[sym] = False
            feed.insert( ATR( name='atr', period=atrPeriod ) )            
            
        self._db = InstrumentDb.Instance()
        
        self._riskfactor = riskFactor

        self._tradeHigh = {}
        self._tradeLow = {}
        if tradeStart != None:
            self._tradeStart = tradeStart
        else:
            # set this to an arbitrarily early date so we can compare 
            # directly in the onBars method below
            self._tradeStart = datetime.datetime(1900,1,1)
            
        self.prep_bar_feed()
        self._startingCash = cash
        self._compounding = compounding
        self._stop = stop
        self._limit = limit
        self._intraday = intraday
        self._dynamic = dynamic
        
    def getPositions(self, symbol = None):
        if symbol == None:
            return self._positions
        else:
            poslong = None if not self._positions.has_key('%s-long' % symbol) else self._positions['%s-long' % symbol] 
            posshort = None if not self._positions.has_key('%s-short' % symbol) else self._positions['%s-short' % symbol]
            return (poslong, posshort) 
    
    def prep_bar_feed(self):
        raise NotImplementedError()
    
    def getPositionKey(self, position):
        return '%s-%s' % (position.getInstrument(), 'long' if position.isLong() else 'short')
    
    def hasPosition(self, sym):
        return self._positions.has_key('%s-long' % sym) or self._positions.has_key('%s-short' % sym)
    
    def onExitOk(self, position):
        poskey = self.getPositionKey(position)
        if self._positions.has_key(poskey):
            del self._positions[poskey]
        else:
            logger.error('unknown position exit for %s, positions are: %s' % (position.getInstrument(),self._positions)) 
            assert(False)
        
    def __calc_position_size(self, instrument, atr):
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
        return (ret, ret * atr * self._db.get(instrument).point_value())
        
    def enterLongRiskSized(self, sym, bar):
        poskey = '%s-long' % sym
        if self._positions.has_key(poskey):
            logger.warning('Already have a %s position, will ignore...')
            return
        (pos_size, risk) = self.__calc_position_size(sym, bar.atr())
        position = self.enterLong(sym, pos_size, goodTillCanceled=True)
        position.setImpliedRisk(risk)
        self._tradeHigh[sym] = bar.close()
        if self._stop != None and self._intraday:
            self.exitPosition(position, stopPrice=self._tradeHigh[sym]-self._stop*bar.atr(), goodTillCanceled=True)
        self._positions[poskey] = position

    def enterShortRiskSized(self, sym, bar):
        poskey = '%s-short' % sym
        if self._positions.has_key(poskey):
            logger.warning('Already have a %s position, will ignore...')
            return
        (pos_size, risk) = self.__calc_position_size(sym, bar.atr())
        position = self.enterShort(sym, pos_size, goodTillCanceled=True)
        position.setImpliedRisk(risk)        
        self._tradeLow[sym] = bar.close()
        if self._stop != None and self._intraday:
            self.exitPosition(position, stopPrice=self._tradeLow[sym]+self._stop*bar.atr(), goodTillCanceled=True)
        self._positions[poskey] = position
    
    def getCurrentExit(self, position):
        if position.getExitOrder():
            return position.getExitOrder().getStopPrice()
        elif self._stop != None:
            bars = self._barFeed.get_current_bars()
            cur_atr = bars.get_bar(position.getInstrument()).atr()
            if position.isLong():
                return self._tradeHigh[position.getInstrument()] - self._stop * cur_atr
            else:
                return self._tradeLow[position.getInstrument()] + self._stop * cur_atr                
        else:
            # indicate no stop with 0.0
            return 0.0
        
    def __handleStopLimit(self, pos, bar):
        # first check the position to see if there is already a market exit 
        # order.  If so, we don't want to do anything
        exit_ = pos.getExitOrder()
        if exit_ and exit_.getType() == Order.Type.MARKET:
            return
        elif not pos.entryFilled():
            return

        # update tradeHigh for long positions and tradeLow for shorts
        sym = pos.getInstrument()
        if pos.isLong():
            if bar.close() > self._tradeHigh[sym]:
                self._tradeHigh[sym] = bar.close()
        else:
            if bar.close() < self._tradeLow[sym]:
                self._tradeLow[sym] = bar.close()

        # handle stop processing
        if self._stop != None and self._intraday:
            if pos.isLong():
                self.exitPosition(pos, stopPrice=self._tradeHigh[sym]-self._stop*bar.atr(), goodTillCanceled=True)
            else:
                self.exitPosition(pos, stopPrice=self._tradeLow[sym]+self._stop*bar.atr(), goodTillCanceled=True)
        elif self._stop != None and not self._intraday:
            if pos.isLong():
                if bar.close() < self._tradeHigh[sym] - ( self._stop * bar.atr() ):
                    self.exitPosition(pos, goodTillCanceled=True)
            else:
                if bar.close() > self._tradeLow[sym] + ( self._stop * bar.atr() ):
                    self.exitPosition(pos, goodTillCanceled=True)
                                                
        # handle limit processing
        if self._limit != None and pos.entryFilled():
            # not going to support intraday limit exit - this will
            # require a bit of work since there is essentially two
            # exit orders that constitute a one-cancels-other situation
            tradeEntry = pos.getEntryOrder().getExecutionInfo().getPrice()
            if pos.isLong():
                if bar.close() > tradeEntry + (self._limit * bar.atr()):
                    self.exitPosition(pos, goodTillCanceled=True)                                    
            else:
                if bar.close() < tradeEntry - (self._limit * bar.atr()):
                    self.exitPosition(pos, goodTillCanceled=True)                                    
        
    def onBars(self, bars):
        for sym in self._symbols:
            if sym in bars.symbols():
                bar = bars.get_bar(sym)
                if not self._started[sym]:
                    if not bar.has_nan() and bars.datetime() >= self._tradeStart:
                        self._started[sym] = True
                                                
                if self._started[sym]:
                    self.onSymBar(sym,bar)

                    poslong = '%s-long' % sym
                    posshort = '%s-short' % sym                    
                    if self._positions.has_key(poslong):
                        self.__handleStopLimit(self._positions[poslong], bar)                    
                    if self._positions.has_key(posshort):
                        self.__handleStopLimit(self._positions[posshort], bar)
                                            
    def onSymBar(self, symbol, bar):
        '''
        Override (**mandatory**) to get notified when a new bar is available 
        for a particular symbol.
        
        When using on MultiSymFuturesBaseStrategy, this is where the user will
        typically implement the main bulk of the strategy.
        
        :param string symbol: symbol string
        :param bar: a :class:`hedgeit.feeds.bar` instance
        '''
        raise NotImplementedError()
          
    def exitPositions(self):
        for sym in self._positions:
            self.exitPosition(self._positions[sym])