# PyAlgoTrade
# 
# Copyright 2011 Gabriel Martin Becedillas Ruiz
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#   http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
hedgeit.feeds.bar

Contains:
  class Position
  class LongPosition
  class ShortPosition
  
.. moduleauthor:: Gabriel Martin Becedillas Ruiz <gabriel.becedillas@gmail.com>
"""

import hedgeit.broker.broker as broker
from hedgeit.broker.orders import Order
from hedgeit.analyzer import returns

class Position:
    """Base class for positions. 

    :param strategy: The strategy that this position belongs to.
    :type strategy: :class:`pyalgotrade.strategy.Strategy`.
    :param entryOrder: The order used to enter the position.
    :type entryOrder: :class:`pyalgotrade.broker.Order`
    :param goodTillCanceled: True if the entry order should be set as good till canceled.
    :type goodTillCanceled: boolean.

    .. note::
        This is a base class and should not be used directly.
    """

    def __init__(self, strategy, entryOrder, goodTillCanceled):
        self.__strategy = strategy
        self.__entryOrder = entryOrder
        self.__exitOrder = None
        self.__exitOnSessionClose = False
        entryOrder.setGoodTillCanceled(goodTillCanceled)
        self.__exitDateTime = None

    def getStrategy(self):
        return self.__strategy

    def entryFilled(self):
        """Returns True if the entry order was filled."""
        return self.__entryOrder != None and self.__entryOrder.isFilled()

    def exitFilled(self):
        """Returns True if the exit order was filled."""
        return self.__exitOrder != None and self.__exitOrder.isFilled()

    def getGoodTillCanceled(self):
        return self.__entryOrder.getGoodTillCanceled()

    def setExitOnSessionClose(self, exitOnSessionClose):
        """Set to True to automatically place an exit order when the session is about to close. Only useful for intraday trading.

        .. note::
            If the entry order was not filled by the time the session is about to close, it will get canceled.
        """
        self.__exitOnSessionClose = exitOnSessionClose

    def getExitOnSessionClose(self):
        """Returns True if an order to exit the position should be automatically submitted when the session is about to close."""
        return self.__exitOnSessionClose

    def getEntryOrder(self):
        """Returns the :class:`pyalgotrade.broker.Order` used to enter the position."""
        return self.__entryOrder

    def setExitOrder(self, exitOrder):
        self.__exitOrder = exitOrder

    def getExitOrder(self):
        """Returns the :class:`pyalgotrade.broker.Order` used to exit the position. If this position hasn't been closed yet, None is returned."""
        return self.__exitOrder

    def getInstrument(self):
        """Returns the instrument used for this position."""
        return self.__entryOrder.getInstrument()

    def getQuantity(self):
        """Returns the number of shares used to enter this position."""
        return self.__entryOrder.getQuantity()

    def close(self, limitPrice, stopPrice, goodTillCanceled = None):
        # If a previous exit order was pending, cancel it.
        if self.getExitOrder() != None:
            self.getStrategy().getBroker().cancelOrder(self.getExitOrder())

        closeOrder = self.buildExitOrder(limitPrice, stopPrice)

        # If goodTillCanceled was not set, match the entry order.
        if goodTillCanceled == None:
            goodTillCanceled = self.__entryOrder.getGoodTillCanceled()
        closeOrder.setGoodTillCanceled(goodTillCanceled)

        self.getStrategy().getBroker().placeOrder(closeOrder)
        self.setExitOrder(closeOrder)

    def checkExitOnSessionClose(self, bars):
        ret = None
        # If the position was set to exit on session close, and this is the penultimate bar then:
        # * Create the exit order if the entry was filled.
        # * Cancel the entry order if it was not filled so far.
        if self.__exitOnSessionClose and self.__exitOrder == None:
            bar = bars.getBar(self.getInstrument())
            if bar and bar.getBarsTillSessionClose() == 1:
                if self.entryFilled():
                    ret = self.buildExitOnSessionCloseOrder()
                    self.getStrategy().getBroker().placeOrder(ret)
                    self.setExitOrder(ret)
                else:
                    self.getStrategy().getBroker().cancelOrder(self.getEntryOrder())
        return ret

    def getReturn(self, includeCommissions=True):
        """Returns the position's returns."""
        if not self.entryFilled():
            raise Exception("Position not opened yet")
        elif not self.exitFilled():
            raise Exception("Position not closed yet")
        return self.getReturnImpl(includeCommissions)

    def getReturnImpl(self, includeCommissions):
        raise NotImplementedError()

    def getNetProfit(self, includeCommissions=True):
        """Returns the position's net profit."""
        if not self.entryFilled():
            raise Exception("Position not opened yet")
        elif not self.exitFilled():
            raise Exception("Position not closed yet")
        return self.getNetProfitImpl(includeCommissions)

    def getNetProfitImpl(self, includeCommissions):
        raise NotImplementedError()

    def buildExitOrder(self, limitPrice, stopPrice):
        raise NotImplementedError()

    def buildExitOnSessionCloseOrder(self):
        raise NotImplementedError()

    def isLong(self):
        raise NotImplementedError()

    def isShort(self):
        return not self.isLong()

