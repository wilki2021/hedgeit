'''
hedgeit.feeds.feed

Contains:
  class Feed
'''
import numpy
from hedgeit.feeds.bar import Bar

class Feed(object):
    '''
    Feed stores a data feed corresponding to one instrument.  Includes both 
    standard bars (open, high, low, close, etc.) plus the ability to add custom
    indicators via the Indicator class.  Also provides various accessors to 
    the different data series and methods to iterate over the bars in the feed
    '''

    def __init__(self, inst):
        '''
        Constructor.
        
        :param Instrument inst: Instrument that this feed is for
        '''
        self._inst = inst
        self._values = []
        self._indictrs = []
        self._lkup = {}
        self._cursor = 0

        # as part of the constructor we will translate from "horizontal" bars
        # to "vertical" data series.  This facilitates the addition of new 
        # indicators since in virtually all cases they are derived via some
        # transform applied to one or more price series.
        #
        # There is one special series containing datetime instances that is 
        # always stored in the first slot of the _values array.  All other
        # series are numpy arrays.  Series can be accessed directly in _values
        # for ones with fixed position (generally this is only for Datetime),
        # but more commonly they are indexed via the _lkup dict that maps 
        # series name to series
        inst.load_data()
        self._len = len(inst.bars())
        
        dates = []
        for b in self._inst.bars():
            dates.append(b.datetime())
        self._add_series('Datetime', dates)

        self._add_from_bars('Open', Bar.open)
        self._add_from_bars('High', Bar.high)
        self._add_from_bars('Low', Bar.low)
        self._add_from_bars('Close', Bar.close)
        self._add_from_bars('Volume', Bar.volume)
        
    def instrument(self):
        '''Returns the Instrument associated with the Feed.'''
        return self._inst
    
    def len(self):
        '''Returns the total number of Bars in this feed.'''
        return self._len
    
    def get_series(self, name):
        '''
        Returns one of the data series.
        
        :param str name: name of series to return
        :returns: numpy array or list of datetime instances
        
        :raises: Exception if series name not found
        '''
        if not self._lkup.has_key(name):
            raise Exception("Workspace does not have a %s series in %s!" % (name, self._lkup.keys()))
        return self._lkup[name]
    
    def insert(self, ind):
        '''
        Adds a new indicator to the feed.
        
        :param Indicator ind: Indicator instance to add
        
        :raises: Exception if Feed already has a series of the same name
        '''
        if self._lkup.has_key(ind.name()):
            raise Exception("Workspace already has an indicator named %s" % ind.name())

        self._indictrs.append(ind)
        series = ind.calc(self)
        self._add_series(ind.name(), series)
            
    def set_cursor(self, start=None):
        '''
        Sets the cursor to the date specified by start.  The cursor determines 
        which Bar is returned on the next call to get_current_bar.
        
        :param datetime start: if present, the cursor will be set to the first 
                               instance that is >= start.  If no date is >=
                               start then the cursor will be set to the end of
                               the list
        '''
        if start != None:
            # the list of dates is always guaranteed to be in _values[0]
            i = 0
            while self._values[0][i] < start and i < len(self._values[0]):
                i = i+1
            self._cursor = i
        else:
            self._cursor = 0
            
    def get_next_bar_date(self):
        '''Returns the datetime of the current Bar instance.'''
        if self._cursor < self._len:
            return self._values[0][self._cursor]
        else:
            return None
        
    def get_current_bar(self):
        '''
        Returns the current Bar as a Bar instance.  The cursor is advanced to 
        point to the next Bar.
        
        :returns Bar: Bar containing all standard fields plus a user-defined
                      field for each indicator in this feed.
        '''
        if self._cursor >= self._len:
            return None
        
        # because of how the code in the constructor above, we all of the 
        # standard bar fields exist at fixed offsets in self._values
        b = Bar(self._values[0][self._cursor],
                self._values[1][self._cursor],
                self._values[2][self._cursor],
                self._values[3][self._cursor],
                self._values[4][self._cursor],
                self._values[5][self._cursor])
        
        for ind in self._indictrs:
            b.set_user_defined(ind.name(), self._lkup[ind.name()][self._cursor])

        self._cursor += 1
        return b

    def get_last_close(self):
        '''
        Returns the closing price the cursor is currently pointing to
        
        :returns float: clasing price
        '''
        # the cursor is always pointing at the next value to return so
        # we need to look at the one previous
        if self._cursor <= 0 or self._cursor >= self._len:
            return 0.0
        else:
            return self._values[4][self._cursor-1] 
        
    def values(self):
        '''Returns the array of data serios.'''
        return self._values    
        
    def _add_series(self, name, series):
        '''Adds a new series to the instance.'''
        if len(series) != self._len:
            raise Exception("Error adding new series %s with length %d that differs from current length %d!" % (name, len(series), self._len))
        self._values.append(series)
        self._lkup[name] = series
        
    def _add_from_bars(self, name, func):
        '''Adds a series from Bar instances by using one of the Bar methods as a functor.'''
        arr = numpy.zeros(self._len)
        for i in range(0, self._len):
            arr[i] = func(self._inst.bars()[i])           
        self._add_series(name, arr)
        
        