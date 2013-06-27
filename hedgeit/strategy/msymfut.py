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
                 compounding = True, parms = None):
        self._parms = self.defaultParms()
        if parms:
            self._parms.update(parms)          
          
        if broker is None:
            broker = BacktestingFuturesBroker(cash, barFeed, commission=FuturesCommission(2.50))
        Strategy.__init__(self, barFeed, cash, broker)
        if symbols is None:
            self._symbols = barFeed.symbols()
        else:
            self._symbols = symbols
        self._barFeed = barFeed
        self._longpositions = {}
        self._shortpositions = {}
        self._started = {}
        for sym in self._symbols:
            feed = self._barFeed.get_feed(sym)
            self._started[sym] = False
            feed.insert( ATR( name='atr', period=self._parms['atrPeriod'] ) )            
            
        self._db = InstrumentDb.Instance()
        
        self._riskfactor = self._parms['riskFactor']

        self._tradeHigh = {}
        self._tradeLow = {}
            
        self.prep_bar_feed()
        self._startingCash = cash
        self._compounding = compounding
        self._stop = self._parms['stop']
        self._limit = self._parms['limit']
        self._intraday = self._parms['intradayStop']
        self._dynamic = self._parms['dynamicStop']

    def defaultParms(self):
        '''
        Override (**optional**) for each strategy to provide a default 
        parameter dict. 
        
        Derived classes should always call the base class method to
        establish a starting dict and then add their own params
        
        :returns dict: parms dict
        '''
        return { 'riskFactor'    : 0.002,
                 'atrPeriod'     : 100,
                 'stop'          : None,
                 'intradayStop'  : True,
                 'dynamicStop'   : True,
                 'limit'         : None,
                 'intradayLimit' : False,
                 'dynamicLimit'  : True,
                 'longOnly'      : False,
                 'shortOnly'     : False }
        
    def showParms(self):
        logger.info('Strategy type %s, using parameter set:' % self.__class__.__name__)
        for k in sorted(self._parms.keys()):
            logger.info('  %-16s = %s' % (k, self._parms[k]))
            
    def getPositions(self, symbol = None):
        if symbol == None:
            ret = dict(self._longpositions)
            ret.update(self._shortpositions)
            return ret
        else:
            poslong = None if not self._longpositions.has_key(symbol) else self._longpositions[symbol] 
            posshort = None if not self._shortpositions.has_key(symbol) else self._shortpositions[symbol]
            return (poslong, posshort) 
    
    def prep_bar_feed(self):
        raise NotImplementedError()
    
    def hasPosition(self, sym):
        return self._longpositions.has_key(sym) or self._shortpositions.has_key(sym)
    
    def onExitOk(self, position):
        sym = position.getInstrument()
        if position.isLong() and self._longpositions.has_key(sym):
            del self._longpositions[sym]
        elif position.isShort() and self._shortpositions.has_key(sym):
            del self._shortpositions[sym]
        else:
            logger.error('unknown position exit for %s, positions are: %s' % (sym,self.getPositions())) 
            assert(False)
        
    def __calc_position_size(self, instrument, atr):
        #print 'atr = %f,equity = %0.2f,point_vaue = %0.2f,risk_factor = %f' % \
        #    (atr, self.getBroker().getCash(), self._db.get(instrument).point_value(), self._riskfactor )
        equity = self.getBroker().getCash() if self._compounding else self._startingCash
        target_quant = equity * self._riskfactor / \
                        (self._db.get(instrument).point_value() * atr)
        if target_quant < 1:
            # default to minimum of one contract - can lead to outsized risk - warning ends up being annoying
            # logger.warning('Insufficient equity to meet risk target for %s, risk multiple %0.3f' % (instrument,1.0/target_quant))
            ret = 1
        else:
            ret = round(target_quant)
        return (ret, ret * atr * self._db.get(instrument).point_value())
        
    def enterLongRiskSized(self, sym, bar):
        if self._parms['shortOnly']:
            return
        
        if self._longpositions.has_key(sym):
            logger.warning('Already have a %s position, will ignore...')
            return
        (pos_size, risk) = self.__calc_position_size(sym, bar.atr())
        position = self.enterLong(sym, pos_size, goodTillCanceled=True)
        position.setImpliedRisk(risk)
        self._tradeHigh[sym] = bar.close()
        if self._stop != None and self._intraday:
            self.exitPosition(position, stopPrice=self._tradeHigh[sym]-self._stop*bar.atr(), goodTillCanceled=True)
        self._longpositions[sym] = position

    def enterShortRiskSized(self, sym, bar):
        if self._parms['longOnly']:
            return

        if self._shortpositions.has_key(sym):
            logger.warning('Already have a %s position, will ignore...')
            return
        (pos_size, risk) = self.__calc_position_size(sym, bar.atr())
        position = self.enterShort(sym, pos_size, goodTillCanceled=True)
        position.setImpliedRisk(risk)        
        self._tradeLow[sym] = bar.close()
        if self._stop != None and self._intraday:
            self.exitPosition(position, stopPrice=self._tradeLow[sym]+self._stop*bar.atr(), goodTillCanceled=True)
        self._shortpositions[sym] = position
    
    def getCurrentExit(self, position):
        sym = position.getInstrument()
        order = position.getExitOrder()
        if order and position.getExitOrder().getType() == Order.Type.STOP:
            return position.getExitOrder().getStopPrice()
        elif order and position.getExitOrder().getType() == Order.Type.MARKET:
            return self._barFeed.get_feed(sym).get_last_close()
        elif self._stop != None:
            bars = self._barFeed.get_current_bars()
            cur_atr = bars.get_bar(sym).atr()
            if position.isLong():
                return self._tradeHigh[sym] - self._stop * cur_atr
            else:
                return self._tradeLow[sym] + self._stop * cur_atr                
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
                    if not bar.has_nan():
                        self._started[sym] = True
                                                
                if self._started[sym]:
                    self.onSymBar(sym,bar)

                    if self._longpositions.has_key(sym):
                        self.__handleStopLimit(self._longpositions[sym], bar)                    
                    if self._shortpositions.has_key(sym):
                        self.__handleStopLimit(self._shortpositions[sym], bar)
                                            
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
        for position in self.getPositions().itervalues():
            self.exitPosition(position)