hedgeit
=======
hedgeit is an algorithmic trading tool written in Python.  It has roots in [PyAlgoTrade](http://gbeced.github.io/pyalgotrade/) but with various modifications/enhancements including:

 - Optimized handling of data feeds and indicators.
 - Futures Broker with daily mark-to-market support.
 - Extensive reporting output for trades, returns, etc.
 - Built in support for selection breakout and moving average strategies.

Much of hedgeit was inpired by Andreas Clenow's [Following the Trend](http://www.amazon.com/Following-Trend-Diversified-Managed-Futures/dp/1118410858/ref=sr_1_1?ie=UTF8&qid=1368067548&sr=8-1&keywords=following+the+trend) and the basic strategies follow his systems and recommendations closely.

## Installation

hedgeit depends on Python and various different Python packages.  It is known to work with Python 2.7 and likely works with Python 3.x as well.  For the purposes of this guide, installation from a fresh Ubuntu 12.04 install is assumed.

##### Clone the hedgeit repo.

    git clone https://github.com/wilki2021/hedgeit.git

##### Install numpy

The easiest way to install numpy seems to be the standard Ubuntu package.  You can also use easy_install, but it will require installation of various dependencies (Fortran compilers, etc.).

    sudo apt-get install python-numpy

##### Install pytz

First make sure you have easy_install available and then install

    sudo apt-get install python-setuptools
    sudo easy_install pytz

##### Install TA-Lib

This is a bit more involved.  First you need to download, compile and install the ta-lib library.  Then install the Python wrappers for it.

    wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
    tar xvzf ta-lib-0.4.0-src.tar.gz
    cd ta-lib
    ./configure --prefix=/usr
    make
    sudo make install

    sudo apt-get install python-dev
    sudo apt-get install cython
    sudo easy_install TA-Lib

##### Verify

To verify that everything is working correctly, execute the hedge unit test suite.

    make

If everything worked, there will be some miscellaneous logs followed by something like this.  The number of tests will obviously change over time, but as long as the last line says 'Ok' then the installation is correct.

    ----------------------------------------------------------------------
    Ran 45 tests in 0.709s

    OK


## Usage

hedgeit currently has a single executable `backtest.py`.  This utility executes a Clenow-style strategy for one or more futures markets.  

### hedgeit - mandatory arguments

    usage: backtest.py <manifest> <sector-map> <feedStart> <tradeStart> <tradeEnd>
    
        manifest   : file containing information on tradable instruments.  The file
                     is CSV format - see hedgeit.feeds.db for information
        sector-map : file containing JSON specification for sectors.  Must be 
                     of the form:
                         { '<sector1>' : ['<symbol1>','<symbol2'>,<'symbolN'>],
                           . . .
                           '<sectorN>' : ['<symbol1>','<symbol2'>,<'symbolN'>] }
        feedStart : datetime to start feeds (needs to be early enough to 
                    establish opening position on tradeStart)
        tradeStart: datetime to start tracking real trade performance
        tradeEnd  : datetime to stop backtest 

The manifest file defines the different instruments available for trading.  hedgeit comes with a manifest file in `data/future.csv` that defines a universe of different futures contracts similar to the distribution in the Clenow book.

The sector map is a file in JSON format. It defines one or more sectors, each of which contains one or more symbols.  Each symbol present must correspond to an entry in the manifest file.  The assignment of symbols to sectors is completely arbitrary (as are the sector names).  The purpose of sector assignment is granularity in the various reporting output - returns, margin, etc. are all output on a per sector (but not per symbol) basis.  There are several examples of sector maps in the `examples/` directory.

Finally, there are three dates - feedStart, tradeStart, and tradeEnd.  Each must be specified in the format YYYY-MM-DD (strptime format "%Y-%m-%d") and it must be true that feedStart <= tradeStart <= tradeEnd.  feedStart defines the first *bar* that will be passed to the strategy and tradeEnd defines the last *bar*.  As the name suggests, tradeStart defines the point where trading commences.  All returns, equities, trades, etc. will appear in the output as though they began on the tradeStart date with the strategy taking open positions on that date for any position open at the time.  The philosophy of setting feedStart vs. tradeStart is debatable.  Clenow argued to take any positions that would have been opened at the time trading starts - to simulate this behavior set feedStart sufficiently before tradeStart (I typically use 1 year) so that any opening trades occur and result in open positions at trade start.

So, now an example command-line:

    bin/backtest.py data/future.csv examples/clenow-best40.json 2012-01-01 2013-01-01 2013-12-31

This command uses all defaults and trades for all of 2013.  The feed starts in Jan-2012 so that any positions opened (but not closed) in 2012 are assumed taken on 1/1/2013.  The command will produce output similar to:

    .
    .
    .
    2013-05-08 22:06:06,159 [WARNING] Insufficient equity to meet risk target for RB2, risk multiple 1.551
    2013-05-08 22:06:06,338 [WARNING] Insufficient equity to meet risk target for SI2, risk multiple 1.763
    2013-05-08 22:06:06,520 [INFO] Total Trades    : 44
    2013-05-08 22:06:06,521 [INFO] Total Net Profit: $36686.65
    2013-05-08 22:06:06,521 [INFO] Total Avg Profit: $833.79
    2013-05-08 22:06:06,521 [INFO] Winning Trades  : 23 (52.3%)
    2013-05-08 22:06:06,521 [INFO] Average Winner  : $5605.35 (101.2%)
    2013-05-08 22:06:06,521 [INFO] Losing   Trades : 21 (47.7%)
    2013-05-08 22:06:06,521 [INFO] Average Loser   : $-4392.21 (-83.0%)
    2013-05-08 22:06:06,521 [INFO] There are 1 new trade alerts
    2013-05-08 22:06:06,521 [INFO] Net return     :  3.7%
    2013-05-08 22:06:06,521 [INFO] Max drawdown   : -5.0%

The warnings are because the default starting equity ($1000000) is insufficient to trade a full contract of the specified instrument.  Read the Clenow text for details, but this occurs if the (Average Trading Range (ATR) * point_value) / (equity) > risk (default 0.002).  The strategy will still take these trades (may add a future option to avoid trades over a risk threshold) - the warning just indicates the magnitude of additional risk.  For the RB2 trade above, this means that at the time the trade was opened it has an expected risk of 1.551 * 0.002 or ~0.3% vs. the target 0.2%.  The rest of the console out is relatively self-explanatory.

In addition to the console output, the following output files are generated.  All files are CSV format with a header row to indicate contents.

##### trades.csv

This file contains one row per trade.  Every trade as always a round-trip (any open positions are always shown closed on the final *bar*.  Short trades are indicated by a negative value for *units*.

    description,symbol,units,entryDate,entryPrice,exitDate,exitPrice,commissions,profitLoss
    SUGAR #11,SB2,-3,2012-10-26 00:00:00,19.190000,2013-03-08 00:00:00,18.787900,15.00,1336.06
    JAPANESE YEN,JY,-2,2012-11-16 00:00:00,1.155600,2013-02-25 00:00:00,1.097634,10.00,14481.50

##### summary.csv

This file contains month by year summary returns for the overall startegy.  

    Year,Jan,Feb,Mar,Apr,May,Jun,Jul,Aug,Sep,Oct,Nov,Dec,Full Year
    2013,2.5,0.6,-1.9,1.4,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,2.7

##### returns.csv

This file contains overall returns by sector, with short/long detail.

    Name,Long %,Short %,Total %
    Ag,0.0,-0.6,-0.5
    Currencies,-1.1,2.5,1.4
    Equities,1.9,0.0,1.9
    Non-Ag,-0.0,2.2,2.2
    Rates,-0.4,-0.8,-1.2
    total,0.3,3.3,3.7

##### positions.csv

This file contains position count summaries by sector on both the trade start and trade ending dates.

    Datetime,Ag-Long,Ag-Short,Currencies-Long,Currencies-Short,Equities-Long,Equities-Short,Non-Ag-Long,Non-Ag-Short,Rates-Long,Rates-Short,Total-Long,Total-Short
    2013-01-02 00:00:00,0,2,4,1,2,0,2,1,0,1,8,5
    2013-04-12 00:00:00,0,1,0,1,3,0,1,4,1,0,5,6

##### equity.csv

This file contains daily equity and margin by sector.

    Datetime,Ag-Equity,Ag-Margin,Currencies-Equity,Currencies-Margin,Equities-Equity,Equities-Margin,Non-Ag-Equity,Non-Ag-Margin,Rates-Equity,Rates-Margin,Total-Equity,Total-Margin
    2013-01-02 00:00:00,522.70,6450.00,2257.50,19050.00,5807.50,10300.00,305.30,12150.00,652.50,14500.00,9545.50,62450.00
    2013-01-03 00:00:00,2492.60,6450.00,-4036.25,19050.00,4512.50,10300.00,9.50,12150.00,4010.00,23500.00,6988.35,71450.00

### hedgeit - options

`backtest.py` also supports several options to configure behavior.  These are defined in the usage output as shown here.

	    Options:
	        -h          : show usage
	        -c <number> : set the starting (per sector) equity (default = 1000000)
	        -p <parms>  : model parameters.  Formatted as comma separated list of
	                      key=value pairs.  ex.
	                          atrPeriod=100,period=7
	        -t <model>  : model type ('breakout', 'macross', 'rsireversal', 
	                                  'split7s', 'connorsrsi', default = 'breakout')
	        -g          : no compounding of equity
	        
	        --tssb <name>: write out two files for tssb consumption - <name>_long.csv
	                      and <name>_short.csv containing long and short trades
	                      respectively.   
        
Most options are parameters straight out of the basic Clenow breakout strategy, but a few warrant additional treatment.

Of the possible model options for the `-t` option, the *breakout* and *macross* strategy are straight from the Clenow book.  The *rsicounter* strategy is an experimental counter-trend strategy (results not guaranteed!).

The `-g` option is a special option that affects position sizing.  In the default mode (compounding enabled), trade sizing is done according to current account equity.  Thus, in the case of a successful strategy with rising equity, position sizes will naturally increase.  With compounding off, position sizes are always taken according to starting account equity.  The primary reason for this option is to output a consistent return measure when writing tssb output files where it is important to have a uniform measure of trade profitability over the life of the simulation.

The `-tssb` option writes out two additional files that can be used as input for [TSSB](http://www.tssbsoftware.com/).  There are more details in the tssb README, but the goal is to be able to implement trade filters in TSSB that improve the profitability of trades output by hedgeit.

## TSSB

