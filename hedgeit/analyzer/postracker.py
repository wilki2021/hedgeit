# PyAlgoTrade
# 
# Copyright 2012 Gabriel Martin Becedillas Ruiz
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#   http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
.. moduleauthor:: Gabriel Martin Becedillas Ruiz <gabriel.becedillas@gmail.com>
"""

# Helper class to calculate returns and net profit.
class PositionTracker(object):
    def __init__(self, instrument):
        self.reset()
        self.__instrument = instrument
        self.__pointValue = instrument.point_value()

    def __updateCost(self, quantity, price):
        cost = 0

        if self.__units > 0: # Current position is long
            if quantity > 0: # Increase long position
                cost = quantity * price * self.__pointValue
            else:
                diff = self.__units + quantity
                if diff < 0: # Entering a short position
                    cost = abs(diff) * price * self.__pointValue
        elif self.__units < 0: # Current position is short
            if quantity < 0: # Increase short position
                cost = abs(quantity) * price * self.__pointValue
            else:
                diff = self.__units + quantity
                if diff > 0: # Entering a long position
                    cost = diff * price * self.__pointValue
        else:
            cost = abs(quantity) * price * self.__pointValue
        self.__cost += cost
        
    def getSymbol(self):
        return self.__instrument.symbol()
    
    def getTradeSize(self):
        return self.__tradeSize

    def getEntryDate(self):
        return self.__entryDate
    
    def getEntryPrice(self):
        return self.__entryPrice

    def resetEntryPrice(self, price):
        self.__entryPrice = price
        self.__cost = abs(self.__tradeSize * price * self.__pointValue)
        self.__cash = self.__tradeSize * -1 * price * self.__pointValue
        
    def getExitDate(self):
        return self.__exitDate

    def getExitPrice(self):
        return self.__exitPrice

    def getUnits(self):
        return self.__units

    def getBasis(self):
        return self.__cost

    def getCommissions(self):
        return self.__commissions

    def getNetProfit(self, price, includeCommissions = True):
        ret = self.__cash + self.__units * price * self.__pointValue
        if includeCommissions:
            ret -= self.__commissions
        return ret

    def getReturn(self, price, includeCommissions = True):
        ret = 0
        netProfit = self.getNetProfit(price, includeCommissions)
        cost = self.getBasis()
        if cost != 0:
            ret = netProfit / float(cost)
        return ret
    
    def getMaintMargin(self):
        return abs(self.__units) * self.__instrument.maint_margin()

    def __transact(self, tradeDate, quantity, price, commission = 0):
        if self.__units == 0:
            self.__entryDate = tradeDate
            self.__entryPrice = price
            self.__tradeSize = quantity 
        self.__updateCost(quantity, price)
        self.__cash += quantity * -1 * price * self.__pointValue
        self.__units += quantity
        if self.__units == 0:
            self.__exitDate = tradeDate                 
            self.__exitPrice = price 
        self.__commissions += commission

    def buy(self, tradeDate, quantity, price, commission = 0):
        assert(quantity > 0)
        self.__transact(tradeDate, quantity, price, commission)

    def sell(self, tradeDate, quantity, price, commission = 0):
        assert(quantity > 0)
        self.__transact(tradeDate, -quantity, price, commission)

    def reset(self):
        self.__units = 0
        self.__tradeSize = 0
        self.__commissions = 0
        self.__cash = 0
        self.__cost = 0
        self.__entryDate = None
        self.__entryPrice = 0
        self.__exitDate = None
        self.__exitPrice = 0

