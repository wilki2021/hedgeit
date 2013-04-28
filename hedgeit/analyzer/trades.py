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

import hedgeit.analyzer as analyzer
import hedgeit.broker.broker as broker
import hedgeit.analyzer.returns as returns
from postracker import PositionTracker
from hedgeit.feeds.db import InstrumentDb

import numpy as np

class Trades(analyzer.StrategyAnalyzer):
	"""A :class:`pyalgotrade.stratanalyzer.StrategyAnalyzer` that records the profit/loss
	and returns of every completed trade.

	.. note::
		This analyzer operates on individual completed trades.
		For example, lets say you start with a $1000 cash, and then you buy 1 share of XYZ
		for $10 and later sell it for $20:

			* The trade's profit was $10.
			* The trade's return is 100%, even though your whole portfolio went from $1000 to $1020, a 2% return.
	"""

	def __init__(self):
		self.__posTrackers = {}
		self.reset(None)
		self._db = InstrumentDb.Instance()

	def __updateTrades(self, posTracker):
		price = 0 # The price doesn't matter since the position should be closed.
		assert(posTracker.getUnits() == 0)
		netProfit =  posTracker.getNetProfit(price)
		netReturn =  posTracker.getReturn(price)

		if netProfit > 0:
			self.__profits.append(netProfit)
			self.__positiveReturns.append(netReturn )
			self.__profitableCommissions.append(posTracker.getCommissions())
		elif netProfit < 0:
			self.__losses.append(netProfit)
			self.__negativeReturns.append(netReturn )
			self.__unprofitableCommissions.append(posTracker.getCommissions())
		else:
			self.__evenCommissions.append(posTracker.getCommissions())

		self.__all.append(netProfit)
		self.__allReturns.append(netReturn)
		self.__allCommissions.append(posTracker.getCommissions())

		# append this trade record to the master list and then remove the entry from the map
		self._tradeRecords.append(posTracker)		
		del self.__posTrackers[posTracker.getSymbol()]
		
	def __updatePosTracker(self, posTracker, datetime, price, commission, quantity):
		currentShares = posTracker.getUnits()

		if currentShares > 0: # Current position is long
			if quantity > 0: # Increase long position
				posTracker.buy(datetime, quantity, price, commission)
			else:
				newShares = currentShares + quantity
				if newShares == 0: # Exit long.
					posTracker.sell(datetime, currentShares, price, commission)
					self.__updateTrades(posTracker)
				elif newShares > 0: # Sell some shares.
					posTracker.sell(datetime, quantity*-1, price, commission)
				else: # Exit long and enter short. Use proportional commissions.
					posTracker.sell(datetime, currentShares, price, commission / float(currentShares))
					self.__updateTrades(posTracker)
					posTracker.sell(datetime, newShares*-1, price, commission / float(newShares*-1))
		elif currentShares < 0: # Current position is short
			if quantity < 0: # Increase short position
				posTracker.sell(datetime, quantity*-1, price, commission)
			else:
				newShares = currentShares + quantity
				if newShares == 0: # Exit short.
					posTracker.buy(datetime, currentShares*-1, price, commission)
					self.__updateTrades(posTracker)
				elif newShares < 0: # Re-buy some shares.
					posTracker.buy(datetime, quantity, price, commission)
				else: # Exit short and enter long. Use proportional commissions.
					posTracker.buy(datetime, currentShares*-1, price, commission / float(currentShares*-1))
					self.__updateTrades(posTracker)
					posTracker.buy(datetime, newShares, price, commission / float(newShares))
		elif quantity > 0:
			posTracker.buy(datetime, quantity, price, commission)
		else:
			posTracker.sell(datetime, quantity*-1, price, commission)

	def __onOrderUpdate(self, broker_, order):
		# Only interested in filled orders.
		if not order.isFilled():
			return

		# Get or create the tracker for this instrument.
		try:
			posTracker = self.__posTrackers[order.getInstrument()]
		except KeyError:
			posTracker = PositionTracker(self._db.get(order.getInstrument()))
			self.__posTrackers[order.getInstrument()] = posTracker

		# Update the tracker for this order.
		price = order.getExecutionInfo().getPrice()
		commission = order.getExecutionInfo().getCommission()
		action = order.getAction()
		if action in [broker.Order.Action.BUY, broker.Order.Action.BUY_TO_COVER]:
			quantity = order.getExecutionInfo().getQuantity()
		elif action in [broker.Order.Action.SELL, broker.Order.Action.SELL_SHORT]:
			quantity = order.getExecutionInfo().getQuantity() * -1
		else: # Unknown action
			assert(False)

		self.__updatePosTracker(posTracker, order.getExecutionInfo().getDateTime(), price, commission, quantity)

	def attached(self, strat):
		strat.getBroker().getOrderUpdatedEvent().subscribe(self.__onOrderUpdate)

	def getCount(self):
		"""Returns the total number of trades."""
		return len(self.__all)

	def getProfitableCount(self):
		"""Returns the number of profitable trades."""
		return len(self.__profits)

	def getUnprofitableCount(self):
		"""Returns the number of unprofitable trades."""
		return len(self.__losses)

	def getEvenCount(self):
		"""Returns the number of trades whose net profit was 0."""
		return len(self.__evenCommissions)

	def getAll(self):
		"""Returns a numpy.array with the profits/losses for each trade."""
		return np.array(self.__all)

	def getProfits(self):
		"""Returns a numpy.array with the profits for each profitable trade."""
		return np.array(self.__profits)

	def getLosses(self):
		"""Returns a numpy.array with the losses for each unprofitable trade."""
		return np.array(self.__losses)

	def getAllReturns(self):
		"""Returns a numpy.array with the returns for each trade."""
		return np.array(self.__allReturns)

	def getPositiveReturns(self):
		"""Returns a numpy.array with the positive returns for each trade."""
		return np.array(self.__positiveReturns)

	def getNegativeReturns(self):
		"""Returns a numpy.array with the negative returns for each trade."""
		return np.array(self.__negativeReturns)

	def getCommissionsForAllTrades(self):
		"""Returns a numpy.array with the commissions for each trade."""
		return np.array(self.__allCommissions)

	def getCommissionsForProfitableTrades(self):
		"""Returns a numpy.array with the commissions for each profitable trade."""
		return np.array(self.__profitableCommissions)

	def getCommissionsForUnprofitableTrades(self):
		"""Returns a numpy.array with the commissions for each unprofitable trade."""
		return np.array(self.__unprofitableCommissions)

	def getCommissionsForEvenTrades(self):
		"""Returns a numpy.array with the commissions for each trade whose net profit was 0."""
		return np.array(self.__evenCommissions)

	def writeTradeLog(self, filename):
		file_ = open(filename,'w')
		# write the header row
		file_.write('symbol,units,entryDate,entryPrice,exitDate,exitPrice,commissions,profitLoss\n')
		for t in self._tradeRecords:
			file_.write('%s,%d,%s,%f,%s,%f,%0.2f,%0.2f\n' % 
						(t.getSymbol(),
						 t.getTradeSize(),
						 t.getEntryDate(),
						 t.getEntryPrice(),
						 t.getExitDate(),
						 t.getExitPrice(),
						 t.getCommissions(),
						 t.getNetProfit(0)))
		file_.close()

	def reset(self, last_marktomarket):
		'''
		Removes any already completed trades and resets the entry price for
		open trades.  Used by the Controller to reset trading for the
		tradeStart date.  Also called by the constructor to init members
		'''
		self.__all = []
		self.__profits = []
		self.__losses = []
		self.__allReturns = []
		self.__positiveReturns = []
		self.__negativeReturns = []
		self.__allCommissions = []
		self.__profitableCommissions = []
		self.__unprofitableCommissions = []
		self.__evenCommissions = []
		self._tradeRecords = []
		# we need to sum up and return commissions incurred to open the
		# open positions.  This simulates the new open of positions on the
		# trade start date
		ret = 0.0
		for inst in self.__posTrackers:
			ret += self.__posTrackers[inst].getCommissions()			
			self.__posTrackers[inst].resetEntryPrice(last_marktomarket[inst])
		return ret
		
	def trade_records(self):
		return self._tradeRecords