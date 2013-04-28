'''
hedgeit.feeds.bars

Contains:
  class Bars
'''

class Bars(object):
    '''
    Bars is a collection of Bar instances, typically returned from the
    MultiFeed to represent price activity for a collection of instruments
    over a given trading period.
    '''
    def __init__(self):
        '''Constructor.'''
        self._datetime = None
        self._bars = {}
        
    def add_bar(self, symbol, bar):
        '''
        Adds a new Bar instance to the collection
        
        :param string symbol: symbol corresponding to the Bar instance
        :param Bar bar: instance of type Bar
        
        :raises Exception: if attempting to add a duplicate symbol or a
                           Bar instance with a different datetime than 
                           another Bar
        '''
        if self._datetime != None and bar.datetime() != self._datetime:
            raise Exception("Error in Bars.add_bar(), new Bar datetime(%s) != current datetime(%s)" % \
                            (bar.datetime(), self._datetime) )
        elif self._bars.has_key(symbol):
            raise Exception("Error in Bars.add_bar(), attempt to add duplicate bar for %s" % \
                            symbol)
        else:
            self._bars[symbol] = bar
            self._datetime = bar.datetime()
    
    def get_bar(self, symbol):
        '''
        Returns Bar instance corresponding to symbol.
        
        :returns Bar: Bar instance corresponding to symbol
        :raises KeyError: if symbol not previously added
        '''
        return self._bars[symbol]
    
    def symbols(self):
        '''Returns list of symbols currently in Bars.'''
        return sorted(self._bars.keys())
        
    def datetime(self):
        '''Returns datetime for the Bars collection.'''
        return self._datetime
        
    
        