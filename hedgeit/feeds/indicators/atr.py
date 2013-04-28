'''
hedgeit.strategy.indicators.atr

Average True Range
'''
from hedgeit.feeds.indicator import Indicator
import numpy

class ATR(Indicator):
    '''
    classdocs
    '''

    def __init__(self, name=None, period=100):
        '''
        Constructor
        '''
        if not name:
            name = 'ATR'
        Indicator.__init__(self,name)
        self._period = period
        
    def calc(self, feed):  
        lastclose = None
        lastatr = None      

        trseries = numpy.zeros(feed.len())
        high = feed.get_series('High')
        low = feed.get_series('Low')
        close = feed.get_series('Close')
        
        # first scan through the series and calculate daily true range
        for i in range(0, feed.len()):
            if lastclose == None:
                tr = high[i] - low[i]
            else:
                tr = max( lastclose, high[i] ) - min( lastclose, low[i] )
                        
            lastclose = close[i]
            trseries[i] = tr

        sum_ = 0.0
        # now scan one more time to compute atr
        series = numpy.zeros(feed.len())
        for i in range(0, feed.len()):
            # add the new entry to the window
            sum_ = sum_ + trseries[i]
            if i < (self._period - 1):
                series[i] = numpy.nan
            else:
                series[i] = sum_ / self._period
                # subtract off the one that is sliding out of the window
                sum_ -= trseries[i-(self._period-1)]
            
        return series