# PyAlgoTrade
# 
# Copyright 2011 Gabriel Martin Becedillas Ruiz
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#    http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
######################################################################

## Broker
import broker
from commissions import *
from fillstrategy import *
import orders
from hedgeit.common.logger import getLogger
from hedgeit.feeds.db import InstrumentDb
import copy

logger = getLogger("broker.backtesting")
######################################################################
## These are backtest-specific orders derived from the base classes
## in the orders module.

class BacktestingOrder:
    def __init__(self):
        pass

    def checkCanceled(self, broker, bars):
        # This check is only for accepted orders that are not GTC.
        if self.getGoodTillCanceled() or not self.isAccepted():
            return

        # TODO - for now every bar is a session close since we are only
        # dealing with daily data.  Revisit this if ever using <day data
        # If its the last bar of the session and the order was not filled then cancel it.
        # bar_ = bars.getBar(self.getInstrument())
        # if bar_ != None and bar_.getSessionClose():
        broker.cancelOrder(self)

    def tryExecute(self, broker, bars):
        if self.isAccepted():
            # Process the order if there is data available.
            bar_ = bars.get_bar(self.getInstrument())
            if bar_ != None:
                self.tryExecuteImpl(broker, bar_)
            # Check if the order has to be canceled.
            self.checkCanceled(broker, bars)

class MarketOrder(orders.MarketOrder, BacktestingOrder):
    def __init__(self, action, instrument, quantity, onClose):
        orders.MarketOrder.__init__(self, action, instrument, quantity, onClose)
        BacktestingOrder.__init__(self)

    def tryExecuteImpl(self, broker_, bar_):
        price = broker_.getFillStrategy().fillMarketOrder(self, broker_, bar_)
        if price != None:
            broker_.commitOrderExecution(self, price, self.getQuantity(), bar_.datetime())

class LimitOrder(orders.LimitOrder, BacktestingOrder):
    def __init__(self, action, instrument, limitPrice, quantity):
        orders.LimitOrder.__init__(self, action, instrument, limitPrice, quantity)
        BacktestingOrder.__init__(self)

    def tryExecuteImpl(self, broker_, bar_):
        price = broker_.getFillStrategy().fillLimitOrder(self, broker_, bar_)
        if price != None:
            broker_.commitOrderExecution(self, price, self.getQuantity(), bar_.datetime())

class StopOrder(orders.StopOrder, BacktestingOrder):
    def __init__(self, action, instrument, stopPrice, quantity):
        orders.StopOrder.__init__(self, action, instrument, stopPrice, quantity)
        BacktestingOrder.__init__(self)

    def tryExecuteImpl(self, broker_, bar_):
        price = broker_.getFillStrategy().fillStopOrder(self, broker_, bar_)
        if price != None:
            broker_.commitOrderExecution(self, price, self.getQuantity(), bar_.datetime())

# http://www.sec.gov/answers/stoplim.htm
# http://www.interactivebrokers.com/en/trading/orders/stopLimit.php
class StopLimitOrder(orders.StopLimitOrder, BacktestingOrder):
    def __init__(self, action, instrument, limitPrice, stopPrice, quantity):
        orders.StopLimitOrder.__init__(self, action, instrument, limitPrice, stopPrice, quantity)
        BacktestingOrder.__init__(self)

    def __stopHit(self, broker_, bar_):
        ret = False
        high = broker_.getBarHigh(bar_)
        low = broker_.getBarLow(bar_)
        stopPrice = self.getStopPrice()

        # If the bar is above the stop price, or the bar includes the stop price, the stop was hit.
        if self.getAction() in [orders.Order.Action.BUY, orders.Order.Action.BUY_TO_COVER]:
            if low >= stopPrice or stopPrice <= high:
                ret = True
        # If the bar is below the stop price, or the bar includes the stop price, the stop was hit.
        elif self.getAction() in [orders.Order.Action.SELL, orders.Order.Action.SELL_SHORT]:
            if high <= stopPrice or stopPrice >= low:
                ret = True
        else: # Unknown action
            assert(False)
        return ret

    def tryExecuteImpl(self, broker_, bar_):
        justHitStopPrice = False

        # Check if we have to activate the limit order first.
        if not self.isLimitOrderActive() and self.__stopHit(broker_, bar_):
            self.setLimitOrderActive(True)
            justHitStopPrice = True

        # Check if we have ever reached the limit price
        if self.isLimitOrderActive():
            price = broker_.getFillStrategy().fillStopLimitOrder(self, broker_, bar_, justHitStopPrice)
            if price != None:
                broker_.commitOrderExecution(self, price, self.getQuantity(), bar_.datetime())


