'''
hedgeit.strategy.indicators.pvelocity

Contains:
    class PriceVelocity
'''
from hedgeit.feeds.indicator import Indicator
import numpy

class PriceVelocity(Indicator):
    '''
    classdocs
    '''

    def __init__(self, name=None, period=10, baseIndicator=None):
        '''
        Constructor
        '''
        if not name:
            name = 'PVEL(%s,%d)' % (baseIndicator,period)
        Indicator.__init__(self,name)
        self._period = period
        if baseIndicator == None:
            raise Exception("Cannot instantiate PriceVelocity indicator without a base indicator!")
        self._base = baseIndicator
        
    def calc(self, feed):  

        series = numpy.zeros(feed.len())
        base = feed.get_series(self._base)
        x = numpy.arange(0,self._period)
        A = numpy.vstack([x, numpy.ones(len(x))]).T
                
        # first scan through the series and calculate daily true range
        for i in range(0, feed.len()):
            if i < (self._period - 1):
                series[i] = numpy.NAN
            else:
                # alternate method that works fine too
                # slope, intercept, r_value, p_value, std_err = stats.linregress(x,base[i-(self._period-1):i+1])
                y = base[i-(self._period-1):i+1]
                m, c = numpy.linalg.lstsq(A, y)[0]
                series[i] = m
                            
        return series