# This class is reponsible for order management in long positions.
class LongPosition(Position):
    def __init__(self, strategy, instrument, limitPrice, stopPrice, quantity, goodTillCanceled):
        if limitPrice == None and stopPrice == None:
            entryOrder = strategy.getBroker().createMarketOrder(Order.Action.BUY, instrument, quantity, False)
        elif limitPrice != None and stopPrice == None:
            entryOrder = strategy.getBroker().createLimitOrder(Order.Action.BUY, instrument, limitPrice, quantity)
        elif limitPrice == None and stopPrice != None:
            entryOrder = strategy.getBroker().createStopOrder(Order.Action.BUY, instrument, stopPrice, quantity)
        elif limitPrice != None and stopPrice != None:
            entryOrder = strategy.getBroker().createStopLimitOrder(Order.Action.BUY, instrument, stopPrice, limitPrice, quantity)
        else:
            assert(False)

        Position.__init__(self, strategy, entryOrder, goodTillCanceled)
        strategy.getBroker().placeOrder(entryOrder)

    def __getPosTracker(self):
        ret = returns.PositionTracker()
        entryExecInfo = self.getEntryOrder().getExecutionInfo()
        exitExecInfo = self.getExitOrder().getExecutionInfo()
        ret.buy(entryExecInfo.getQuantity(), entryExecInfo.getPrice(), entryExecInfo.getCommission())
        ret.sell(exitExecInfo.getQuantity(), exitExecInfo.getPrice(), exitExecInfo.getCommission())
        return ret

    def getReturnImpl(self, includeCommissions):
        return self.__getPosTracker().getReturn(self.getExitOrder().getExecutionInfo().getPrice(), includeCommissions)

    def getNetProfitImpl(self, includeCommissions):
        return self.__getPosTracker().getNetProfit(self.getExitOrder().getExecutionInfo().getPrice(), includeCommissions)

    def buildExitOrder(self, limitPrice, stopPrice):
        if limitPrice == None and stopPrice == None:
            ret = self.getStrategy().getBroker().createMarketOrder(Order.Action.SELL, self.getInstrument(), self.getQuantity(), False)
        elif limitPrice != None and stopPrice == None:
            ret = self.getStrategy().getBroker().createLimitOrder(Order.Action.SELL, self.getInstrument(), limitPrice, self.getQuantity())
        elif limitPrice == None and stopPrice != None:
            ret = self.getStrategy().getBroker().createStopOrder(Order.Action.SELL, self.getInstrument(), stopPrice, self.getQuantity())
        elif limitPrice != None and stopPrice != None:
            ret = self.getStrategy().getBroker().createStopLimitOrder(Order.Action.SELL, self.getInstrument(), stopPrice, limitPrice, self.getQuantity())
        else:
            assert(False)

        return ret

    def buildExitOnSessionCloseOrder(self):
        ret = self.getStrategy().getBroker().createMarketOrder(Order.Action.SELL, self.getInstrument(), self.getQuantity(), True)
        ret.setGoodTillCanceled(True) # Mark the exit order as GTC since we want to exit ASAP and avoid this order to get canceled.
        return ret

    def isLong(self):
        return True

