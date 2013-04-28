'''
hedgeit.feeds.instrument

Contains:
  class InstrumentDb
'''
import csv
from instrument import Instrument
from hedgeit.common.logger import getLogger
from hedgeit.common.singleton import Singleton
import os

logger = getLogger("feeds.db")

@Singleton
class InstrumentDb(object):
    def __init__(self):
        '''
        Constructor.
        '''
        self._db = {}
        
    def load(self, manifest):
        '''    
        Loads the instrument Database using a manifest file.
        
        :param str manifest: file containing the list of instruments to load
        
        File Format:
        The file must be a .CSV file containing a header row with at least the
        following fields:
            description
            symbol
            pointValue
            currency
            exchange
            initialMargin
            maintMargin
            sector
            datafile
        Other fields may be present and will be ignored.  The datafiles 
        corresponding to the Instruments must be in the same directory with
        the manifest file.
        '''
        path, filename = os.path.split(manifest)
        reader = csv.DictReader(open(manifest, "r"))
        for row in reader:
            entry_ = self._parseRow(row, path)
            if entry_ != None:
                self._db[entry_.symbol()] = entry_        

    def get(self, symbol):
        '''Returns the instrument for the specified symbol.'''
        return self._db[symbol]
    
    def get_symbols(self):
        return sorted(self._db.keys())
    
    def _parseRow(self, csvRowDict, basepath):
        '''Parses one row in the manifest file.'''
        description = csvRowDict["description"]
        symbol = csvRowDict["symbol"]
        pointValue = float(csvRowDict["pointValue"])
        currency = csvRowDict["currency"]
        exchange = csvRowDict["exchange"]
        initialMargin = float(csvRowDict["initialMargin"])
        maintMargin = float(csvRowDict["maintMargin"])
        sector = csvRowDict["sector"]
        datafile = basepath + '/' + csvRowDict["datafile"]
        if symbol.find('?') == -1:
            return Instrument(symbol, datafile, pointValue = pointValue, \
                              currency = currency, exchange = exchange, \
                              initialMargin = initialMargin, maintMargin = maintMargin, \
                              sector = sector, description = description)
        else:
            logger.warning('Skipping unknown symbol %s' % symbol )
            return None
        
        
        