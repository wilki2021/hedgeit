'''
Created on May 22, 2013

@author: bwilkinson
'''
import getopt
import os
import shutil
import sys
import re

class Main(object):
    
    def __init__(self):
        pass

    def main(self,argv=None):
        try:
            opts, args = getopt.getopt(sys.argv[1:], "d:", [])
        except getopt.GetoptError as err:
            # print help information and exit:
            print str(err) # will print something like "option -a not recognized"
            self.usage()
            sys.exit(2)
    
        installdir = 'c:\\tssb'
        for o, a in opts:
            if o == '-d':
                installdir = a
            else:
                # we don't support any options so anything here is a problem.
                self.usage()
                sys.exit(1)

        print 'Installing to %s' % installdir
        datadir = os.path.join(installdir,'data')
        
        srcpath = os.path.dirname(__file__)
        srcdist = os.path.join(srcpath,'dist')
        srcdata = os.path.join(srcpath,'..\\data')
        
        if not os.path.exists(installdir):
            os.makedirs(installdir)
        if not os.path.exists(datadir):
            os.makedirs(datadir)
                             
        for f in os.listdir(srcdist):
            print 'Installing %s...' % f
            shutil.copy(os.path.join(srcdist,f),installdir)
            
        symbol = re.compile('([0-9a-zA-Z]+).*\.csv')
        print 'Installing data files...'
        for f in os.listdir(srcdata):
            mat = symbol.match(f)
            if mat:
                targname = '%s.csv' % mat.group(1)
                shutil.copy(os.path.join(srcdata,f),os.path.join(datadir,targname))
            
    def usage(self):
        print '''
usage: setup.py [-d <dir>]

    Installs the TSSB executable along with the data set
    
    Parameters:
        None
        
    Options:
        -d <dir> - Path to install to
'''
    
        
if __name__ == '__main__':
    s = Main()
    sys.exit(s.main())