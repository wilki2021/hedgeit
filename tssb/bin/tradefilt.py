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
import json
import numpy
import copy
import time

class SimMain(object):
    
    def __init__(self):
        self._stage1_scripts = ['subsample.txt']
        self._stage2_scripts = ['createdb.txt','findgroups.txt','preselect.txt']
        self._varmap = {
            '<YEAR_MAX>' : '2013',
            '<VAR_LIST>' : 'varlist.txt',
            '<DB_NAME>'  : 'vardb',
            '<TRADE_DB>' : '..\\\\..\\\\tssb_long.csv',
            '<NUM_VARS>' : '1',
            '<MODEL>'    : 'QUADRATIC',
            '<RETENTION>': '10',
            '<MIN_CRIT>' : '0.3',
            '<AGG_DB>'   : 'ALL',
            '<STAGE1_CRIT>' : 'SHORT PROFIT FACTOR',
            '<STAGE2_CRIT>' : 'LONG PROFIT FACTOR',
            '<STAGE3_CRIT>' : 'LONG PROFIT FACTOR' }
        self._with_val = False
        self._var_thresh = 3.0
        self._varbase = 'db/ALL'
        self._headers = False

    def main(self,argv=None):
        try:
            opts, args = getopt.getopt(sys.argv[1:], "", 
                                       ['rescan','trades=','num_vars=','model=',
                                        'with_val','retention=','min_crit=',
                                        'var_thresh=','vars=','stage1_crit=',
                                        'stage2_crit=','stage3_crit='])
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
                self._varmap['<TRADE_DB>'] = '..\\\\..\\\\%s' % a
            elif o == '--num_vars':
                print 'Using %s variables' % a
                self._varmap['<NUM_VARS>'] = a
            elif o == '--model':
                print 'Using model type %s' % a
                self._varmap['<MODEL>'] = a
            elif o == '--with_val':
                print 'Using a validation year'
                self._with_val = True
            elif o == '--retention':
                int(a)
                print 'Setting STEPWISE RETENTION to %s' % a
                self._varmap['<RETENTION>'] = a
            elif o == '--min_crit':
                float(a)
                print 'Setting MIN CRITERION FRACTION to %s' % a
                self._varmap['<MIN_CRIT>'] = a
            elif o == '--var_thresh':
                self._var_thresh = float(a)
                print 'Setting variable selection threshold to %s' % a
            elif o == '--vars':
                self._varbase = a
                self._varmap['<AGG_DB>'] = a
                print 'Using aggregate variable database %s' % a
            elif o == '--stage1_crit':
                self._varmap['<STAGE1_CRIT>'] = a
                print 'Using stage 1 criterion %s' % a                                
            elif o == '--stage2_crit':
                self._varmap['<STAGE2_CRIT>'] = a
                print 'Using stage 2 criterion %s' % a                                
            elif o == '--stage3_crit':
                self._varmap['<STAGE3_CRIT>'] = a
                print 'Using stage 3 criterion %s' % a                                
            else:
                # we don't support any options so anything here is a problem.
                self.usage()
                sys.exit(1)
            
        if rescan:
            self.do_rescan(args)
            return
            
        if len(args) != 3:
            print 'Not enough arguments to tradefilt!'
            self.usage()
            sys.exit(1)
    
        runname = args[0]
        yearstart = int(args[1])
        yearend = int(args[2])
    
        if not rescan:
            for s in self._stage1_scripts:
                if not os.path.exists(s):
                    print 'Error: must have the script template %s in current directory' % s
            for s in self._stage2_scripts:
                if not os.path.exists(s):
                    print 'Error: must have the script template %s in current directory' % s

            vars_ = VarParser('%s.TXT' % self._varbase)
            if not os.path.exists(runname):
                os.mkdir(runname)
    
        os.chdir(runname)
        self.run_years(yearstart, yearend, rescan=False, vars_=vars_)        
        os.chdir('..')
        
    def usage(self):
        print '''
usage: tradefilt.py [options] <run-name> <year-start> <year-end>
       tradefile.py --rescan [run-directories]

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
        --rescan      - do not perform any new TSSB runs.  Takes an optional
                        list of run directories to scan - by default it 
                        assumes all subdirectories in the current directory
                        are runs and will rescan each.  If this option is
                        used it is the only option that is processed.
        --trades <file>- file containing the trades to use for this
                        model run. (default = tssp_long.csv)
        --num_vars <num>- number of variables to use for each source
                        model. (default = 1)
        --model <type>- model type to use for source models.  Supported
                        options: LINREG, QUADRATIC, GRNN. (default =
                        LINREG)
        --with_val    - use a validation year to select models based
                        on out-of-sample performance.  Note - this option
                        shifts the true walk-forward year ahead by 1 so
                        performance for 2002 is actually out-of-sample
                        performance for 2004 
        --retention <num>-value to use for the STEPWISE RETENTION 
                        setting in all relevant stages
        --min_crit <float>-value to use for the MIN CRITERION FRACTION
                        setting in all relevant stages
        --var_thresh <float>-threshold to use for variable selection after
                        the subsampling stage
        --vars <base> - base name of the aggregate variable database and
                        corresponding definition file 
        --stage1_crit <crit>-set the CRITERION to be used for the stage 1-
                        subsampling phase used for variable down-select. 
                        Most be one of the supported TSSB criterion strings.
        --stage2_crit <crit>-set the CRITERION to be used for the stage 2-
                        find groups phase used for model selection. 
                        Most be one of the supported TSSB criterion strings.
        --stage3_crit <crit>-set the CRITERION to be used for the stage 3-
                        walk-forward testing.
'''
    
    def do_rescan(self,dirs):
        # if dirs is not empty then we assume user provided a list they
        # wanted to rescan.  If no list is provided then we scan all
        if not len(dirs):
            dirents = os.listdir('.')
            for ent in dirents:
                if os.path.isdir(ent) and ent != '..' and ent != '.' and ent != 'db':
                    dirs.append(ent)
                    
        for d in sorted(dirs):
            os.chdir(d)
            print 'INFO: scanning %s' % d
            if os.path.exists('runvars.json'):
                for line in open('runvars.json').readlines():
                    print line.strip()
            # inside a run directory we should find one directory per year that
            # the filter was run for
            yearstart = 9999
            yearend = 1
            for ent in os.listdir('.'):
                if os.path.isdir(ent) and ent != '..' and ent != '.':
                    y = int(ent)
                    if y < yearstart:
                        yearstart = y
                    if y > yearend:
                        yearend = y
                    
            self.run_years(yearstart, yearend, rescan=True)
            os.chdir('..')

    def run_years(self, yearstart, yearend, rescan=False, vars_=None):
        if not rescan:
            # only dump out the runvars if not rescanning
            wf = open("runvars.json",'w')
            vardump = json.dumps(self._varmap,indent=4,sort_keys=True)
            wf.write(vardump)
            wf.close()

        wf = open("perf.csv","w")
        resultsumm = {}
        for y in range(yearstart, yearend+1):
            # sanity check the year the user gave us to make sure it makes sense
            if (self._with_val and ((y + 2) > int(self._varmap['<YEAR_MAX>']))) or \
                (not self._with_val and ((y + 1) > int(self._varmap['<YEAR_MAX>']))):
                print 'Warning - skipping year %d because no data' % y
                continue
                
            # we get back the results from 1 walk-forward year
            if rescan:
                res = self.rescan_iteration(y)
            else:
                res = self.run_iteration(y, vars_, 13)
    
            if not self._headers:
                self._headers = True
                line = 'year'
                for model in sorted(res.tssbrun().walkforward_summ().iterkeys()):
                    line = line + ",%s" % model
                wf.write('%s\n' % line)
    
            line = '%s' % y
            for (model,wfmstats) in sorted(res.tssbrun().walkforward_summ().iteritems()):
                line = line + ',%0.2f' % wfmstats.long_total_ret
                if not resultsumm.has_key(model):
                    resultsumm[model] = [[],[],[],[],[]]
                    
                resultsumm[model][0].append(wfmstats.long_only_imp)
                resultsumm[model][1].append(wfmstats.long_total_ret)
                resultsumm[model][2].append(wfmstats.long_maxdd)
                resultsumm[model][3].append(wfmstats.total_cases)
                resultsumm[model][4].append(wfmstats.num_above_high)
            wf.write('%s\n' % line)
            
        line = 'avg_total_ret'
        for (model,wfmstats) in sorted(res.tssbrun().walkforward_summ().iteritems()):
            line = line + ',%0.2f' % numpy.average(resultsumm[model][1])
        wf.write('%s\n' % line)

        line = 'std_total_ret'
        for (model,wfmstats) in sorted(res.tssbrun().walkforward_summ().iteritems()):
            line = line + ',%0.2f' % numpy.std(resultsumm[model][1])
        wf.write('%s\n' % line)

        line = 'ret_std_ratio'
        for (model,wfmstats) in sorted(res.tssbrun().walkforward_summ().iteritems()):
            line = line + ',%0.3f' % (numpy.average(resultsumm[model][1]) / numpy.std(resultsumm[model][1]))
        wf.write('%s\n' % line)

        line = 'avg_long_imp'
        for (model,wfmstats) in sorted(res.tssbrun().walkforward_summ().iteritems()):
            line = line + ',%0.2f' % numpy.average(resultsumm[model][0])
        wf.write('%s\n' % line)

        line = 'avg_maxdd'
        for (model,wfmstats) in sorted(res.tssbrun().walkforward_summ().iteritems()):
            line = line + ',%0.2f' % numpy.average(resultsumm[model][2])
        wf.write('%s\n' % line)

        line = 'ret_maxdd_ratio'
        for (model,wfmstats) in sorted(res.tssbrun().walkforward_summ().iteritems()):
            line = line + ',%0.3f' % (numpy.average(resultsumm[model][1]) / numpy.average(resultsumm[model][2]))
        wf.write('%s\n' % line)
        
        wf.close()
        ranked = sorted(resultsumm.items(), key=lambda x: numpy.average(x[1][1]), reverse=True)
        print 'Ranked model performance...'
        print '%-12s%-12s%-12s%-12s%-12s' % ('Model','Avg Ret', 'Avg Imp','Ret/Std Rat','Trade Rat')
        for (k,v) in ranked:
            print '%-12s%-12.2f%-12.3f%-12.3f%-12.3f' % (k, 
                                                         numpy.average(v[1]),
                                                         numpy.average(v[0]),
                                                         numpy.average(v[1]) / numpy.std(v[1]),
                                                         numpy.sum(v[4]) * 1.0 / numpy.sum(v[3]))
            
    def apply_script_template(self, template, output, varmap):
        assert(os.path.exists(template))
        if os.path.exists(output):
            os.remove(output)
        sed_lite(template, output, varmap)
            
    def run_tssb_wrapper(self, script, log):
        filepath = os.path.join(os.getcwd(), script)
        run_tssb(filepath)
    
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
            self._varmap['<VAL_YEAR>'] = '%s' % (year + 1)
            self._varmap['<TEST_YEAR>'] = '%s' % (year + 1)
        # check for a special case here - if the DB was generated by build_ind_dbs
        # the first variable is always RSI_99 which is a dummy variable used to
        # make TSSB happy
        if vars_.varlist()[0] == 'RSI_99':
            self._varmap['<VAR_1>'] = vars_.varlist()[1]
        else:
            self._varmap['<VAR_1>'] = vars_.varlist()[0]
        self._varmap['<VAR_N>'] = vars_.varlist()[-1]
        
        for s in self._stage1_scripts:
            self.apply_script_template(os.path.join("..","..",s), s, self._varmap)
    
        # first run the subsample test to narrow predictors
        log = 'sub_audit.log'
        self.run_tssb_wrapper(self._stage1_scripts[0],log)
        sub = AuditParser(log)
        
        varlist = sub.tssbrun().selection_stats().list_all_gt(self._var_thresh)
        app_dbs = ''   
        for var in varlist:
            app_dbs = app_dbs + ('APPEND DATABASE "..\\\\..\\\\db\\\\%s.DAT" ;\r\n' % var[0])
        self._varmap['<APPEND_DATABASES>'] = app_dbs
        self.apply_script_template(os.path.join("..","..",'createdb.txt'), 'createdb.txt', self._varmap)
        log = 'create_audit.log'
        retry_cnt = 0
        while retry_cnt < 3:
            try:
                # don't understand this, but dealing with periodic failures of 
                # this step in the iteration - most often several years in
                self.run_tssb_wrapper('createdb.txt',log)
                break
            except:
                ++retry_cnt
                print 'tssb createdb.txt failed, trying %d more times' % (3-retry_cnt)
                time.sleep(5.0)            
            
        self._varmap['<VAR_1>'] = varlist[0][0]
        self._varmap['<VAR_N>'] = varlist[-1][0]
        self.apply_script_template(os.path.join("..","..",'findgroups.txt'), 'findgroups.txt', self._varmap)
    
        # now get our groups
        log = 'fgroup_audit.log'
        self.run_tssb_wrapper('findgroups.txt',log)
        groups = AuditParser(log)
        fold = groups.tssbrun().folds()[0]
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

        self.apply_script_template(os.path.join("..","..",'preselect.txt'), 'preselect.txt', self._varmap)
        log = 'pselect_audit.log'
        self.run_tssb_wrapper("preselect.txt",log)
        ret = AuditParser(log)

        if self._with_val:
            varmap2 = copy.deepcopy(self._varmap)
            fold = ret.tssbrun().folds()[0]
            ranked = sorted(fold.models().itervalues(), key=lambda x: x.oosample_stats().long_only_imp, reverse=True)
            for i in range(1,4):
                groupname = '<GROUP%d>' % i
                modeliter = ranked[i-1]
                # we know that the model name is FILTLONGN where N=[1..5] and further
                # that <GROUPN> corresponds to FILTLONGN from the previous step
                fromkey = '<GROUP%s>' % modeliter.name()[-1]
                varmap2[groupname] = self._varmap[fromkey]
            
            self.apply_script_template(os.path.join("..","..",'preselect_test.txt'), 'preselect_test.txt', varmap2)
            log = 'pselect_test_audit.log'
            self.run_tssb_wrapper("preselect_test.txt",log)
            ret = AuditParser(log)    
        
        os.chdir("..")
        return ret
    
    def rescan_iteration(self,year):
        if os.path.exists('%d/pselect_test_audit.log' % year):
            audfile = '%d/pselect_test_audit.log' % year
        else:
            audfile = '%d/pselect_audit.log' % year
            
        if not os.path.exists(audfile):
            raise Exception('Cannot rescan - %s does not exist!' % audfile)
        return AuditParser(audfile)
        
if __name__ == '__main__':
    s = SimMain()
    sys.exit(s.main())