# This class is reponsible for order management in short positions.
class ShortPosition(Position):
    def __init__(self, strategy, instrument, limitPrice, stopPrice, quantity, goodTillCanceled):
        if limitPrice == None and stopPrice == None:
            entryOrder = strategy.getBroker().createMarketOrder(Order.Action.SELL_SHORT, instrument, quantity, False)
        elif limitPrice != None and stopPrice == None:
            entryOrder = strategy.getBroker().createLimitOrder(Order.Action.SELL_SHORT, instrument, limitPrice, quantity)
        elif limitPrice == None and stopPrice != None:
            entryOrder = strategy.getBroker().createStopOrder(Order.Action.SELL_SHORT, instrument, stopPrice, quantity)
        elif limitPrice != None and stopPrice != None:
            entryOrder = strategy.getBroker().createStopLimitOrder(Order.Action.SELL_SHORT, instrument, stopPrice, limitPrice, quantity)
        else:
            assert(False)

        Position.__init__(self, strategy, entryOrder, goodTillCanceled)
        strategy.getBroker().placeOrder(entryOrder)

    def __getPosTracker(self):
        ret = returns.PositionTracker()
        entryExecInfo = self.getEntryOrder().getExecutionInfo()
        exitExecInfo = self.getExitOrder().getExecutionInfo()
        ret.sell(entryExecInfo.getQuantity(), entryExecInfo.getPrice(), entryExecInfo.getCommission())
        ret.buy(exitExecInfo.getQuantity(), exitExecInfo.getPrice(), exitExecInfo.getCommission())
        return ret

    def getReturnImpl(self, includeCommissions):
        return self.__getPosTracker().getReturn(self.getExitOrder().getExecutionInfo().getPrice(), includeCommissions)

    def getNetProfitImpl(self, includeCommissions):
        return self.__getPosTracker().getNetProfit(self.getExitOrder().getExecutionInfo().getPrice(), includeCommissions)

    def buildExitOrder(self, limitPrice, stopPrice):
        if limitPrice == None and stopPrice == None:
            ret = self.getStrategy().getBroker().createMarketOrder(Order.Action.BUY_TO_COVER, self.getInstrument(), self.getQuantity(), False)
        elif limitPrice != None and stopPrice == None:
            ret = self.getStrategy().getBroker().createLimitOrder(Order.Action.BUY_TO_COVER, self.getInstrument(), limitPrice, self.getQuantity())
        elif limitPrice == None and stopPrice != None:
            ret = self.getStrategy().getBroker().createStopOrder(Order.Action.BUY_TO_COVER, self.getInstrument(), stopPrice, self.getQuantity())
        elif limitPrice != None and stopPrice != None:
            ret = self.getStrategy().getBroker().createStopLimitOrder(Order.Action.BUY_TO_COVER, self.getInstrument(), stopPrice, limitPrice, self.getQuantity())
        else:
            assert(False)

        return ret

    def buildExitOnSessionCloseOrder(self):
        ret = self.getStrategy().getBroker().createMarketOrder(Order.Action.BUY_TO_COVER, self.getInstrument(), self.getQuantity(), True)
        ret.setGoodTillCanceled(True) # Mark the exit order as GTC since we want to exit ASAP and avoid this order to get canceled.
        return ret

    def isLong(self):
        return False
