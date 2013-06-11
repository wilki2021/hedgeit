#!/usr/bin/env python
'''
Created on Apr 26, 2013

@author: rtw
'''
import sys
from hedgeit.common.logger import getLogger
import getopt
from datetime import datetime
import json
from hedgeit.control.controller import Controller
from hedgeit.feeds.db import InstrumentDb

Log = getLogger(__name__)
        
def usage():
    print '''
usage: backtest.py <manifest> <sector-map> <feedStart> <tradeStart> <tradeEnd>
    
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
    
def parseParmString(str_):
    ret = {}
    pairs = str_.strip().split(',')
    for p in pairs:
        (var, value) = p.strip().split('=')
        ret[var] = eval(value)
    return ret

def main(argv=None):
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hc:p:t:g", ["tssb="])
    except getopt.GetoptError as err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)

    cash = 1000000
    type_ = 'breakout'
    compounding = True
    tssb = None
    parms = None
    for o, a in opts:
        if o == "-c":
            cash = float(a)
            Log.info('Setting initial cash position to: %0.2f' % cash)
        elif o == "-p":
            parms = parseParmString(a)
            Log.info('Using model parms: %s' % parms)
        elif o == "-t":
            type_ = a
            Log.info('Using model %s' % type_)
        elif o == "-g":
            compounding = False
            Log.info('Compounding disabled')
        elif o == "--tssb":
            tssb = a
            Log.info('Writing tssb files with base %s' % tssb)
        else:
            usage()
            return
                         
    if len(args) != 5:
        Log.error('Not enough arguments to backtest!')
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
    slog = 'summary.csv'
    
    ctrl = Controller(sectormap, 
                      modelType = type_,
                      cash = cash,
                      tradeStart = tradeStart,
                      compounding = compounding,
                      positionsFile = plog, 
                      equityFile = elog, 
                      returnsFile = rlog,
                      summaryFile = slog,
                      parms = parms
                      )
    ctrl.run(feedStart, tradeStart, tradeEnd)

    tlog = 'trades.csv'
    ctrl.writeAllTrades(tlog)
    if tssb:
        ctrl.writeTSSBTrades(tssb)
    
    alog = 'alerts.csv'
    ctrl.writePositionAlerts(alog)
    
    Log.info('Net return     :  %0.1f%%' % (ctrl.net_return() * 100.0))
    Log.info('Max drawdown   : -%0.1f%%' % (ctrl.drawdown().getMaxDrawDown() * 100.0))

if __name__ == "__main__":
    sys.exit(main())
