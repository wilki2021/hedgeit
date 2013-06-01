'''
Created on May 21, 2013

@author: bwilkinson
'''
from pywinauto import application

import datetime
import traceback
import getopt
import os
import shutil
import sys
import time
from hedgeit.common.sendmail import sendmail
from tssbutil.runtssb import get_process_list,run_tssb
from hedgeit.control.clenow import ClenowController
from hedgeit.feeds.db import InstrumentDb
import json
from hedgeit.common.logger import getLogger
from hedgeit.broker.orders import Order
from tssbutil.pdb import DbParser

Log = getLogger(__name__)

class UpdateMain(object):
    
    def __init__(self):
        self._tradeappdir = 'c:/Trading Applications'
        self._dataconvdir = 'c:/Program Files (x86)/Premium Data Converter'
        # we know this script is in hedgeit/bin.  We need to create the
        # path to hedgeit/data for the data update
        bindir = os.path.dirname(os.path.abspath(__file__))
        self._basedir = os.path.split(bindir)[0]
        self._datadir = os.path.join(self._basedir,'data')
        self._alerts = []
        self._exitOrders = []

    def main(self,argv=None):
        try:
            opts, args = getopt.getopt(sys.argv[1:], "cmd:", [])
        except getopt.GetoptError as err:
            # print help information and exit:
            print str(err) # will print something like "option -a not recognized"
            self.usage()
            sys.exit(2)
    
        do_commit = False
        do_msg = False
        
        for o, a in opts:
            if o == '-c':
                do_commit = True
                print 'Will commit successful update to git repo'
            elif o == '-m':
                do_msg = True
                print 'Will send status SMS message'
            elif o == '-d':
                self._datadir = a
                print 'Will export to directory %s' % self._datadir
            else:
                # we don't support any options so anything here is a problem.
                self.usage()
                sys.exit(1)
                         
        success = True  
        try:  
            self.run_updater()
            print 'Update successful...'
        except:
            success = False
            print 'Update had errors...'
            tb = traceback.format_exc()
            print tb
        sys.stdout.flush()
            
        if success:
            try:  
                self.run_exporter()
                print 'Export to %s successful...' % self._datadir
            except:
                success = False
                print 'Export had errors...'
                tb = traceback.format_exc()
                print tb
            sys.stdout.flush()

        if success and do_commit:
            self.git_commit()
            pass
        
        tradeup = ''
        if success:
            self.run_hedgeit()
            # build a status message
            newtrades = 'New Trades:\n'
            for alert in self._alerts:
                order = alert[0]
                risk  = alert[1]
                newtrades = newtrades + '%s,%s,%d,%0.4f\n' % \
                     (order.getInstrument(),
                     Order.Action.action_strs[order.getAction()],
                     order.getQuantity(),
                     risk)
            print newtrades
            tradeup = 'Trade Updates:\n'
            for exit in self._exitOrders:
                tradeup = tradeup + '%s,%s,%d,%0.5f\n' % \
                    (exit.getInstrument(),
                     Order.Action.action_strs[exit.getAction()],
                     exit.getQuantity(),
                     exit.getStopPrice())
            print tradeup
            
        if success:
            # we need to run the TSSB setup utility to install the
            # updated data files
            tssbsetup = os.path.join(self._basedir,'tssb','setup.py')
            ret = os.system('python %s' % tssbsetup) >> 8
            if ret != 0:
                print 'There were errors installing tssb data'
                success = False
            else:
                print 'TSSB data updates installed successfully'
            
        if success:
            self.run_filter_update()
                
        msg = 'Data update successful' if success else 'Data update failed'
        if do_msg:
            self.send_status(msg, newtrades)
        
        return 0 if success else -1
        
    def usage(self):
        print '''
usage: update.py [-cmd:]

    Use the Premium Data tools to update our futures dataset
    
    Parameters:
        None

    Options:
        -c       - commit data updates to git (default OFF)
        -m       - send status SMS message (default OFF)
        -d <dir> - export to the specified directory.  Note that it must
                   be in Windows format with escaped \\ characters because
                   it is passed directly to the export tool.  Default is 
                   <hedgeit-root>/data
'''
    def run_filter_update(self):
        filtbase = os.path.join(self._basedir,'filters')
        filtlong = os.path.join(filtbase,'filt_long')
        filtshort = os.path.join(filtbase,'filt_short')
        
        # copy the new tssb_(long|short) files
        # shutil.copy('tssb_long.csv', os.path.join(filtlong,'tssb_long.csv'))
        
        # have to figure out different strategy than compute on our own
    
    def run_hedgeit(self):
        cash = 250000
        risk = 0.004
        period = 50
        stop = 3.0
        intraDay = True
        type_ = 'breakout'
        compounding = False
        tssb = 'tssb'
        
        manifest = 'data/future.csv'
        sectormap = json.load(open('examples/clenow-best40.json'))
    
        feedStart = datetime.datetime(1999,1,1)
        tradeStart = datetime.datetime(2000,1,1)
        tradeEnd = datetime.datetime(2013,5,23)
    
        InstrumentDb.Instance().load(manifest)
            
        plog = 'positions.csv'
        elog = 'equity.csv'
        rlog = 'returns.csv'
        slog = 'summary.csv'
        
        ctrl = ClenowController(sectormap, plog, elog, rlog,cash=cash,riskFactor=risk,
                                period=period,stop=stop,intraDayStop=intraDay,
                                summaryFile=slog,modelType=type_,compounding=compounding)
        ctrl.run(feedStart, tradeStart, tradeEnd)
    
        tlog = 'trades.csv'
        ctrl.writeAllTrades(tlog)        
        ctrl.writeTSSBTrades(tssb)
        
        self._alerts = ctrl.get_trade_alerts()
        self._exitOrders = ctrl.get_last_exit_orders()

        Log.info('There were %d new trades and %d position exit updates' % (len(self._alerts), len(self._exitOrders)))                

    def send_status(self, subj, msg):
        toaddr = '2146794968@txt.att.net'
        sendmail(toaddr,subj,msg)

    def git_commit(self):
        now = datetime.datetime.now()
        cmd = 'git commit -a -m "update data for %02d-%02d"' % (now.month,now.day)
        os.system(cmd)
        cmd = 'git push'
        os.system(cmd)
        
    def run_updater(self):
        app = application.Application.start('%s/bin/DataTools.exe' % self._tradeappdir)
        time.sleep(0.5)

        mainwin = app.window_(title_re="DataTools.*[0-9\.]+")        
        mainwin.Wait('ready')
        mainwin.MenuSelect('File->Update Data...')
        time.sleep(0.5)

        while True:
            try:
                updatewin = app.window_(title='Update Data')
                updatewin.Wait('ready')
                updatewin.Update.Click()
                break
            except:
                time.sleep(0.5)
        
        while True:
            try:
                text = updatewin['TRichEdit'].Texts()[0]
                if text.find('This Distribution Complete.') != -1:
                    time.sleep(1.0)
                    break
            except:
                time.sleep(0.5)

        while True:
            try:
                if len(app.windows_(title=u'Update Data')) == 0:
                    break
                else:                                     
                    updatewin.Exit.Click()
            except:
                time.sleep(0.5)

        while True:
            try:
                if not 'DataTools.exe' in get_process_list():
                    break
                else:                                     
                    mainwin.MenuSelect('File->Exit')
            except:
                time.sleep(0.5)
                
            
    def run_exporter(self):
        app = application.Application.start('%s/Premium Data Converter.exe' % self._dataconvdir)
        time.sleep(0.5)
        mainwin = app.window_(title_re="Premium Data Converter.*[0-9\.]+")

        destfolder = self._datadir
        text = ''
        while text != destfolder:
            try:
                mainwin['Edit7'].SetEditText(destfolder)
                text = mainwin['Edit7'].TextBlock()
            except:
                tb = traceback.format_exc()
                print tb
                time.sleep(0.5)

        while True:
            try:
                mainwin.ConverttoText.Click()
                break
            except:
                time.sleep(0.5)

        while True:
            try:
                text = mainwin['WindowsForms10.RichEdit20W.app.0.378734a'].Texts()[0]
                if text.find('Finished.') != -1:
                    time.sleep(1.0)
                    break
            except:
                time.sleep(0.5)

        while True:
            try:
                if not 'Premium Data Converter.exe' in get_process_list():
                    break
                else:                                     
                    mainwin.Close()
            except:
                time.sleep(0.5)
        
if __name__ == '__main__':
    u = UpdateMain()
    sys.exit(u.main())