'''
hedgeit.analyzer.istrategy

Contains:
  class InstrumentedStrategy
'''
from hedgeit.analyzer import returns
from hedgeit.analyzer import drawdown
from hedgeit.analyzer import sharpe
from hedgeit.analyzer import trades

class InstrumentedStrategy(object):
    def __init__(self, strategy):
        self._strategy = strategy
        
        # Attach analyzers to the strategy
        self._retAnalyzer = returns.Returns()
        self._strategy.attachAnalyzer(self._retAnalyzer)
        self._sharpeRatioAnalyzer = sharpe.SharpeRatio()
        self._strategy.attachAnalyzer(self._sharpeRatioAnalyzer)
        self._drawDownAnalyzer = drawdown.DrawDown()
        self._strategy.attachAnalyzer(self._drawDownAnalyzer)
        self._tradesAnalyzer = trades.Trades()
        self._strategy.attachAnalyzer(self._tradesAnalyzer)
        
    def feed(self):
        return self._strategy.getFeed()
    
    def strategy(self):
        return self._strategy
    
    def returns_analyzer(self):
        return self._retAnalyzer
    
    def sharpe_analyzer(self):
        return self._sharpeRatioAnalyzer
    
    def drawdown_analyzer(self):
        return self._drawDownAnalyzer
    
    def trades_analyzer(self):
        return self._tradesAnalyzer
    
    def getEquity(self):
        equity = 0.0
        for trade in self._tradesAnalyzer.trade_records():
            equity += trade.getNetProfit(0.0)
        for pos in self._tradesAnalyzer.open_positions().itervalues():
            equity += pos.getNetProfit(self.feed().get_last_close(pos.getSymbol()))
        return equity
    
    def calc_margin(self):
        margin = 0.0
        for pos in self._tradesAnalyzer.open_positions().itervalues():
            margin += pos.getMaintMargin()
        return margin
