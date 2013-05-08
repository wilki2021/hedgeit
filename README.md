hedgeit
=======
hedgeit is an algorithmic trading tool written in Python.  It has roots in `PyAlgoTrade` but with various modifications/enhancements including:

 - Optimized handling of data feeds and indicators.
 - Futures Broker with daily mark-to-market support.
 - Extensive reporting output for trades, returns, etc.
 - Built in support for selection breakout and moving average strategies.

Much of hedgeit was inpired by Andreas Clenow's **Following the Trend** and the basic strategies follow his systems and recommendations closely.

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

hedgeit currently has a single executable `run_clenow.py`.  This utility executes a Clenow-style strategy for one or more futures markets.  The usage (`run_clenow.py -h`) is as follows:

    usage: run_clenow.py <manifest> <sector-map> <feedStart> <tradeStart> <tradeEnd>
    
        Options:
           -h          : show usage
           -c <number> : set the starting (per sector) equity (default = 1000000)
           -r <number> : set the risk factor (default = 0.002)
           -p <integer>: set the strategy period (default = 50)
                         the meaning of period is strategy-dependent as follows:
                           breakout - breakout min/max = period
                                      short moving average = period
                                      long moving average = period*2
                           macross  - short moving average = period / 10
                                      long moving average = period
                           rsicounter-rsi period = period 
           -s <number> : set the stop multiplier (in ATR units) (default = 3.0)
           -n          : no intra-day stops (default = intra-day)
           -t          : model type ('breakout', 'macross', or 'rsicounter', 
                         default = 'breakout')
           -g          : no compounding of equity
        
           -tssb <name>: write out two files for tssb consumption - <name>_long.csv
                         and <name>_short.csv containing long and short trades
                         respectively.   
        
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

## TSSB

