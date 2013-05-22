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
        self._stage1_scripts = ['subsample.txt','createdb.txt']
        self._stage2_scripts = ['findgroups.txt','preselect.txt']
        self._varmap = {
            '<YEAR_MAX>' : '2013',
            '<VAR_LIST>' : 'varlist.txt',
            '<DB_NAME>'  : 'vardb',
            '<TRADE_DB>' : '..\\\\..\\\\tssb_long.csv',
            '<NUM_VARS>' : '1',
            '<MODEL>'    : 'QUADRATIC' }
        self._with_val = False

    def main(self,argv=None):
        try:
            opts, args = getopt.getopt(sys.argv[1:], "", ['rescan','trades=','num_vars=','model=','with_val'])
        except getopt.GetoptError as err:
            # print help information and exit:
            print str(err) # will print something like "option -a not recognized"
            self.usage()
            sys.exit(2)
    
        rescan = False
        for o, a in opts:
            if o == '--rescan':
                rescan = True
                print 'Will rescan TSSB results only - no new TSSB runs'
            elif o == '--trades':
                print 'Using trade database %s' % a
                self._varmap['<TRADE_DB>'] = '..\\\\..\\\\' % a
            elif o == '--num_vars':
                print 'Using %s variables' % a
                self._varmap['<NUM_VARS>'] = a
            elif o == '--model':
                print 'Using model type %s' % a
                self._varmap['<MODEL>'] = a
            elif o == '--with_val':
                print 'Using a validation year'
                self._with_val = True
            else:
                # we don't support any options so anything here is a problem.
                self.usage()
                sys.exit(1)
            
        if len(args) != 3:
            print 'Not enough arguments to tradefilt!'
            self.usage()
            sys.exit(1)
    
        runname = args[0]
        yearstart = int(args[1])
        yearend = int(args[2])
    
        for s in self._stage1_scripts:
            if not os.path.exists(s):
                print 'Error: must have the script template %s in current directory' % s
        for s in self._stage2_scripts:
            if not os.path.exists(s):
                print 'Error: must have the script template %s in current directory' % s
    
        vars_ = VarParser('TREND_VOLATILITY3.TXT')
    
        if not rescan:
            if os.path.exists(runname):
                shutil.rmtree(runname)
            os.mkdir(runname)
        os.chdir(runname)
    
        wf = open("perf.csv","w")
        headers = False
        for y in range(yearstart, yearend+1):
            # we get back the results from 1 walk-forward year
            if rescan:
                res = self.rescan_iteration(y)
            else:
                res = self.run_iteration(y, vars_, 13)
    
            if not headers:
                headers = True
                line = 'year,model,long_profit,long_imp,total_ret,max_dd'
                wf.write('%s\n' % line)
    
            for (model,wfmstats) in sorted(res.tssbrun().walkforward_summ().iteritems()):
                line = '%s,%s,%0.4f,%0.4f,%0.2f,%0.2f' % \
                        (y,model, wfmstats.long_profit_fac, wfmstats.long_only_imp, wfmstats.long_total_ret, wfmstats.long_maxdd)
                wf.write('%s\n' % line)
        wf.close()
        os.chdir('..')
    
    def usage(self):
        print '''
usage: tradefilt.py [options] <run-name> <year-start> <year-end>

    Performs an "outer" walk-forward analysis loop across a series of
    years per the command-line arguments.  Each "inner" walk-forward 
    is a discrete (and currently hard-coded) series of steps to select
    a smaller indicator set from a larger one and then select and train
    a series of models from them.
    
    Parameters:
        <run-name>    - this is the name of the subdirectory that will
                        contain run results.  The run directory will 
                        always have one sub-directory for each year in 
                        the outer walk-forward loop.
        <year-start>  - integer, year to start the outer walk-forward.
                        NOTE - for any given walk-forward year, that
                        year is included in the training set and the 
                        subsequent year is treated as the test/validation
                        period.
        <year-end>    - integer, year to end the outer walk forward.

    Options:
        --rescan      - do not perform any new TSSB runs, just uses 
                        existing .log files from a previous run and 
                        re-reports results
        --trades <file> - file containing the trades to use for this
                        model run. (default = tssp_long.csv)
        --num_vars <num>- number of variables to use for each source
                        model. (default = 1)
        --model <type>- model type to use for source models.  Supported
                        options: LINREG, QUADRATIC, GRNN. (default =
                        LINREG)
        --with_val      use a validation year to select models based
                        on out-of-sample performance.  Note - this option
                        shifts the true walk-forward year ahead by 1 so
                        performance for 2002 is actually out-of-sample
                        performance for 2004 
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
        
    def run_iteration(self,year, vars_, lag):
        print 'Running iteration for year %d' % year
        
        workdir = '%s' % year
        if os.path.exists(workdir):
            shutil.rmtree(workdir)
        os.mkdir(workdir)
            
        os.chdir(workdir)
        
        # update values for this iteration
        self._varmap['<YEAR_START>'] = '%s' % (year - lag)
        self._varmap['<YEAR_END>'] = '%s' % year
        if self._with_val:
            self._varmap['<VAL_YEAR>'] = '%s' % (year + 1)
            self._varmap['<TEST_YEAR>'] = '%s' % (year + 2)
        else:
            self._varmap['<TEST_YEAR>'] = '%s' % (year + 1)
        
        for s in self._stage1_scripts:
            self.apply_script_template(os.path.join("..","..",s), s, self._varmap)
    
        # first run the subsample test to narrow predictors
        log = 'sub_audit.log'
        self.run_tssb_wrapper(self._stage1_scripts[0],log)
        sub = AuditParser(log)
        varfile = open('varlist.txt','w') # must match VAR_LIST entry above
        varlist = sub.tssbrun().selection_stats().list_all_gt(3.0)   
        for var in varlist:
            varfile.write('%s: %s\r\n' % (var[0],vars_.vars()[var[0]]))
        varfile.close()    
    
        # now create our database
        log = 'create_audit.log'
        self.run_tssb_wrapper(self._stage1_scripts[1],log)
        
        self._varmap['<VAR_1>'] = varlist[0][0]
        self._varmap['<VAR_N>'] = varlist[-1][0]
        self.apply_script_template(os.path.join("..","..",'findgroups.txt'), 'findgroups.txt', self._varmap)
    
        # now get our groups
        log = 'fgroup_audit.log'
        self.run_tssb_wrapper(self._stage2_scripts[0],log)
        groups = AuditParser(log)
        fold = groups.tssbrun().folds()[0]
        if not self._with_val:
            for (name,modeliter) in fold.models().iteritems():
                groupname = '<GROUP%s>' % name
                varspec = ''
                for var in modeliter.defn().get_factors():
                    if var[0] != 'CONSTANT':
                        varspec = varspec + ' ' + var[0]
                self._varmap[groupname] = varspec
                
            # there is a potential that we didn't supply enough 
            # variables to find the target number of groups (currently 5)
            # need to make sure we don't use stale <GROUP> values from
            # an earlier iteration.  We reuse models starting from the
            # top of the list to fill in up to 5
            if len(fold.models()) < 5:
                count = len(fold.models())
                for i in range(count+1,6):
                    fromkey = '<GROUP%d>' % i
                    tokey = '<GROUP%d>' % (i-count)
                    self._varmap[fromkey] = self._varmap[tokey]
        else:
            ranked = sorted(fold.models().itervalues(), key=lambda x: x.oosample_stats().long_only_imp, reverse=True)
            for i in range(1,4):
                groupname = '<GROUP%d>' % i
                modeliter = ranked[i-1]
                varspec = ''
                for var in modeliter.defn().get_factors():
                    if var[0] != 'CONSTANT':
                        varspec = varspec + ' ' + var[0]
                self._varmap[groupname] = varspec
                    
        self.apply_script_template(os.path.join("..","..",'preselect.txt'), 'preselect.txt', self._varmap)
    
        # finally execute against our test year
        log = 'pselect_audit.log'
        self.run_tssb_wrapper("preselect.txt",log)
        ret = AuditParser(log)
        
        os.chdir("..")
        return ret
    
    def rescan_iteration(self,year):
        audfile = '%d/pselect_audit.log' % year
        if not os.path.exists(audfile):
            raise Exception('Cannot rescan - %s does not exist!' % audfile)
        return AuditParser(audfile)
        
if __name__ == '__main__':
    s = SimMain()
    sys.exit(s.main())