class BacktestingBroker(broker.Broker):
    '''
    Backtesting broker.
    '''
    
    def __init__(self, cash, barFeed, commission = None):
        '''
        Constructor.
        
        :param number cash: The initial amount of cash.
        :param MultiFeed barFeed: The bar feed that will provide the bars.
        :param Commission commission: An object responsible for calculating order commissions.
        
        :raises: AssertionError if cash is a negative number
        '''
        broker.Broker.__init__(self)

        assert(cash >= 0)
        self.__cash = cash
        if commission is None:
            self.__commission = NoCommission()
        else:
            self.__commission = commission
        self.__shares = {}
        self.__activeOrders = []
        self.__useAdjustedValues = False
        self.__fillStrategy = DefaultStrategy()

        # It is VERY important that the broker subscribes to barfeed events before the strategy.
        barFeed.subscribe(self.onBars)
        self.__barFeed = barFeed
        self.__allowNegativeCash = False

    def getBar(self, bars, instrument):
        ret = bars.get_bar(instrument)
        if ret == None:
            ret = self.__barFeed.getLastBar(instrument)
        return ret

    def setAllowNegativeCash(self, allowNegativeCash):
        self.__allowNegativeCash = allowNegativeCash

    def getCash(self):
        """Returns the available cash."""
        return self.__cash

    def setCash(self, cash):
        """Sets the available cash."""
        self.__cash = cash

    def getCommission(self):
        """Returns the commission instance."""
        return self.__commission

    def setCommission(self, commission):
        """Sets the commission instance."""
        self.__commission = commission

    def setFillStrategy(self, strategy):
        """Sets the :class:`FillStrategy` to use."""
        self.__fillStrategy = strategy 

    def getFillStrategy(self):
        """Returns the :class:`FillStrategy` currently set."""
        return self.__fillStrategy

    def getUseAdjustedValues(self):
        return self.__useAdjustedValues

    def setUseAdjustedValues(self, useAdjusted):
        self.__useAdjustedValues = useAdjusted

    def getActiveOrders(self):
        return self.__activeOrders

    def getShares(self, instrument):
        self.__shares.setdefault(instrument, 0)
        return self.__shares[instrument]

    def getPositions(self):
        return self.__shares

    def getActiveInstruments(self):
        return [instrument for instrument, shares in self.__shares.iteritems() if shares != 0]

    def getEquityWithBars(self, bars):
        ret = self.getCash()
        if bars != None:
            for instrument, shares in self.__shares.iteritems():
                instrumentPrice = self.getBarClose(self.getBar(bars, instrument))
                ret += instrumentPrice * shares
        return ret

    def getValue(self):
        return self.getEquityWithBars(self.__barFeed.get_current_bars())

    def getEquity(self):
        """Returns the portfolio value (cash + shares)."""
        return self.getEquityWithBars(self.__barFeed.get_current_bars())

    # Tries to commit an order execution. Returns True if the order was commited, or False is there is not enough cash.
    def commitOrderExecution(self, order, price, quantity, dateTime):
        if order.getAction() in [orders.Order.Action.BUY, orders.Order.Action.BUY_TO_COVER]:
            cost = price * quantity * -1
            assert(cost < 0)
            sharesDelta = quantity
        elif order.getAction() in [orders.Order.Action.SELL, orders.Order.Action.SELL_SHORT]:
            cost = price * quantity
            assert(cost > 0)
            sharesDelta = quantity * -1
        else: # Unknown action
            assert(False)

        ret = False
        commission = self.getCommission().calculate(order, price, quantity)
        cost -= commission
        resultingCash = self.getCash() + cost

        # Check that we're ok on cash after the commission.
        if resultingCash >= 0 or self.__allowNegativeCash:
            # Commit the order execution.
            self.setCash(resultingCash)
            self.__shares[order.getInstrument()] = self.getShares(order.getInstrument()) + sharesDelta
            ret = True

            # Update the order.
            orderExecutionInfo = orders.OrderExecutionInfo(price, quantity, commission, dateTime)
            order.setExecuted(orderExecutionInfo)
            logger.debug('Order executed: %s' % orderExecutionInfo)
        else:
            logger.debug("Not enough money to fill order %s" % (order))

        return ret

    def placeOrder(self, order):
        logger.debug('Placing: %s' % order)
        if order.isAccepted():
            if order not in self.__activeOrders:
                self.__activeOrders.append(order)
            order.setDirty(False)
        else:
            raise Exception("The order was already processed")

    def onBars(self, bars):
        activeOrders = copy.copy(self.__activeOrders)

        for order in activeOrders:
            if order.getInstrument() in bars.symbols():
                if order.isAccepted():
                    order.tryExecute(self, bars)
                    if not order.isAccepted():
                        self.__activeOrders.remove(order)
                        self.getOrderUpdatedEvent().emit(self, order)
                else:
                    self.__activeOrders.remove(order)
                    self.getOrderUpdatedEvent().emit(self, order)
                
    def executeSessionClose(self):
        '''
        This is available for the Strategy class to use to close open positions 
        at the end of the data feed.  It assumes that the Strategy has entered
        market orders to close out any active positions and then sets the 
        FillOnClose flag for each and then re-evaluates against the last bar
        
        Note that it is the responsibility of the strategy to ensure that only
        Market orders that should be executed are currently active/accepted
        '''
        for order in self.__activeOrders:
            if order.getType() == order.Type.MARKET:
                order.setFillOnClose(True)
        self.onBars(self.__barFeed.get_current_bars())

    def createMarketOrder(self, action, instrument, quantity, onClose = False):
        return MarketOrder(action, instrument, quantity, onClose)

    def createLimitOrder(self, action, instrument, limitPrice, quantity):
        return LimitOrder(action, instrument, limitPrice, quantity)

    def createStopOrder(self, action, instrument, stopPrice, quantity):
        return StopOrder(action, instrument, stopPrice, quantity)

    def createStopLimitOrder(self, action, instrument, stopPrice, limitPrice, quantity):
        return StopLimitOrder(action, instrument, limitPrice, stopPrice, quantity)

    def cancelOrder(self, order):
        if order.isFilled():
            raise Exception("Can't cancel order that has already been filled")
        order.setState(orders.Order.State.CANCELED)

    def getBarOpen(self, bar_):
        return bar_.open()
    
        # leave these accessors in Broker in case we ever want to revisit the
        # adjusted close capability
        #if self.getUseAdjustedValues():
        #    ret = bar_.getAdjOpen()
        #else:
        #    ret = bar_.getOpen()
        #return ret

    def getBarHigh(self, bar_):
        return bar_.high()

    def getBarLow(self, bar_):
        return bar_.low()

    def getBarClose(self, bar_):
        return bar_.close()

