'''
hedgeit.strategy.strategy

Contains:
  class Strategy
'''
        
import hedgeit.common.observer as observer
from hedgeit.broker.brokers import BacktestingBroker
from positions import LongPosition,ShortPosition
      
class Strategy(object):
    """Base class for strategies. 

    :param barFeed: The bar feed to use to backtest the strategy.
    :type barFeed: :class:`pyalgotrade.barfeed.BarFeed`.
    :param cash: The amount of cash available.
    :type cash: int/float.
    :param broker_: Broker to use. If not specified the default backtesting broker (:class:`pyalgotrade.broker.backtesting.Broker`) 
                    will be used.
    :type broker_: :class:`pyalgotrade.broker.Broker`.

    .. note::
        This is a base class and should not be used directly.
    """

    def __init__(self, barFeed, cash = 1000000, broker_ = None):
        self.__feed = barFeed
        self.__activePositions = {}
        self.__orderToPosition = {}
        self.__barsProcessedEvent = observer.Event()
        self.__orderUpdatedEvent = observer.Event()
        self.__analyzers = []
        self.__namedAnalyzers = {}

        if broker_ == None:
            # When doing backtesting (broker_ == None), the broker should subscribe to barFeed events before the strategy.
            # This is to avoid executing orders placed in the current tick.
            self.__broker = BacktestingBroker(cash, barFeed)
        else:
            self.__broker = broker_
        self.__broker.getOrderUpdatedEvent().subscribe(self.__onOrderUpdate)
        # very important that this happens after the broker subscribes to the feed
        self.__feed.subscribe(self.__onBars)

    def getResult(self):
        return self.getBroker().getEquity()

    def getBarsProcessedEvent(self):
        return self.__barsProcessedEvent

    def getOrderUpdatedEvent(self):
        return self.__orderUpdatedEvent

    def __registerOrder(self, position, order):
        try:
            orders = self.__activePositions[position]
        except KeyError:
            orders = set()
            self.__activePositions[position] = orders

        if order.isAccepted():
            self.__orderToPosition[order] = position
            orders.add(order)

    def __unregisterOrder(self, position, order):
        del self.__orderToPosition[order]

        orders = self.__activePositions[position]
        orders.remove(order)
        if len(orders) == 0:
            del self.__activePositions[position]

    def __registerActivePosition(self, position):
        for order in [position.getEntryOrder(), position.getExitOrder()]:
            if order and order.isAccepted():
                self.__registerOrder(position, order)

    def __notifyAnalyzers(self, lambdaExpression):
        for s in self.__analyzers:
            lambdaExpression(s)

    def attachAnalyzerEx(self, strategyAnalyzer, name = None):
        if strategyAnalyzer not in self.__analyzers:
            if name != None:
                if name in self.__namedAnalyzers:
                    raise Exception("A different analyzer named '%s' was already attached" % name)
                self.__namedAnalyzers[name] = strategyAnalyzer

            strategyAnalyzer.beforeAttach(self)
            self.__analyzers.append(strategyAnalyzer)
            strategyAnalyzer.attached(self)

    def attachAnalyzer(self, strategyAnalyzer):
        """Adds a :class:`pyalgotrade.stratanalyzer.StrategyAnalyzer`."""
        self.attachAnalyzerEx(strategyAnalyzer)

    def getNamedAnalyzer(self, name):
        return self.__namedAnalyzers.get(name, None)

    def getFeed(self):
        """Returns the :class:`pyalgotrade.barfeed.BarFeed` that this strategy is using."""
        return self.__feed

    def getCurrentDateTime(self):
        """Returns the :class:`datetime.datetime` for the current :class:`pyalgotrade.bar.Bar`."""
        ret = None
        bars = self.__feed.getCurrentBars()
        if bars:
            ret = bars.getDateTime()
        return ret

    def getBroker(self):
        """Returns the :class:`pyalgotrade.broker.Broker` used to handle order executions."""
        return self.__broker

    def enterLong(self, instrument, quantity, limit=None, stop=None, goodTillCanceled = False):
        """Generates a buy :class:`pyalgotrade.broker.MarketOrder` to enter a long position.

        :param instrument: Instrument identifier.
        :type instrument: string.
        :param quantity: Entry order quantity.
        :type quantity: int.
        :param goodTillCanceled: True if the entry order is good till canceled. If False then the order gets automatically canceled when the session closes.
        :type goodTillCanceled: boolean.
        :rtype: The :class:`Position` entered.
        """

        ret = LongPosition(self, instrument, limit, stop, quantity, goodTillCanceled)
        self.__registerActivePosition(ret)
        return ret

    def enterShort(self, instrument, quantity, limit=None, stop=None, goodTillCanceled = False):
        """Generates a sell short :class:`pyalgotrade.broker.MarketOrder` to enter a short position.

        :param instrument: Instrument identifier.
        :type instrument: string.
        :param quantity: Entry order quantity.
        :type quantity: int.
        :param goodTillCanceled: True if the entry order is good till canceled. If False then the order gets automatically canceled when the session closes.
        :type goodTillCanceled: boolean.
        :rtype: The :class:`Position` entered.
        """

        ret = ShortPosition(self, instrument, limit, stop, quantity, goodTillCanceled)
        self.__registerActivePosition(ret)
        return ret


    def exitPosition(self, position, limitPrice = None, stopPrice = None, goodTillCanceled = None):
        """Generates the exit order for the position.

        :param position: A position returned by any of the enterLongXXX or enterShortXXX methods.
        :type position: :class:`Position`.
        :param limitPrice: The limit price.
        :type limitPrice: float.
        :param stopPrice: The stop price.
        :type stopPrice: float.
        :param goodTillCanceled: True if the exit order is good till canceled. If False then the order gets automatically canceled when the session closes. If None, then it will match the entry order.
        :type goodTillCanceled: boolean.

        .. note::
            * If the entry order was not filled yet, it will be canceled.
            * If a previous exit order for this position was filled, this won't have any effect.
            * If a previous exit order for this position is pending, it will get canceled and the new exit order submitted.
            * If limitPrice is not set and stopPrice is not set, then a :class:`pyalgotrade.broker.MarketOrder` is used to exit the position.
            * If limitPrice is set and stopPrice is not set, then a :class:`pyalgotrade.broker.LimitOrder` is used to exit the position.
            * If limitPrice is not set and stopPrice is set, then a :class:`pyalgotrade.broker.StopOrder` is used to exit the position.
            * If limitPrice is set and stopPrice is set, then a :class:`pyalgotrade.broker.StopLimitOrder` is used to exit the position.
        """

        if position.exitFilled():
            return

        # TODO: Relaxing this requirement to allow for a stop-loss order to be
        # immediately entered.  If this isn't supported, then you effectively
        # miss one trading period where a stop-loss should have been active
        # To really support would need to set up some kind of dependency between
        # orders, but for now just allow it to go in:
        if True:
        # Before exiting a position, the entry order must have been filled.
        # if position.getEntryOrder().isFilled():
            position.close(limitPrice, stopPrice, goodTillCanceled)
            self.__registerActivePosition(position)
        else: # If the entry was not filled, cancel it.
            self.getBroker().cancelOrder(position.getEntryOrder())

    def onEnterOk(self, position):
        """Override (optional) to get notified when the order submitted to enter a position was filled. The default implementation is empty.

        :param position: A position returned by any of the enterLongXXX or enterShortXXX methods.
        :type position: :class:`Position`.
        """
        pass

    def onEnterCanceled(self, position):
        """Override (optional) to get notified when the order submitted to enter a position was canceled. The default implementation is empty.

        :param position: A position returned by any of the enterLongXXX or enterShortXXX methods.
        :type position: :class:`Position`.
        """
        pass

    # Called when the exit order for a position was filled.
    def onExitOk(self, position):
        """Override (optional) to get notified when the order submitted to exit a position was filled. The default implementation is empty.

        :param position: A position returned by any of the enterLongXXX or enterShortXXX methods.
        :type position: :class:`Position`.
        """
        pass

    # Called when the exit order for a position was canceled.
    def onExitCanceled(self, position):
        """Override (optional) to get notified when the order submitted to exit a position was canceled. The default implementation is empty.

        :param position: A position returned by any of the enterLongXXX or enterShortXXX methods.
        :type position: :class:`Position`.
        """
        pass

    """Base class for strategies. """
    def onStart(self):
        """Override (optional) to get notified when the strategy starts executing. The default implementation is empty. """
        pass

    def onFinish(self, bars):
        """Override (optional) to get notified when the strategy finished executing. The default implementation is empty.

        :param bars: The last bars processed.
        :type bars: :class:`pyalgotrade.bar.Bars`.
        """
        pass

    def onBars(self, bars):
        '''
        Override (**mandatory**) to get notified when new bars are available. 
        The default implementation raises an Exception.
        
        onBars is where the user will typically implement the main bulk of
        the strategy.  bars is a :class:`hedgeit.feeds.bars` instance.
        The framework ensures that the bars are for the same period to handle 
        the case where data series may have different stop/start dates.  
        '''
        raise NotImplementedError()

    def onOrderUpdated(self, order):
        """Override (optional) to get notified when an order gets updated. This is only called if the order was placed using the broker interface directly.

        :param order: The order updated.
        :type order: :class:`pyalgotrade.broker.Order`.
        """
        pass

    def __onOrderUpdate(self, broker_, order):
        position = self.__orderToPosition.get(order, None)
        if position == None:
            self.onOrderUpdated(order)
        elif position.getEntryOrder() == order:
            if order.isFilled():
                self.onEnterOk(position)
            elif order.isCanceled():
                self.__unregisterOrder(position, order)
                self.onEnterCanceled(position)
            else:
                assert(False)
        elif position.getExitOrder() == order:
            if order.isFilled():
                self.__unregisterOrder(position, order)
                self.onExitOk(position)
            elif order.isCanceled():
                self.__unregisterOrder(position, order)
                self.onExitCanceled(position)
            else:
                assert(False)
        else:
            # The order used to belong to a position but it was ovewritten with a new one
            # and the previous order should have been canceled.
            assert(order.isCanceled())
            
        # we only want to emit an event if this order was for one of our positions             
        if position != None:
            self.__orderUpdatedEvent.emit( broker_, order)

    def __checkExitOnSessionClose(self, bars):
        for position in self.__activePositions.keys():
            order = position.checkExitOnSessionClose(bars)
            if order:
                self.__registerOrder(position, order)

    def __onBars(self, bars):
        # THE ORDER HERE IS VERY IMPORTANT

        self.__notifyAnalyzers(lambda s: s.beforeOnBars(self))

        # 1: Let the strategy process current bars and place orders.
        self.onBars(bars)

        # 2: Place the necessary orders for positions marked to exit on session close.
        self.__checkExitOnSessionClose(bars)

        # 3: Notify that the bars were processed.
        self.__barsProcessedEvent.emit(self, bars)
