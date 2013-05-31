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
from tssbutil.runtssb import get_process_list

class UpdateMain(object):
    
    def __init__(self):
        self._tradeappdir = 'c:/Trading Applications'
        self._dataconvdir = 'c:/Program Files (x86)/Premium Data Converter'
        self._datadir = os.path.dirname(os.path.abspath(__file__))
        pass

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
        
        msg = 'Data update successful' if success else 'Data update failed'
        if do_msg:
            self.send_status(msg)
        
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
        
    def send_status(self, msg):
        toaddr = '2146794968@txt.att.net'
        sendmail(toaddr,msg,'')

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