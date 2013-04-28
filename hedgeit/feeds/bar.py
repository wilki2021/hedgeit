'''
hedgeit.feeds.bar

Contains:
  class Bar
'''

class Bar(object):
    '''
    Bar represents information about a tradable instrument (stock, option,
    futures contract, etc.).  It always contains price information and may
    additionally carry volume and/or open interest information
    '''


    def __init__(self, datetime_, open_, high, low, close, volume = None, open_interest = None, adj_close = None):
        '''
        Bar Constructor.
        
        :param datetime datetime_: the date/time of the Bar
        :param float open_: opening price
        :param float high: high price
        :param float low: low price
        :param float close: closing price
        :param volume: volume traded
        :type volume: int or None
        :param open_interest: open interest
        :type open_interest: int or None
        :param adj_close: adjusted close
        :type adj_close: float or None
        
        :raises AssertionError: if price information is inconsistent (low > high, etc.)
        '''
        assert(high >= open_)
        assert(high >= close)
        assert(low <= open_)
        assert(low <= close)
        self._datetime = datetime_
        self._open = open_
        self._high = high
        self._low = low
        self._close = close
        self._volume = volume
        self._open_interest = open_interest
        self._adj_close = adj_close
        self._user_defined = {}
        
    def set_user_defined(self, name, value):
        '''Interface to set any additional generic value associated with the bar.'''
        self._user_defined[name] = value
        
    def __getattr__(self, attr):
        '''
        This intercepts access to undefined attributes.  We use this to enable 
        callers to be able to access any user-defined values stored in the
        self._user_defined dict as a method.  
        
        Ex.
        b = Bar(...)
        b.set_value(foo, 42)
        print b.foo()
        > 42
        '''
        if not self._user_defined.has_key(attr):
            raise Exception("Bar has no user-defined attribute named %s" % attr)
        return lambda: self._user_defined.get(attr) 

    def __str__(self):
        '''Returns formatted string representation of Bar.'''
        str_ = 'date:%s,open:%s,high:%s,low:%s,close:%s' % \
            (self._datetime, self._open, self._high, self._low, self._close)
        if self._volume != None:
            str_ += ',volume:%s' % self._volume
        if self._open_interest != None:
            str_ += ',open_interest:%s' % self._open_interest
        if self._adj_close != None:
            str_ += ',adjusted_close:%s' % self._adj_close
        for val in self._user_defined:
            str_ += ',%s:%s' % (val, self._user_defined[val])
        return str_
        
    def datetime(self):
        '''Returns datetime of Bar.'''
        return self._datetime
    
    def open(self):
        '''Returns opening price.'''
        return self._open

    def high(self):
        '''Returns high price.'''
        return self._high
        
    def low(self):
        '''Returns low price.'''
        return self._low

    def close(self):
        '''Returns closing price.'''
        return self._close

    def volume(self):
        '''Returns volume.'''
        return self._volume
        
    def open_interest(self):
        '''Returns open_interest.'''
        return self._open_interest

    def adj_close(self):
        '''Returns adjusted close.'''
        return self._adj_close