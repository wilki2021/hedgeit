'''
Created on Apr 16, 2013

@author: rtw
'''
import unittest
from hedgeit.broker.orders import Order
from hedgeit.broker.brokers import BacktestingBroker
from hedgeit.feeds.multifeed import MultiFeed
from hedgeit.feeds.feed import Feed
from hedgeit.feeds.instrument import Instrument
import os
import datetime

class Test(unittest.TestCase):


    def setUp(self):
        datafile = '%s/data/AC___CCB-10d.csv' % os.path.dirname(__file__)
        self._feed = Feed(Instrument('AC',datafile))
        

    def tearDown(self):
        pass

    ###########################################################################
    ## Test a basic long market entry order
    
    def on_bars_1(self,bars):
        if not self._placed_markorder:
            o = self._broker.createMarketOrder(Order.Action.BUY, 'AC', 100, False)
            self._broker.placeOrder(o)
            self._placed_markorder = True
        else:
            # we expect by the next Bar that we own the 100 units of AC
            self.assertEqual(self._broker.getPositions()['AC'], 100) 
            
    def on_order_update_1(self, broker, order):
        # 2.215 is open price on day 2 - we expect to execute there
        self.assertEqual(order.getExecutionInfo().getPrice(),2.215)
        
    def testMarketOrder(self):
        self._placed_markorder = False
        mf = MultiFeed()
        mf.register_feed(self._feed)
        self._broker = BacktestingBroker(10000, mf)
        mf.subscribe(self.on_bars_1)
        self._broker.getOrderUpdatedEvent().subscribe(self.on_order_update_1)
        mf.start()

    ###########################################################################
    ## Test a long limit entry order

    def on_bars_2(self,bars):
        if not self._placed_lo:
            self._lo = self._broker.createLimitOrder(Order.Action.BUY, 'AC', 2.210, 100)
            self._lo.setGoodTillCanceled(True)
            self._broker.placeOrder(self._lo)
            self._placed_lo = True
        else:
            if self._lo.getState() == Order.State.FILLED:
                # when the order is filled we should have 100 units of AC
                self.assertEqual(self._broker.getPositions()['AC'], 100) 
            
    def on_order_update_2(self, broker, order):
        # our limit should trigger on 1/25 because the low goes to 2.205
        self.assertEqual(order.getExecutionInfo().getPrice(),2.210)
        self.assertEqual(order.getExecutionInfo().getDateTime(),datetime.datetime(2012,1,25,0,0))
        
    def testLimitOrder(self):
        self._placed_lo = False
        mf = MultiFeed()
        mf.register_feed(self._feed)
        self._broker = BacktestingBroker(10000, mf)
        mf.subscribe(self.on_bars_2)
        self._broker.getOrderUpdatedEvent().subscribe(self.on_order_update_2)
        mf.start()

    ###########################################################################
    ## Test a short market entry order

    def on_bars_3(self,bars):
        if not self._placed_smo:
            o = self._broker.createMarketOrder(Order.Action.SELL_SHORT, 'AC', 100, False)
            self._broker.placeOrder(o)
            self._placed_smo = True
        else:
            # we expect by the next Bar that we own the 100 units of AC
            self.assertEqual(self._broker.getPositions()['AC'], -100) 
            
    def on_order_update_3(self, broker, order):
        # 2.215 is open price on day 2 - we expect to execute there
        self.assertEqual(order.getExecutionInfo().getPrice(),2.215)
        
    def testMarketOrderShort(self):
        self._placed_smo = False
        mf = MultiFeed()
        mf.register_feed(self._feed)
        self._broker = BacktestingBroker(10000, mf)
        mf.subscribe(self.on_bars_3)
        self._broker.getOrderUpdatedEvent().subscribe(self.on_order_update_3)
        mf.start()

    ###########################################################################
    ## Test a stop-loss exit from a market entry long

    def on_bars_4(self,bars):
        if not self._placed_markorder:
            o = self._broker.createMarketOrder(Order.Action.BUY, 'AC', 100, False)
            self._broker.placeOrder(o)
            self._placed_markorder = True
            # now we also need to place our stop-loss
            o1 = self._broker.createStopOrder(Order.Action.SELL, 'AC', 2.2075, 100)
            o1.setGoodTillCanceled(True)
            self._broker.placeOrder(o1)
            
    def on_order_update_4(self, broker, order):
        # 2.215 is open price on day 2 - we expect to execute there
        if order.getType() == Order.Type.MARKET:
            self.assertEqual(order.getExecutionInfo().getPrice(),2.215)
            self.assertEqual(self._broker.getPositions()['AC'], 100) 
        elif order.getType() == Order.Type.STOP:
            self.assertEqual(order.getExecutionInfo().getPrice(),2.2075)
            self.assertEqual(self._broker.getPositions()['AC'], 0) 
        else:
            self.assertTrue(False)
        
    def testMarketOrderStopLimit(self):
        self._placed_markorder = False
        mf = MultiFeed()
        mf.register_feed(self._feed)
        self._broker = BacktestingBroker(10000, mf)
        mf.subscribe(self.on_bars_4)
        self._broker.getOrderUpdatedEvent().subscribe(self.on_order_update_4)
        mf.start()

    ###########################################################################
    ## Test a stop-loss exit from a market entry short

    def on_bars_5(self,bars):
        if not self._placed_markorder:
            o = self._broker.createMarketOrder(Order.Action.SELL_SHORT, 'AC', 100, False)
            self._broker.placeOrder(o)
            self._placed_markorder = True
            # now we also need to place our stop-loss
            o1 = self._broker.createStopOrder(Order.Action.BUY_TO_COVER, 'AC', 2.265, 100)
            o1.setGoodTillCanceled(True)
            self._broker.placeOrder(o1)
            
    def on_order_update_5(self, broker, order):
        # 2.215 is open price on day 2 - we expect to execute there
        if order.getType() == Order.Type.MARKET:
            self.assertEqual(order.getExecutionInfo().getPrice(),2.215)
            self.assertEqual(self._broker.getPositions()['AC'], -100) 
        elif order.getType() == Order.Type.STOP:
            # this scenario gaps up on day stop hit so price is open price, not stop price
            self.assertEqual(order.getExecutionInfo().getPrice(),2.275)
            self.assertEqual(self._broker.getPositions()['AC'], 0) 
        else:
            self.assertTrue(False)
        
    def testMarketOrderShortStopLimit(self):
        self._placed_markorder = False
        mf = MultiFeed()
        mf.register_feed(self._feed)
        self._broker = BacktestingBroker(10000, mf)
        mf.subscribe(self.on_bars_5)
        self._broker.getOrderUpdatedEvent().subscribe(self.on_order_update_5)
        mf.start()

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()