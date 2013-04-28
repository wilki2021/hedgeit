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

######################################################################
## Orders
## http://stocks.about.com/od/tradingbasics/a/markords.htm
## http://www.interactivebrokers.com/en/software/tws/usersguidebook/ordertypes/basic_order_types.htm

class Order:
    """Base class for orders. 

    :param type_: The order type
    :type type_: :class:`Order.Type`
    :param action: The order action.
    :type action: :class:`Order.Action`
    :param instrument: Instrument identifier.
    :type instrument: string.
    :param quantity: Order quantity.
    :type quantity: int.

    .. note::

        Valid **action** parameter values are:

         * Order.Action.BUY
         * Order.Action.BUY_TO_COVER
         * Order.Action.SELL
         * Order.Action.SELL_SHORT

        This is a base class and should not be used directly.
    """

    class Action:
        BUY             = 1
        BUY_TO_COVER    = 2
        SELL            = 3
        SELL_SHORT      = 4

        action_strs = [
            '',
            'BUY',
            'BUY_TO_COVER',
            'SELL',
            'SELL_SHORT'        
            ]
    
    class State:
        ACCEPTED        = 1
        CANCELED        = 2
        FILLED          = 3

        state_strs = [
            '',
            'ACCEPTED',
            'CANCELED',
            'FILLED'
            ]
    
    class Type:
        MARKET          = 1
        LIMIT           = 2
        STOP            = 3
        STOP_LIMIT      = 4

        type_strs = [
            '',
            'MARKET',
            'LIMIT',
            'STOP',
            'STOP_LIMIT'
            ]
    
    def __init__(self, type_, action, instrument, quantity):
        self.__type = type_
        self.__action = action
        self.__instrument = instrument
        self.__quantity = quantity
        self.__executionInfo = None
        self.__goodTillCanceled = False
        self.__allOrNone = True
        self.__state = Order.State.ACCEPTED
        self.__dirty = False

    def isDirty(self):
        return self.__dirty

    def setDirty(self, dirty):
        self.__dirty = dirty

    def getType(self):
        """Returns the order type"""
        return self.__type

    def getAction(self):
        """Returns the order action."""
        return self.__action

    def getState(self):
        """Returns the order state.

        Valid order states are:
         * Order.State.ACCEPTED (the initial state).
         * Order.State.CANCELED
         * Order.State.FILLED
        """
        return self.__state

    def isAccepted(self):
        """Returns True if the order state is Order.State.ACCEPTED."""
        return self.__state == Order.State.ACCEPTED

    def isCanceled(self):
        """Returns True if the order state is Order.State.CANCELED."""
        return self.__state == Order.State.CANCELED

    def isFilled(self):
        """Returns True if the order state is Order.State.FILLED."""
        return self.__state == Order.State.FILLED

    def getInstrument(self):
        """Returns the instrument identifier."""
        return self.__instrument

    def getQuantity(self):
        """Returns the quantity."""
        return self.__quantity

    def setQuantity(self, quantity):
        """Updates the quantity."""
        self.__quantity = quantity
        self.setDirty(True)

    def getGoodTillCanceled(self):
        """Returns True if the order is good till canceled."""
        return self.__goodTillCanceled

    def setGoodTillCanceled(self, goodTillCanceled):
        """Sets if the order should be good till canceled.
        Orders that are not filled by the time the session closes will be will be automatically canceled
        if they were not set as good till canceled

        :param goodTillCanceled: True if the order should be good till canceled.
        :type goodTillCanceled: boolean.
        """
        self.__goodTillCanceled = goodTillCanceled
        self.setDirty(True)

    def getAllOrNone(self):
        """Returns True if the order should be completely filled or else canceled."""
        return self.__allOrNone

    def setAllOrNone(self, allOrNone):
        """Sets the All-Or-None property for this order.

        :param allOrNone: True if the order should be completely filled or else canceled.
        :type allOrNone: boolean.
        """
        self.__allOrNone = allOrNone
        self.setDirty(True)

    def setExecuted(self, orderExecutionInfo):
        self.__executionInfo = orderExecutionInfo
        self.__state = Order.State.FILLED

    def setState(self, state):
        self.__state = state

    def getExecutionInfo(self):
        """Returns the order execution info if the order was filled, or None otherwise.

        :rtype: :class:`OrderExecutionInfo`.
        """
        return self.__executionInfo
    
    def __str__(self):
        str_ = 'Order(type:%s,action:%s,symbol:%s,quantity:%d,gtc:%s,allOrNone:%s,state:%s)' %\
            (Order.Type.type_strs[self.__type],
             Order.Action.action_strs[self.__action],
             self.__instrument,
             self.__quantity,
             self.__goodTillCanceled,
             self.__allOrNone,
             Order.State.state_strs[self.__state])
        return str_
    
