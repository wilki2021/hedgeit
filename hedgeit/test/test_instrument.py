'''
Created on Jan 21, 2013

@author: rtw
'''
import unittest
import os
from hedgeit.feeds.instrument import Instrument

class Test(unittest.TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass


    def testBasic(self):
        datafile = '%s/data/AC___CCB.csv' % os.path.dirname(__file__)

        i = Instrument('AC',datafile)
        i.load_data()
        
        self.assertEqual( i.symbol(), 'AC' )
        self.assertEqual( len(i.bars()), 252 )
        self.assertAlmostEqual( i.bars()[251].open(), 2.35 )
        self.assertAlmostEqual( i.bars()[0].high(), 2.227 )
        self.assertAlmostEqual( i.bars()[100].low(), 2.031 )
        self.assertAlmostEqual( i.bars()[200].close(), 2.337 )

    def testFields(self):
        datafile = '%s/data/AC___CCB.csv' % os.path.dirname(__file__)

        i = Instrument('AC',datafile,pointValue=500,currency='USD', exchange='NYMEX', initialMargin=1480, maintMargin=1170, sector='Ag Commodities', description='test description')
        i.load_data()
        
        self.assertEqual( i.point_value(), 500 )
        self.assertEqual( i.currency(), 'USD' )
        self.assertEqual( i.exchange(), 'NYMEX' )
        self.assertEqual( i.initial_margin(), 1480 )
        self.assertEqual( i.maint_margin(), 1170 )
        self.assertEqual( i.sector(), 'Ag Commodities' )
        self.assertEqual( i.description(), 'test description' )

    def testAltDate(self):
        datafile = '%s/data/S2___CCB.csv' % os.path.dirname(__file__)

        i = Instrument('S2',datafile)
        i.load_data()
        self.assertAlmostEqual( i.bars()[0].close(), 1001.75 )

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testBasic']
    unittest.main()