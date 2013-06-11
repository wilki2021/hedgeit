'''
hedgeit.strategy.factory

Contains:
   Class StrategyFactory
'''

from trends import *
from countertrends import *

class StrategyFactory(object):
    '''
    classdocs
    '''

    def __init__(self):
        pass

    factoryMethods = {}

    @classmethod
    def register(cls, name, method):
        StrategyFactory.factoryMethods[name] = method
        
    @classmethod
    def create(cls, name, barFeed, symbols = None, broker = None, cash = 1000000,
               compounding = True, parms = None):
        if not StrategyFactory.factoryMethods.has_key(name):
            raise Exception('No strategy %s registered' % name)
        return StrategyFactory.factoryMethods[name](barFeed, 
                                                    symbols = symbols,
                                                    broker = broker,
                                                    cash = cash,
                                                    compounding = compounding,
                                                    parms = parms)
        
StrategyFactory.register('breakout', BreakoutStrategy)
StrategyFactory.register('macross', MACrossStrategy)
        
StrategyFactory.register('rsireversal', RSIReversalStrategy)
StrategyFactory.register('connorsrsi', ConnorsRSIStrategy)
StrategyFactory.register('split7s', Split7sStrategy)
        