'''
Created on Jan 21, 2013

@author: rtw
'''
from hedgeit.feeds.indicator import Indicator
import talib

# Calls a talib function with the last values of a dataseries.
def call_talib_with_c(feed, talibFunc, *parameters):
    data = feed.get_series("Close")
    if data == None:
        return None
    
    return talibFunc(data, *parameters)

def call_talib_with_hlc(feed, talibFunc, *parameters):
    high = feed.get_series("High")
    if high == None:
        return None

    low = feed.get_series("Low")
    if low == None:
        return None

    close = feed.get_series("Close")
    if close == None:
        return None

    return talibFunc(high, low, close, *parameters)

class TalibFunc(Indicator):
    '''
    classdocs
    '''

    def __init__(self, name, feed, talibfunc, talibhelper, *parameters):
        '''
        Constructor
        '''        
        Indicator.__init__(self,name)
        self._feed = feed
        self._talibfunc = talibfunc
        self._talibhelper = talibhelper
        self._parms = parameters

    def calc(self, feed):
        return self._talibhelper(self._feed, self._talibfunc, *self._parms)  
        
def ATR(name,feed,timeperiod):
    """Average True Range"""
    return TalibFunc(name,feed,talib.ATR,call_talib_with_hlc,timeperiod) 

def MAX(name,feed,timeperiod):
    """Highest value over a specified period"""
    return TalibFunc(name,feed,talib.MAX,call_talib_with_c,timeperiod) 
        
def MIN(name,feed,timeperiod):
    """Lowest value over a specified period"""
    return TalibFunc(name,feed,talib.MIN,call_talib_with_c,timeperiod) 

def SMA(name,feed,timeperiod):
    """Simple Moving Average"""
    return TalibFunc(name,feed,talib.SMA,call_talib_with_c,timeperiod) 

def RSI(name,feed,timeperiod):
    """Relative Strength Index"""
    return TalibFunc(name,feed,talib.RSI,call_talib_with_c,timeperiod)