class BacktestingFuturesBroker(BacktestingBroker):
    '''
    Backtesting broker for futures trades
    '''
    
    def __init__(self, cash, barFeed, commission = None):
        '''
        Constructor.
        
        :param number cash: The initial amount of cash.
        :param MultiFeed barFeed: The bar feed that will provide the bars.
        :param Commission commission: An object responsible for calculating order commissions.
        
        :raises: AssertionError if cash is a negative number
        '''
        BacktestingBroker.__init__(self, cash, barFeed, commission)
        self._last_marktomarket = {}
        self._db = InstrumentDb.Instance()

    def calc_margin(self, instrument=None, quantity=0):
        '''
        Calculates margin reqmts, optionally for a new position.  
        
        :param str instrument:if for a new position, string containing symbol name
        :param number quantity:if for a new position, numbef or contracts
        
        :returns number:margin requirement
        '''
        ret = 0.0;
        # first we need to consider maintenance margin on all current positions
        for instrument, shares in self.getPositions().iteritems():
            ret += self._db.get(instrument).maint_margin() * abs(shares)
            
        # now, check for initial margin against this new position
        if instrument != None:
            ret += self._db.get(instrument).initial_margin() * quantity

        return ret
        
    def margin_check(self, instrument=None, quantity=0):
        '''
        Performs a margin check.  It is assumed that the current cash position in 
        the account reflects a "mark-to-market" of all positions up until the most 
        recent bar.

        :param str instrument:if for a new position, string containing symbol name
        :param number quantity:if for a new position, numbef or contracts
        
        :returns boolean:True = sufficient margin, False = insufficient margin
        '''        
        margin = self.getCash() - self.calc_margin(instrument, quantity)
        if margin < 0:
            logger.error("Insufficient margin, need additional %d$" % -margin)
        return True if margin >= 0.0 else False
    
    def mark_to_market(self, bars):
        '''
        Performs a mark-to-market calculation for all open positions.  The
        cash position is the account is updated according to the bar delta
        passed in.  Note this assumes the closing price as the settlement
        price which may or may not be technically accurate, but nevertheless
        all that we have.
        '''
        cash = self.getCash()
        for instrument, shares in self.getPositions().iteritems():
            if instrument in bars.symbols():
                close = self.getBarClose(self.getBar(bars, instrument))            
                delta = (close - self._last_marktomarket[instrument]) * self._db.get(instrument).point_value() 
                self._last_marktomarket[instrument] = close
                cash += delta * shares            
        self.setCash(cash)
    
    def get_last_mark_to_market(self):
        return self._last_marktomarket
    
    # Tries to commit an order execution. Returns True if the order was commited, or False is there is not enough cash.
    def commitOrderExecution(self, order, price, quantity, dateTime):
        instrument = order.getInstrument()
        # first determine if we need a margin check and execute one        
        if order.getAction() in [orders.Order.Action.BUY, orders.Order.Action.SELL_SHORT]:
            if not self.margin_check(instrument, quantity):
                raise Exception("Not Enough Margin!")
        
        if order.getAction() in [orders.Order.Action.BUY, orders.Order.Action.BUY_TO_COVER]:
            sharesDelta = quantity
        elif order.getAction() in [orders.Order.Action.SELL, orders.Order.Action.SELL_SHORT]:
            sharesDelta = quantity * -1
        else: # Unknown action
            assert(False)

        if order.getAction() in [orders.Order.Action.SELL, orders.Order.Action.BUY_TO_COVER]:
            # we are closing a position and need to update the account equity
            delta = (price - self._last_marktomarket[instrument]) * self._db.get(instrument).point_value() 
            self.setCash(self.getCash() - delta * sharesDelta)

             
        # initialize the marktomarket reference as our order price
        self._last_marktomarket[instrument] = price
        
        commission = self.getCommission().calculate(order, price, quantity)
        resultingCash = self.getCash() - commission

        # It's effectively impossible that we run out of cash trading futures
        # before hitting a margin limit so ignore the case where resultingCash
        # may be < 0.

        # Commit the order execution.
        self.setCash(resultingCash)
        self.getPositions()[instrument] = self.getShares(instrument) + sharesDelta

        # Update the order.
        orderExecutionInfo = orders.OrderExecutionInfo(price, quantity, commission, dateTime)
        order.setExecuted(orderExecutionInfo)
        logger.debug('Order executed: %s\n%s' % (orderExecutionInfo,order))

        return True

    def onBars(self, bars):
        super( BacktestingFuturesBroker, self ).onBars( bars )
        self.mark_to_market(bars)
        if not self.margin_check():
            raise Exception("Margin Call!")
        
    def getEquityWithBars(self, bars):
        # because the futures broker always performs mark-to-market after 
        # processing a bar set, the cash always represents account equity
        return self.getCash()
        