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

class UpdateMain(object):
    
    def __init__(self):
        self._tradeappdir = 'c:/Trading Applications'
        self._dataconvdir = 'c:/Program Files (x86)/Premium Data Converter'
        self._datadir = os.path.dirname(os.path.abspath(__file__))
        pass

    def main(self,argv=None):
        try:
            opts, args = getopt.getopt(sys.argv[1:], "", [])
        except getopt.GetoptError as err:
            # print help information and exit:
            print str(err) # will print something like "option -a not recognized"
            self.usage()
            sys.exit(2)
    
        for o, a in opts:
            if True:
                # we don't support any options so anything here is a problem.
                self.usage()
                sys.exit(1)
                             
        self.run_updater()
        self.run_exporter()
        self.git_commit()
        
    def usage(self):
        print '''
usage: update.py <TBD>

    Use the Premium Data tools to update our futures dataset
    
    Parameters:
        None

    Options:
        None
'''
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
                updatewin.Exit.Click()
                break
            except:
                time.sleep(0.5)
                
        mainwin.MenuSelect('File->Exit')
            
    def run_exporter(self):
        app = application.Application.start('%s/Premium Data Converter.exe' % self._dataconvdir)
        time.sleep(0.5)
        mainwin = app.window_(title_re="Premium Data Converter.*[0-9\.]+")

        destfolder = self._datadir
        print 'destfolder is %s' % destfolder
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
                
        mainwin.Close()
        
if __name__ == '__main__':
    u = UpdateMain()
    sys.exit(u.main())
