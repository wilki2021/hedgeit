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
## Order filling strategies
from orders import Order

class FillStrategy:
    """Base class for order filling strategies."""

    # Return the fill price for a MarketOrder or None.
    def fillMarketOrder(self, order, broker_, bar):
        """Override to return the fill price for a market order or None if the order can't be filled at the given time.

        :param order: The order.
        :type order: :class:`pyalgotrade.broker.MarketOrder`.
        :param broker_: The broker.
        :type broker_: :class:`Broker`.
        :param bar: The current bar.
        :type bar: :class:`pyalgotrade.bar.Bar`.
        :rtype: An int/float with the fill price or None if the order should not be filled.
        """
        raise NotImplementedError()

    # Return the fill price for a LimitOrder or None.
    def fillLimitOrder(self, order, broker_, bar):
        """Override to return the fill price for a limit order or None if the order can't be filled at the given time.

        :param order: The order.
        :type order: :class:`pyalgotrade.broker.LimitOrder`.
        :param broker_: The broker.
        :type broker_: :class:`Broker`.
        :param bar: The current bar.
        :type bar: :class:`pyalgotrade.bar.Bar`.
        :rtype: An int/float with the fill price or None if the order should not be filled.
        """
        raise NotImplementedError()

    # Return the fill price for a StopOrder or None.
    def fillStopOrder(self, order, broker_, bar):
        """Override to return the fill price for a stop order or None if the order can't be filled at the given time.

        :param order: The order.
        :type order: :class:`pyalgotrade.broker.StopOrder`.
        :param broker_: The broker.
        :type broker_: :class:`Broker`.
        :param bar: The current bar.
        :type bar: :class:`pyalgotrade.bar.Bar`.
        :rtype: An int/float with the fill price or None if the order should not be filled.
        """
        raise NotImplementedError()

    # Return the fill price for a StopLimitOrder or None.
    def fillStopLimitOrder(self, order, broker_, bar, justHitStopPrice):
        """Override to return the fill price for a stop limit order or None if the order can't be filled at the given time.

        :param order: The order.
        :type order: :class:`pyalgotrade.broker.StopLimitOrder`.
        :param broker_: The broker.
        :type broker_: :class:`Broker`.
        :param bar: The current bar.
        :type bar: :class:`pyalgotrade.bar.Bar`.
        :param justHitStopPrice: True if the stop price has just been hit with the current bar.
        :type justHitStopPrice: boolean.
        :rtype: An int/float with the fill price or None if the order should not be filled.
        """
        raise NotImplementedError()

class DefaultStrategy(FillStrategy):
    """
    This strategy works as follows:

    * A :class:`pyalgotrade.broker.MarketOrder` is always filled using the open/close price.
    * A :class:`pyalgotrade.broker.LimitOrder` will be filled like this:
        * If the limit price was penetrated with the open price, then the open price is used.
        * If the bar includes the limit price, then the limit price is used.
        * Note that when buying the price is penetrated if it gets <= the limit price, and when selling the price is penetrated if it gets >= the limit price
    * A :class:`pyalgotrade.broker.StopOrder` will be filled like this:
        * If the stop price was penetrated with the open price, then the open price is used.
        * If the bar includes the stop price, then the stop price is used.
        * Note that when buying the price is penetrated if it gets >= the stop price, and when selling the price is penetrated if it gets <= the stop price
    * A :class:`pyalgotrade.broker.StopLimitOrder` will be filled like this:
        * If the stop price was penetrated with the open price, or if the bar includes the stop price, then the limit order becomes active.
        * If the limit order is active:
            * If the limit order was activated in this same bar and the limit price is penetrated as well, then the best between the stop price and the limit fill price (as described earlier) is used.
            * If the limit order was activated at a previous bar then the limit fill price (as described earlier) is used.

    .. note::
        This is the default strategy used by the Broker.
    """
    def __getLimitOrderFillPrice(self, broker_, bar_, action, limitPrice):
        ret = None
        open_ = broker_.getBarOpen(bar_)
        high = broker_.getBarHigh(bar_)
        low = broker_.getBarLow(bar_)

        # If the bar is below the limit price, use the open price.
        # If the bar includes the limit price, use the open price or the limit price.
        if action in [Order.Action.BUY, Order.Action.BUY_TO_COVER]:
            if high < limitPrice:
                ret = open_
            elif limitPrice >= low:
                if open_ < limitPrice: # The limit price was penetrated on open.
                    ret = open_
                else:
                    ret = limitPrice
        # If the bar is above the limit price, use the open price.
        # If the bar includes the limit price, use the open price or the limit price.
        elif action in [Order.Action.SELL, Order.Action.SELL_SHORT]:
            if low > limitPrice:
                ret = open_
            elif limitPrice <= high:
                if open_ > limitPrice: # The limit price was penetrated on open.
                    ret = open_
                else:
                    ret = limitPrice
        else: # Unknown action
            assert(False)
        return ret

    def fillMarketOrder(self, order, broker_, bar):
        if order.getFillOnClose():
            ret = broker_.getBarClose(bar)
        else:
            ret = broker_.getBarOpen(bar)
        return ret

    # Return the fill price for a LimitOrder or None.
    def fillLimitOrder(self, order, broker_, bar):
        return self.__getLimitOrderFillPrice(broker_, bar, order.getAction(), order.getLimitPrice())

    # Return the fill price for a StopOrder or None.
    def fillStopOrder(self, order, broker_, bar):
        ret = None
        open_ = broker_.getBarOpen(bar)
        high = broker_.getBarHigh(bar)
        low = broker_.getBarLow(bar)
        stopPrice = order.getStopPrice()

        # If the bar is above the stop price, use the open price.
        # If the bar includes the stop price, use the open price or the stop price. Whichever is better.
        if order.getAction() in [Order.Action.BUY, Order.Action.BUY_TO_COVER]:
            if low > stopPrice:
                ret = open_
            elif stopPrice <= high:
                if open_ > stopPrice: # The stop price was penetrated on open.
                    ret = open_
                else:
                    ret = stopPrice
        # If the bar is below the stop price, use the open price.
        # If the bar includes the stop price, use the open price or the stop price. Whichever is better.
        elif order.getAction() in [Order.Action.SELL, Order.Action.SELL_SHORT]:
            if high < stopPrice:
                ret = open_
            elif stopPrice >= low:
                if open_ < stopPrice: # The stop price was penetrated on open.
                    ret = open_
                else:
                    ret = stopPrice
        else: # Unknown action
            assert(False)
        return ret

    # Return the fill price for a StopLimitOrder or None.
    def fillStopLimitOrder(self, order, broker_, bar, justHitStopPrice):
        ret = self.__getLimitOrderFillPrice(broker_, bar, order.getAction(), order.getLimitPrice())
        # If we just hit the stop price, we need to make additional checks.
        if ret != None and justHitStopPrice:
            if order.getAction() in [Order.Action.BUY, Order.Action.BUY_TO_COVER]:
                # If the stop price is lower than the limit price, then use that one. Else use the limit price.
                ret = min(order.getStopPrice(), order.getLimitPrice())
            elif order.getAction() in [Order.Action.SELL, Order.Action.SELL_SHORT]:
                # If the stop price is greater than the limit price, then use that one. Else use the limit price.
                ret = max(order.getStopPrice(), order.getLimitPrice())
            else: # Unknown action
                assert(False)
        return ret