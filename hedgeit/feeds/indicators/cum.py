'''
hedgeit.strategy.indicators.cum

Implements a indicator that is a moving cumulative sum of another indicator

'''

from hedgeit.feeds.indicator import Indicator
import numpy

class CUM(Indicator):
    '''
    classdocs
    '''

    def __init__(self, name=None, period=2, baseIndicator=None):
        '''
        Constructor
        '''
        if not name:
            name = 'CUM'
        Indicator.__init__(self,name)
        self._period = period
        if baseIndicator == None:
            raise Exception("Cannot instantiate PriceVelocity indicator without a base indicator!")
        self._base = baseIndicator
        
    def calc(self, feed):  
        base = feed.get_series(self._base)
        
        series = numpy.zeros(feed.len())
        cum = 0.0
        for i in range(0, feed.len()):
            if not numpy.isnan(base[i]):
                cum += base[i]
            if i >= self._period and not numpy.isnan(base[i-self._period]):
                cum -= base[i-self._period]
            series[i] = cum
        
        return series