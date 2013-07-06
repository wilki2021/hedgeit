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
from hedgeit.control.controller import Controller
from hedgeit.feeds.db import InstrumentDb
import json
from hedgeit.common.logger import getLogger
from tssbutil.pdb import DbParser
from tssbutil.paudit import AuditParser

Log = getLogger(__name__)

class UpdateMain(object):
    
    def __init__(self):
        self._tradeappdir = 'c:/Trading Applications'
        self._dataconvdir = 'c:/Program Files (x86)/Premium Data Converter'
        # we know this script is in hedgeit/bin.  We need to create the
        # path to hedgeit/data for the data update
        self._bindir = os.path.dirname(os.path.abspath(__file__))
        self._basedir = os.path.split(self._bindir)[0]
        self._datadir = os.path.join(self._basedir,'data')
        self._alerts = []
        self._exitOrders = []

    def main(self,argv=None):
        try:
            opts, args = getopt.getopt(sys.argv[1:], "cmnd:", [])
        except getopt.GetoptError as err:
            # print help information and exit:
            print str(err) # will print something like "option -a not recognized"
            self.usage()
            sys.exit(2)
    
        do_commit = False
        do_msg = False
        do_update = True
        
        for o, a in opts:
            if o == '-c':
                do_commit = True
                print 'Will commit successful update to git repo'
            elif o == '-m':
                do_msg = True
                print 'Will send status SMS message'
            elif o == '-n':
                do_update = False
                print 'Will bypass data update'
            elif o == '-d':
                self._datadir = a
                print 'Will export to directory %s' % self._datadir
            else:
                # we don't support any options so anything here is a problem.
                self.usage()
                sys.exit(1)
                         
        success = True  
        try:
            if do_update:  
                print 'Doing update...'
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
                if do_update:  
                    print 'Doing export...'
                    self.run_exporter()
                    print 'Export to %s successful...' % self._datadir
            except:
                success = False
                print 'Export had errors...'
                tb = traceback.format_exc()
                print tb
            sys.stdout.flush()

        if success:
            print 'Doing backtest...'
            self.run_hedgeit()
            print 'Backtest successful...'
            
        if success:
            print 'Doing TSSB data install...'
            # we need to run the TSSB setup utility to install the
            # updated data files
            tssbsetup = os.path.join(self._basedir,'tssb','setup.py')
            ret = os.system('python %s' % tssbsetup) >> 8
            if ret != 0:
                print 'There were errors installing tssb data'
                success = False
            else:
                print 'TSSB data updates installed successfully'
            
        if success and len(self._alerts):
            print 'Running filter for new trades'
            self.run_filter_update()
            activetrades = ''
            for alert in self._alerts:  
                if alert.execute:
                    if activetrades:
                        activetrades = activetrades + '\n'
                    activetrades = activetrades + \
                        '%s %s %d %s(%s),risk(%0.0f),stop(%0.4f)' % \
                        (alert.datetime.strftime('%Y%m%d'),
                         alert.action,
                         alert.quantity,
                         alert.symbol,
                         alert.description,
                         alert.risk,
                         alert.stop)
            print 'Active Trade Alerts:'
            print activetrades                    

        # do this last so that we pick up any updates that occur during the
        # filter step (in particular we are committing the tssb_long/short
        # trade files
        if success and do_commit:
            self.git_commit()
            pass
                        
        msg = 'Data update successful' if success else 'Data update failed'
        if do_msg:
            self.send_status(msg, activetrades)
        
        return 0 if success else -1
        
    def usage(self):
        print '''
usage: update.py [-cmd:]

    Use the Premium Data tools to update our futures dataset
    
    Parameters:
        None

    Options:
        -n       - skip the data update and export steps (default do update)
        -c       - commit data updates to git (default OFF)
        -m       - send status SMS message (default OFF)
        -d <dir> - export to the specified directory.  Note that it must
                   be in Windows format with escaped \\ characters because
                   it is passed directly to the export tool.  Default is 
                   <hedgeit-root>/data
'''
    def run_filter_update(self):
        filtbase = os.path.join(self._basedir,'filters')
        
        # update our trade filters long first
        filtlong = os.path.join(filtbase,'filt_long')
        
        # copy the new tssb_(long|short) files
        shutil.copy('tssb_long.csv', os.path.join(filtlong,'tssb_long.csv'))
 
        cwd = os.getcwd()       
        os.chdir(filtlong)
        # important to clear any previous db directory because TSSB doesn't
        # overwrite database files (and silently :()
        if os.path.exists('db'):
            shutil.rmtree('db')
        cmd = 'python %s/build_ind_dbs.py TREND_VOLATILITY3.txt db' % os.path.join(self._basedir,'tssb','bin')
        os.system(cmd)
        
        self.run_tssb_wrapper(os.path.join(filtlong,"preselect_test.txt"),'pselect_test_audit.log')
        longparse = AuditParser('pselect_test_audit.log')
        longdb = DbParser('FILTLONG.DAT')
        os.chdir(cwd)
            
        # then short...
        filtshort = os.path.join(filtbase,'filt_short')
        
        # copy the new tssb_(long|short) files
        shutil.copy('tssb_short.csv', os.path.join(filtshort,'tssb_short.csv'))
        
        cwd = os.getcwd()       
        os.chdir(filtshort)
        if os.path.exists('db'):
            shutil.rmtree('db')
        cmd = 'python %s/build_ind_dbs.py TREND_VOLATILITY3.txt db' % os.path.join(self._basedir,'tssb','bin')
        os.system(cmd)
        
        self.run_tssb_wrapper(os.path.join(filtshort,"preselect_test.txt"),'pselect_test_audit.log')
        shortparse = AuditParser('pselect_test_audit.log')
        shortdb = DbParser('FILTSHORT.DAT')
        os.chdir(cwd)

        for alert in self._alerts:
            # model values are hard-coded for the year based on the tradefilt run
            if alert.action == 'BUY':
                parse = longparse
                db = longdb
                model = 'COMM5'
            else:
                parse = shortparse
                db = shortdb
                model = 'COMM5'
            self.check_filter(alert, parse, db, model)

    def run_tssb_wrapper(self, script, log):
        if os.path.exists('AUDIT.LOG'):
            os.remove('AUDIT.LOG')

        run_tssb(script)
    
        if not os.path.exists('AUDIT.LOG'):
            raise Exception("TSSB did not appear to write an AUDIT.log file!!")
        
        if os.path.exists(log):
            os.remove(log)
        os.rename('AUDIT.LOG',log)
            
    def check_filter(self,alert, filtparse, filtdb, model):
        # first we need the threshold for the model
        
        run = filtparse.tssbrun()
        modeliter = run.folds()[0].models()[model]
        stats = modeliter.insample_stats()
        thresh = stats.hi_thresh
        
        date = alert.datetime.strftime("%Y%m%d")
        val = filtdb.get_value(date,alert.symbol,model)            
        execute = True if val >= thresh else False
        alert.filter_value = val
        alert.filter_thresh = thresh
        alert.execute = execute            
        print '%-10s alert for %s - filter val %0.5f vs threshold %0.5f' % (alert.action, alert.symbol, alert.filter_value, alert.filter_thresh)
    
    def run_hedgeit(self):
        manifest = 'data/future.csv'
        sectormap = json.load(open('examples/clenow-best40.json'))
    
        feedStart = datetime.datetime(1999,1,1)
        tradeStart = datetime.datetime(2000,1,1)
        tradeEnd = datetime.datetime(2013,12,31)
    
        InstrumentDb.Instance().load(manifest)
            
        plog = 'positions.csv'
        elog = 'equity.csv'
        rlog = 'returns.csv'
        slog = 'summary.csv'

        parms = { 'riskFactor' : 0.004 }
        
        ctrl = Controller(sectormap, 
                          modelType = 'breakout',
                          cash = 250000,
                          tradeStart = tradeStart,
                          compounding = False,
                          positionsFile = plog, 
                          equityFile = elog, 
                          returnsFile = rlog,
                          summaryFile = slog,
                          parms = parms
                          )
        
        ctrl.run(feedStart, tradeStart, tradeEnd)
    
        ctrl.writeAllTrades('trades.csv')        
        ctrl.writeTSSBTrades('tssb')
        ctrl.writePositionAlerts('alerts.csv')
        
        self._alerts = sorted(ctrl.get_position_alerts(), key=lambda x: x.datetime, reverse=True)

        Log.info('There are %d position updates' % (len(self._alerts)))                

    def send_status(self, subj, msg):
        toaddr = '2146794968@mms.att.net'
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
