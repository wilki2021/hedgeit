'''
hedgeit.feeds.csvparser

Contains:
  class RowParser - abstract base class
  class PremiumDataParser - concrete class for parsing Premium Data feed
'''
import datetime
import hedgeit.feeds.bar as bar

class RowParser:
    '''Interface for csv row parsers.'''
    def parseBar(self, csvRowDict):
        raise Exception("Not implemented")

    def getFieldNames(self):
        raise Exception("Not implemented")

    def getDelimiter(self):
        raise Exception("Not implemented")


class PremiumDataParser(RowParser):
    '''
    Concrete RowParser for the Premium Data feed.
    
    # Daily Bars Format:
    # yyyy-MM-dd,open price,high price,low price,close price,volume,open interest
    '''
    
    def __init__(self):
        pass

    def __parseDateTime(self, dateTime):
        # try a few different formats to allow for flexibility
        try:
            ret = datetime.datetime.strptime(dateTime, "%Y-%m-%d")
        except ValueError:
            ret = datetime.datetime.strptime(dateTime, "%Y%m%d")
            
        return ret

    def getFieldNames(self):
        '''Field names present on row 1 so return None.'''
        return ['Date','Open','High','Low','Close','Volume','Open Interest']

    def getDelimiter(self):
        return ","

    def parseBar(self, csvRowDict):
        dateTime = self.__parseDateTime(csvRowDict["Date"])
        close = float(csvRowDict["Close"])
        open_ = float(csvRowDict["Open"])
        high = float(csvRowDict["High"])
        low = float(csvRowDict["Low"])
        volume = float(csvRowDict["Volume"])
        openint = float(csvRowDict["Open Interest"])
        return bar.Bar(dateTime, open_, high, low, close, volume, None)