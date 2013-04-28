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
import hedgeit.common.observer as observer

class ReturnsAnalyzerBase(analyzer.StrategyAnalyzer):
	def __init__(self):
		self.__netRet = 0
		self.__cumRet = 0
		self.__event = observer.Event()
		self.__lastPortfolioValue = None

	@classmethod
	def getOrCreateShared(cls, strat):
		name = cls.__name__
		# Get or create the shared ReturnsAnalyzerBase.
		ret = strat.getNamedAnalyzer(name)
		if ret == None:
			ret = ReturnsAnalyzerBase()
			strat.attachAnalyzerEx(ret, name)
		return ret

	def attached(self, strat):
		self.__lastPortfolioValue = strat.getBroker().getEquity()

	# An event will be notified when return are calculated at each bar. The hander should receive 1 parameter:
	# 1: This analyzer's instance
	def getEvent(self):
		return self.__event

	def getNetReturn(self):
		return self.__netRet

	def getCumulativeReturn(self):
		return self.__cumRet

	def beforeOnBars(self, strat):
		currentPortfolioValue = strat.getBroker().getEquity()
		netReturn = (currentPortfolioValue - self.__lastPortfolioValue) / float(self.__lastPortfolioValue)
		self.__lastPortfolioValue = currentPortfolioValue

		self.__netRet = netReturn

		# Calculate cumulative return.
		self.__cumRet = (1 + self.__cumRet) * (1 + netReturn) - 1

		# Notify that new returns are available.
		self.__event.emit(self)

class Returns(analyzer.StrategyAnalyzer):
	"""A :class:`pyalgotrade.stratanalyzer.StrategyAnalyzer` that calculates
	returns and cumulative returns for the whole portfolio."""

	def __init__(self):
		self.__netReturns = []
		self.__cumReturns = []

	def beforeAttach(self, strat):
		# Get or create a shared ReturnsAnalyzerBase
		analyzer = ReturnsAnalyzerBase.getOrCreateShared(strat)
		analyzer.getEvent().subscribe(self.__onReturns)

	def __onReturns(self, returnsAnalyzerBase):
		self.__netReturns.append(returnsAnalyzerBase.getNetReturn())
		self.__cumReturns.append(returnsAnalyzerBase.getCumulativeReturn())

	def getReturns(self):
		"""Returns a :class:`pyalgotrade.dataseries.DataSeries` with the returns for each bar."""
		return self.__netReturns

	def getCumulativeReturns(self):
		"""Returns a :class:`pyalgotrade.dataseries.DataSeries` with the cumulative returns for each bar."""
		return self.__cumReturns

