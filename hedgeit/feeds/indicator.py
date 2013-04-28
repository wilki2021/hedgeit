'''
hedgeit.feeds.indicator

An indicator that can be used in a strategy
'''
from abc import ABCMeta, abstractmethod

class Indicator(object):
    '''
    Indicator is an abstract base class that defines the interface for
    the signals that can be used to form trading strategies
    '''

    def __init__(self, name):
        '''
        Constructor
        
        @param name      - name used to reference the indicator
        '''
        self._name = name
        
    def name(self):
        return self._name
    
    @abstractmethod
    def calc(self, feed):
        """
        Produce the data series for the indicator in the input feed.
        
        :param Feed feed: feed that the indicator is for
        :returns: indicator data serios
        :rtype: numpy array
        """
        raise Exception("Not implemented")
