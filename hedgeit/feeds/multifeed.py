'''
hedgeit.feeds.multifeed

Contains:
  class MultiFeed
'''
import hedgeit.common.observer as observer
from bars import Bars
import datetime

class MultiFeed(object):
    '''
    MultiFeed is an aggregator of multiple feeds.  This is essential for any
    portfolio-based strategy and an instance of this class serves as the core
    for Strategy execution.
    '''
    
    def __init__(self):
        '''Constructor.'''
        self._feeds = {}
        self._on_bars_event = observer.Event()
        self._current_bars = {}
        
    def register_feed(self, feed):
        '''
        Registers a new Feed in the MultiFeed.  Each symbol may only exist
        once in the MultiFeed
        
        :param Feed feed: feed to add
        
        :raises: Exception if a feed with the same symbol already exists
        '''
        if self._feeds.has_key(feed.instrument().symbol()):
            raise Exception("MultiFeed already has a Feed for symbol %s" % feed.instrument().symbol())
        self._feeds[feed.instrument().symbol()] = feed
        
    def symbols(self):
        '''Returns a list of the symbols in the MultiFeed.'''
        return self._feeds.keys()
    
    def get_feed(self, symbol):
        '''Returns the Feed instance for the symbol.'''
        return self._feeds[symbol]
    
    def subscribe(self, handler):
        '''Subscribes the handler to the on_bars_event Observer.'''
        return self._on_bars_event.subscribe(handler)

    def unsubscribe(self, handler):
        '''Unsubscribes the handler from the on_bars_event Observer.'''
        return self._on_bars_event.unsubscribe(handler)
    
    def start(self,first=None,last=None):
        '''
        Starts emitting all bars in all feeds from either the current cursor 
        position or the cursor position corresponding to <first> if specified.
        Bars are emitted up to the end of each feed or <last> if specified.
        All Bars for a given datetime are emitted at once and receivers of the 
        event are guaranteed that all bars passed to one handler callback are 
        for the same datetime.  Note that this means each callback may or may not 
        have a Bar for each Feed since it is not the case that all securities 
        trade all days.
        
        :param datetime first: if not None,earliest date emitted from the feed
        :param datetime last: if not None, last date emitted from the feed
        '''
        # first reset all feeds to the start if we need to
        if first != None:
            for f in self._feeds:
                self._feeds[f].set_cursor(first)
        # simply some checks below by setting last to an arbitrary future date
        if last == None:
            last = datetime.datetime(9999,12,31)
            
        bars = None
        smallestDateTime = self.get_next_bars_date()
        if smallestDateTime <= last:
            bars = self._fetch_next_bars(smallestDateTime)
        while bars != None:
            self._on_bars_event.emit(bars)
            smallestDateTime = self.get_next_bars_date()
            if smallestDateTime != None and smallestDateTime <= last:
                bars = self._fetch_next_bars(smallestDateTime)
            else:
                bars = None            
            
    def get_next_bars_date(self):
        '''Returns the next datetime that will be emitted from this feeds.'''
        # all feeds may or may not have the same bars - we need to return the
        # smallest datetime at the head of one of our feeds
        smallestDateTime = None

        # Make a first pass to get the smallest datetime.
        for symbol, feed in self._feeds.iteritems():
            if feed.get_next_bar_date() != None:
                if (smallestDateTime != None and feed.get_next_bar_date() < smallestDateTime) or smallestDateTime == None:
                    smallestDateTime = feed.get_next_bar_date()                    

        return smallestDateTime
        
    def set_cursor(self, datetime=None):
        '''
        Sets each feeds' cursor to the date specified by start.  The cursor 
        determines which Bar is returned on the next call to get_current_bar.
        
        :param datetime start: if present, each feed will be set to the first 
                               Bar that is >= start.  If no date is >=
                               start then the cursor will be set to the end of
                               the list.  If not present, the feed will cursor
                               will be reset to the beginning of the list
        '''
        for symbol, feed in self._feeds.iteritems():
            feed.set_cursor(datetime)
        
    def _fetch_next_bars(self, smallestDateTime):
        '''Find the next earliest datetime and emit all Bars that have an entry for it.'''
        if smallestDateTime == None:
            return None

        # Make a second pass to get all the bars that had the smallest datetime.
        self._current_bars = Bars()
        for symbol, feed in self._feeds.iteritems():
            if feed.get_next_bar_date() == smallestDateTime:
                self._current_bars.add_bar(symbol, feed.get_current_bar())

        return self._current_bars
    
    def get_current_bars(self):
        '''Returns that last set of bars that were emitted by the feed.'''
        return self._current_bars
