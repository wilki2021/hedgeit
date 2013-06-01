'''
Created on Apr 17, 2013

@author: rtw
'''
import unittest

from hedgeit.control.clenow import ClenowController
from hedgeit.feeds.db import InstrumentDb
import datetime
import test_util

import os


class Test(unittest.TestCase):


    def setUp(self):
        manifest = '%s/data/manifest1.csv' % os.path.dirname(__file__)        
        self._db = InstrumentDb.Instance()
        self._db.load(manifest)
        

    def tearDown(self):
        pass


    def testClenowRunGroup(self):
        #crg = ClenowRunGroup(['RR','LH','O'])
        
        #crg.feed().start()
        #crg.strategy().exitPositions()
        plog = '%s/positions.csv' % os.path.dirname(__file__)
        elog = '%s/equity.csv' % os.path.dirname(__file__)
        rlog = '%s/returns.csv' % os.path.dirname(__file__)
        slog = '%s/summary.csv' % os.path.dirname(__file__)

        ctrl = ClenowController({ 'Ag-1' : ['RR','LH','O'], 'Ag-2' : ['LB','LC']}, plog, elog, rlog, summaryFile=slog)
        ctrl.run(datetime.datetime(2011,12,31),datetime.datetime(2012,8,1),datetime.datetime(2013,12,31))

        tlog = '%s/trade4.log' % os.path.dirname(__file__)
        ctrl.writeAllTrades(tlog)

        self.assertAlmostEqual(ctrl.get_net_profit(),ctrl.get_trade_profit(),places=2)
        
        crg = ctrl._runGroups['Ag-1']
        trades = crg.trades_analyzer()
        
        self.assertEqual(trades.getCount(),6)
        self.assertEqual(trades.getProfitableCount(),1)
        self.assertEqual(trades.getUnprofitableCount(),5)
        
        self.assertTrue(test_util.file_compare('%s/trade4.reflog' % os.path.dirname(__file__), tlog))
        os.remove(tlog)
        self.assertTrue(test_util.file_compare('%s/positions.refcsv' % os.path.dirname(__file__), plog))
        os.remove(plog)
        self.assertTrue(test_util.file_compare('%s/equity.refcsv' % os.path.dirname(__file__), elog))
        os.remove(elog)
        self.assertTrue(test_util.file_compare('%s/returns.refcsv' % os.path.dirname(__file__), rlog))
        os.remove(rlog)
        self.assertTrue(test_util.file_compare('%s/summary.refcsv' % os.path.dirname(__file__), slog))
        os.remove(slog)

        # now check the last open trades 
        last_trades = ctrl.get_last_exit_orders()
        self.assertEqual(len(last_trades),1)
        self.assertEqual(last_trades[0].getStopPrice(),1476.35)
            
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()