'''
hedgeit.feeds.instrument

Contains:
  class Instrument
'''
import csv
from csvparser import PremiumDataParser
from hedgeit.common.logger import getLogger
import os

logger = getLogger("hedgeit.feeds")

class Instrument(object):
    '''
    Instrument associates a symbol with bar data for a tradable instrument.
    At present time, Instrument is hard-coded to support the PremiumData
    feed format input via .csv file.  In the future Instrument may become
    an abstract base class to support different historical and/or real-time
    data feeds
    '''

    def __init__(self, symbol, datafile, pointValue=1, currency='USD', exchange='', \
                 initialMargin=0, maintMargin=0, sector='',description=''):
        '''
        Constructor
        
        :param str symbol: symbol name
        :param str datafile: csv file containing historical bar data
        :param number pointValue: multiplier for one unit of movement in price quote
        :param str currency: currency that the instrument is settled in
        :param str exchange: exchange where the instrument trades
        :param number initialMargin: initial margin requirement per contract
        :param number maintMargin: maintenance margin requirement per contract
        :param str sector: arbtrary sector designation for the instrument
        '''        
        self._symbol = symbol
        self._datafile = datafile
        self._pointValue = pointValue
        self._currency = currency
        self._exchange = exchange
        self._initialMargin = initialMargin
        self._maintMargin = maintMargin
        self._sector = sector
        self._description = description
        self._bars = []
        
    def symbol(self):
        '''Returns the symbol.'''
        return self._symbol
    
    def bars(self):
        '''Returns the list of Bar instances.'''
        return self._bars
    
    def point_value(self):
        '''Returns the point value.'''
        return self._pointValue

    def currency(self):
        '''Returns the currency type.'''
        return self._currency

    def exchange(self):
        '''Returns the exchange.'''
        return self._exchange

    def initial_margin(self):
        '''Returns the initial margin amount.'''
        return self._initialMargin

    def maint_margin(self):
        '''Returns the maintenance margin amount.'''
        return self._maintMargin

    def sector(self):
        '''Returns the sector.'''
        return self._sector
    
    def description(self):
        '''Returns the description.'''
        return self._description
    
    def load_data(self):
        '''Loads Bar data from the datafile.'''
        if not os.path.exists(self._datafile):
            logger.error('Unable to locate datafile %s for %s' % (self._datafile, self._symbol))
            return

        # need to peek at the first line of the file and see if there is a header row
        rowparser = PremiumDataParser()
        f = open(self._datafile)
        if f.readline().find('Date') != -1:
            fieldnames = None
        else:
            fieldnames=rowparser.getFieldNames()
        f.close()
        reader = csv.DictReader(open(self._datafile, "r"), fieldnames=fieldnames, delimiter=rowparser.getDelimiter())
        for row in reader:
            bar_ = rowparser.parseBar(row)
            if bar_ != None:
                self._bars.append( bar_ )
        logger.debug('First bar for symbol %s: %s' % (self._symbol,self._bars[0].datetime()))