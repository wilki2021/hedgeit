'''
Created on May 21, 2013

@author: bwilkinson
'''
'''
Created on May 13, 2013

@author: rtw
'''
from tssbutil.paudit import AuditParser
from tssbutil.pvars import VarParser
from tssbutil.runtssb import run_tssb
from tssbutil.sedlite import sed_lite
import getopt
import os
import shutil
import sys

class SimMain(object):
    
    def __init__(self):
        self._stage1_scripts = ['createall.txt','create1.txt']
        self._varmap = {
            '<YEAR_MAX>' : '2013',
            '<VAR_LIST>' : 'varlist.txt',
            '<DB_NAME>'  : 'vardb' }

    def main(self,argv=None):
        try:
            opts, args = getopt.getopt(sys.argv[1:], "", ['rescan'])
        except getopt.GetoptError as err:
            # print help information and exit:
            print str(err) # will print something like "option -a not recognized"
            self.usage()
            sys.exit(2)
    
        rescan = False
        for o, a in opts:
            if o == '--rescan':
                rescan = True
            else:
                # we don't support any options so anything here is a problem.
                self.usage()
                sys.exit(1)
                             
        if len(args) != 2:
            print 'Not enough arguments to subgroup_stability!'
            self.usage()
            sys.exit(1)
            
        varinput = args[0]
        dbloc = args[1]

        for s in self._stage1_scripts:
            if not os.path.exists(s):
                print 'Error: must have the script template %s in current directory' % s
    
        vars_ = VarParser(varinput)        

        if not rescan:
            if os.path.exists(dbloc):
                shutil.rmtree(dbloc)
            os.mkdir(dbloc)
        os.chdir(dbloc)
            
        # write all the individual indicator databases
        read_databases = ''
        for v in vars_.varlist():
            if not rescan:
                # write a file with this one indicator
                tmp = open("tmp.txt","w")
                tmp.write('%s: %s\r\n' % (v,vars_.vars()[v]))
                tmp.close()
                self._varmap['<VAR_LIST>'] = 'tmp.txt'
                self._varmap['<DB_NAME>'] = v
                self.apply_script_template('..\create1.txt', 'create1.txt', self._varmap)
                self.run_tssb_wrapper('create1.txt', 'create1.log')
                
            read_databases = read_databases + 'APPEND DATABASE "%s.DAT" ;\r\n' % v

        self._varmap['<APPEND_DATABASES>'] = read_databases
        self._varmap['<DB_NAME>'] = 'all'
        self.apply_script_template('..\createall.txt', 'createall.txt', self._varmap)
        self.run_tssb_wrapper('createall.txt', 'createall.log')
        
        os.chdir('..')
            
    def usage(self):
        print '''
usage: build_ind_dbs.py <indicator-defns> <db-location>

    Builds TSSB databases given an input file with a list of TSSB indicator
    definitions.  It builds one database with all indicators and one database
    per individual indicator
    
    Parameters:
        <indicator-defns> - a text file containing TSSB indicator defns.
        <db-location>     - directory location to place database files
                            (treated as relative to current)

    Options:
        --rescan          - reuse individual indicator databases to create
                            the aggregate database
'''
    
    def apply_script_template(self, template, output, varmap):
        assert(os.path.exists(template))
        if os.path.exists(output):
            os.remove(output)
        sed_lite(template, output, varmap)
            
    def run_tssb_wrapper(self, script, log):
        tssb = 'C:\\Users\\bwilkinson.Calpont\\TSSB\\tssb64.exe'
        filepath = os.path.join(os.getcwd(), script)
        run_tssb(filepath,tssb_path=tssb)
    
        if not os.path.exists('AUDIT.LOG'):
            raise Exception("TSSB did not appear to write an AUDIT.log file!!")
        
        if os.path.exists(log):
            os.remove(log)
        os.rename('AUDIT.LOG',log)
        
        
if __name__ == '__main__':
    s = SimMain()
    sys.exit(s.main())