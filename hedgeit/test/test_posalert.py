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

    def testControllerPosAlerts(self):
        plog = '%s/positions.csv' % os.path.dirname(__file__)
        elog = '%s/equity.csv' % os.path.dirname(__file__)
        rlog = '%s/returns.csv' % os.path.dirname(__file__)
        slog = '%s/summary.csv' % os.path.dirname(__file__)

        ctrl = ClenowController({ 'Ag-1' : ['RR'] }, plog, elog, rlog, summaryFile=slog)
        ctrl.run(datetime.datetime(2011,12,31),datetime.datetime(2012,8,1),datetime.datetime(2013,12,31))

        tlog = '%s/posalert.log' % os.path.dirname(__file__)
        ctrl.writePositionAlerts(tlog)

        self.assertTrue(test_util.file_compare('%s/posalert.reflog' % os.path.dirname(__file__), tlog))
        os.remove(tlog)

        tlog = '%s/trade7.log' % os.path.dirname(__file__)
        ctrl.writeAllTrades(tlog)
        
        self.assertTrue(test_util.file_compare('%s/trade7.reflog' % os.path.dirname(__file__), tlog))
        os.remove(tlog)
        
        tlog = '%s/tssb' % os.path.dirname(__file__)
        ctrl.writeTSSBTrades(tlog)

        self.assertTrue(test_util.file_compare('%s_long.reflog' % tlog, '%s_long.csv' % tlog))
        self.assertTrue(test_util.file_compare('%s_short.reflog' % tlog, '%s_short.csv' % tlog))
        os.remove('%s_long.csv' % tlog)
        os.remove('%s_short.csv' % tlog)
        os.remove(plog)
        os.remove(elog)
        os.remove(rlog)
        os.remove(slog)
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testBasic']
    unittest.main()