class MarketOrder(Order):
    """Base class for market orders.

    .. note::

        This is a base class and should not be used directly.
    """

    def __init__(self, action, instrument, quantity, onClose):
        Order.__init__(self, Order.Type.MARKET, action, instrument, quantity)
        self.__onClose = onClose

    def getFillOnClose(self):
        """Returns True if the order should be filled as close to the closing price as possible (Market-On-Close order)."""
        return self.__onClose

    def setFillOnClose(self, onClose):
        """Sets if the order should be filled as close to the closing price as possible (Market-On-Close order)."""
        self.__onClose = onClose
        self.setDirty(True)

    def __str__(self):
        str_ = Order.__str__(self)
        str_ = str_[:-1] + ',onClose:%s' % self.__onClose + ')'
        return str_

class LimitOrder(Order):
    """Base class for limit orders.

    .. note::

        This is a base class and should not be used directly.
    """

    def __init__(self, action, instrument, limitPrice, quantity):
        Order.__init__(self, Order.Type.LIMIT, action, instrument, quantity)
        self.__limitPrice = limitPrice

    def getLimitPrice(self):
        """Returns the limit price."""
        return self.__limitPrice

    def setLimitPrice(self, limitPrice):
        """Updates the limit price."""
        self.__limitPrice = limitPrice
        self.setDirty(True)

    def __str__(self):
        str_ = Order.__str__(self)
        str_ = str_[:-1] + ',limit:%0.3f' % self.__limitPrice + ')'
        return str_

class StopOrder(Order):
    """Base class for stop orders.

    .. note::

        This is a base class and should not be used directly.
    """

    def __init__(self, action, instrument, stopPrice, quantity):
        Order.__init__(self, Order.Type.STOP, action, instrument, quantity)
        self.__stopPrice = stopPrice

    def getStopPrice(self):
        """Returns the stop price."""
        return self.__stopPrice

    def setStopPrice(self, stopPrice):
        """Updates the stop price."""
        self.__stopPrice = stopPrice
        self.setDirty(True)

    def __str__(self):
        str_ = Order.__str__(self)
        str_ = str_[:-1] + ',stop:%0.3f' % self.__stopPrice + ')'
        return str_

class StopLimitOrder(Order):
    """Base class for stop limit orders.

    .. note::

        This is a base class and should not be used directly.
    """

    def __init__(self, action, instrument, limitPrice, stopPrice, quantity):
        Order.__init__(self, Order.Type.STOP_LIMIT, action, instrument, quantity)
        self.__limitPrice = limitPrice
        self.__stopPrice = stopPrice
        self.__limitOrderActive = False # Set to true when the limit order is activated (stop price is hit)
        
    def getLimitPrice(self):
        """Returns the limit price."""
        return self.__limitPrice

    def setLimitPrice(self, limitPrice):
        """Updates the limit price."""
        self.__limitPrice = limitPrice
        self.setDirty(True)

    def getStopPrice(self):
        """Returns the stop price."""
        return self.__stopPrice

    def setStopPrice(self, stopPrice):
        """Updates the stop price."""
        self.__stopPrice = stopPrice
        self.setDirty(True)

    def setLimitOrderActive(self, limitOrderActive):
        self.__limitOrderActive = limitOrderActive

    def isLimitOrderActive(self):
        """Returns True if the limit order is active."""
        return self.__limitOrderActive

    def __str__(self):
        str_ = Order.__str__(self)
        str_ = str_[:-1] + ',stop:%0.3f,limit:%0.3f' % (self.__stopPrice,self.__limitPrice) + ')'
        return str_

class OrderExecutionInfo:
    """Execution information for a filled order."""
    def __init__(self, price, quantity, commission, dateTime):
        self.__price = price
        self.__quantity = quantity
        self.__commission = commission
        self.__dateTime = dateTime

    def getPrice(self):
        """Returns the fill price."""
        return self.__price

    def getQuantity(self):
        """Returns the quantity."""
        return self.__quantity

    def getCommission(self):
        """Returns the commission applied."""
        return self.__commission

    def getDateTime(self):
        """Returns the :class:`datatime.datetime` when the order was executed."""
        return self.__dateTime
    
    def __str__(self):        
        str_ = 'OrderExecution(price:%0.3f,quantity:%d,commission:%s,datetime:%s)' %\
            (self.__price,
             self.__quantity,
             self.__commission,
             self.__dateTime)
        return str_
