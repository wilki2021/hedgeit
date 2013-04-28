'''
Created on Apr 26, 2013

@author: rtw
'''
import sys
from hedgeit.common.logger import getLogger
import getopt
from datetime import datetime
import json
from hedgeit.control.clenow import ClenowController
from hedgeit.feeds.db import InstrumentDb

Log = getLogger(__name__)
        
def usage():
    print '''
usage: run_clenow.py <manifest> <sector-map> <feedStart> <tradeStart> <tradeEnd>
    
    Options:
        -h          : show usage
        -c <number> : set the starting (per sector) equity (default = 1000000)
        -r <number> : set the risk factor (default = 0.002)
        -b <integer>: set the breakout window length (default = 50)
        -s <number> : set the stop multiplier (in ATR units) (default = 3.0)
        -n          : no intra-day stops (default = intra-day
        
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
'''
    
def main(argv=None):
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hc:r:b:s:n", [])
    except getopt.GetoptError as err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)

    cash = 1000000
    risk = 0.002
    breakout = 50
    stop = 3.0
    intraDay = True
    for o, a in opts:
        if o == "-c":
            cash = float(a)
            Log.info('Setting initial cash position to: %0.2f' % cash)
        elif o == '-r':
            risk = float(a)
            Log.info('Setting risk level to: %0.4f' % risk)
        elif o == "-b":
            breakout = int(a)
            Log.info('Setting breakout window to: %d' % breakout)
        elif o == "-s":
            stop = float(a)
            Log.info('Setting stop multiple to: %0.1f' % stop)
        elif o == "-n":
            intraDay = False
            Log.info('Turning off intra-day stops')
        else:
            usage()
            return
                         
    if len(args) != 5:
        Log.error('Not enough arguments to run_clenow!')
        usage()
        sys.exit(1)
        
    manifest = args[0]
    sectormap = json.load(open(args[1]))

    feedStart = datetime.strptime(args[2], '%Y-%m-%d')
    tradeStart = datetime.strptime(args[3], '%Y-%m-%d')
    tradeEnd = datetime.strptime(args[4], '%Y-%m-%d')

    InstrumentDb.Instance().load(manifest)
        
    plog = 'positions.csv'
    elog = 'equity.csv'
    rlog = 'returns.csv'

    ctrl = ClenowController(sectormap, plog, elog, rlog,cash=cash,riskFactor=risk,breakout=breakout,stop=stop,intraDayStop=intraDay)
    ctrl.run(feedStart, tradeStart, tradeEnd)

    tlog = 'trades.csv'
    ctrl.writeAllTrades(tlog)
    
    Log.info('Net return  :  %0.1f%%' % (ctrl.net_return() * 100.0))
    Log.info('Max drawdown: -%0.1f%%' % (ctrl.drawdown().getMaxDrawDown() * 100.0))

if __name__ == "__main__":
    sys.exit(main())
