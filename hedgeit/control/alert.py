'''
hedgeit.control.alert

Contains:
   closs Alert
'''

class Alert(object):
    '''
    Simple struct-like object that the Controller uses to represent information
    that a user needs to execute a strategy.  It includes implied risk, trade
    stops, etc.
    '''

    def __init__(self, datetime, symbol, desc, quant, action, risk, stop):
        '''
        Constructor.
        '''
        self.datetime = datetime
        self.symbol = symbol
        self.description = desc
        self.quantity = quant
        self.action = action
        self.risk = risk
        self.stop = stop
        self.filter_value = 0.0
        self.filter_thresh = 0.0
        self.execute = False
        
    def __str__(self):
        ret = '%s,%s,%s,%d,%s,%0.4f,%0.4f,%0.5f,%0.5f,%s' % (self.datetime.strftime('%Y%m%d'),
                                                self.symbol,
                                                self.description,
                                                self.quantity,
                                                self.action,
                                                self.risk,
                                                self.stop,
                                                self.filter_value,
                                                self.filter_thresh,
                                                self.execute)
        return ret
        
        