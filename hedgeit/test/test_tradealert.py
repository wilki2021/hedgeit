'''
Created on Apr 17, 2013

@author: rtw
'''
import unittest

from hedgeit.feeds.feed import Feed
from hedgeit.feeds.db import InstrumentDb
from hedgeit.feeds.multifeed import MultiFeed
from hedgeit.analyzer import returns
from hedgeit.analyzer import drawdown
from hedgeit.analyzer import sharpe
from hedgeit.analyzer import trades
from hedgeit.strategy.clenow import ClenowBreakoutStrategy
from hedgeit.control.clenow import ClenowController
from hedgeit.broker.orders import Order
import datetime
import test_util

import os

class Test(unittest.TestCase):


    def setUp(self):
        # we are using a special data set that triggers a trade on the last bar
        manifest = '%s/data/manifest2.csv' % os.path.dirname(__file__)        
        self._db = InstrumentDb.Instance()
        self._db.load(manifest)
        
    def setupFeed(self, barFeed):
        barFeed.register_feed(Feed(self._db.get('RR')))

    def tearDown(self):
        pass


    def testNewTradeAlert(self):
        mf = MultiFeed()
        self.setupFeed(mf)
        strat = ClenowBreakoutStrategy(mf,tradeStart=datetime.datetime(2012,8,11))
        
        # Attach a few analyzers to the strategy before executing it.
        retAnalyzer = returns.Returns()
        strat.attachAnalyzer(retAnalyzer)
        sharpeRatioAnalyzer = sharpe.SharpeRatio()
        strat.attachAnalyzer(sharpeRatioAnalyzer)
        drawDownAnalyzer = drawdown.DrawDown()
        strat.attachAnalyzer(drawDownAnalyzer)
        tradesAnalyzer = trades.Trades()
        strat.attachAnalyzer(tradesAnalyzer)
        
        mf.start()
        strat.exitPositions()
        
        # check new trades
        self.assertEqual(len(strat.getPositions()),1)
        self.assertTrue(strat.getPositions().has_key('RR'))
        self.assertEqual(strat.getPositions()['RR'].getQuantity(),4)
        self.assertEqual(strat.getPositions()['RR'].getEntryOrder().getAction(),Order.Action.SELL_SHORT)
        alerts = strat.tradeAlerts()
        self.assertEqual(len(alerts),1)
        order = alerts[0][0]
        self.assertEqual(order.getInstrument(), 'RR')
        self.assertEqual(order.getQuantity(),4)
        self.assertEqual(order.getAction(),Order.Action.SELL_SHORT)
        self.assertAlmostEqual(alerts[0][1], 0.0019, places=4)
        
        tlog = '%s/trade6.log' % os.path.dirname(__file__)
        tradesAnalyzer.writeTradeLog(tlog)
        
        self.assertAlmostEqual(strat.getResult(),995993.20,places=2)
        self.assertEqual(tradesAnalyzer.getCount(),1)
        self.assertEqual(tradesAnalyzer.getProfitableCount(),0)
        self.assertEqual(tradesAnalyzer.getUnprofitableCount(),1)
        
        self.assertTrue(test_util.file_compare('%s/trade6.reflog' % os.path.dirname(__file__), tlog))
        os.system('rm %s' % tlog)

    def testControllerTradeAlerts(self):
        plog = '%s/positions.csv' % os.path.dirname(__file__)
        elog = '%s/equity.csv' % os.path.dirname(__file__)
        rlog = '%s/returns.csv' % os.path.dirname(__file__)
        slog = '%s/summary.csv' % os.path.dirname(__file__)

        ctrl = ClenowController({ 'Ag-1' : ['RR'] }, plog, elog, rlog, summaryFile=slog)
        ctrl.run(datetime.datetime(2011,12,31),datetime.datetime(2012,8,1),datetime.datetime(2013,12,31))

        tlog = '%s/tradealert.log' % os.path.dirname(__file__)
        ctrl.writeTradeAlerts(tlog)
        
        self.assertTrue(test_util.file_compare('%s/tradealert.reflog' % os.path.dirname(__file__), tlog))
        os.system('rm %s' % tlog)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testBasic']
    unittest.main()