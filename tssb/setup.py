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
                srcfile = os.path.join(srcdata,f)
                targfile = os.path.join(datadir,targname)
                shutil.copy(srcfile,targfile)
                
                # we need to replace some negative numbers since TSSB
                # can't handle them.  There are several contracts with 
                # negatives we only deal with a few.  
                if targname == 'RB2.csv' or targname == 'S2.csv':
                    cmd = 'sed -i \'s/\-[\.0-9]*/0\.0001/g\' %s' % targfile
                    os.system(cmd)
                    cmd = 'sed -i \'s/0.00000/0\.0001/g\' %s' % targfile
                    os.system(cmd)
                    
                if targname == 'GO.csv':
                    self.prune_past_negatives(srcfile,targfile)
            
    def usage(self):
        print '''
usage: setup.py [-d <dir>]

    Installs the TSSB executable along with the data set
    
    Parameters:
        None
        
    Options:
        -d <dir> - Path to install to
'''
    
    def prune_past_negatives(self,src,dest):
        # first scan to find the most recent row with no subsequent negatives
        fsrc = open(src)
        lastdate = None
        for line in fsrc.readlines():
            if line.find('-') != -1:
                lastdate = None
            elif not lastdate:
                lastdate = line[0:line.find(',')]
        fsrc.close()
        
        fsrc = open(src)
        fdest = open(dest,'w')
        started = False
        for line in fsrc.readlines():
            if started:
                fdest.write(line)
            else:
                if line.find(lastdate) != -1:
                    started = True
                    fdest.write(line)
        fsrc.close()
        fdest.close()
            
if __name__ == '__main__':
    s = Main()
    sys.exit(s.main())
