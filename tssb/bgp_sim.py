'''
Created on May 13, 2013

@author: rtw
'''
from tssbutil.paudit import *
from tssbutil.pvars import *
from tssbutil.runtssb import run_tssb
from tssbutil.sedlite import sed_lite
import getopt
import os
import shutil
import sys

def usage():
    print '''
usage: outer_wf.py <year-start> <year-end>

    Performs an "outer" walk-forward analysis loop across a series of
    years per the command-line arguments.  Each "inner" walk-forward 
    is a discrete (and currently hard-coded) series of steps to select
    a smaller indicator set from a larger one and then select and train
    a series of models from them.
    
    Parameters:
        <year-start>  - integer, year to start the outer walk forward.
                        NOTE - for any given walk-forward year, that
                        year is included in the training set and the 
                        subsequent year is treated as the test/validation
                        period.
        <year-end>    - integer, year to end the outer walk forward.
    Options:  None
'''
    
def apply_script_template(template, output, varmap):
    assert(os.path.exists(template))
    if os.path.exists(output):
        os.remove(output)
    sed_lite(template, output, varmap)
        
def run_tssb_wrapper(script, log):
    tssb = 'C:\\Users\\bwilkinson.Calpont\\TSSB\\tssb64.exe'
    filepath = os.path.join(os.getcwd(), script)
    run_tssb(filepath,tssb_path=tssb)

    if not os.path.exists('AUDIT.LOG'):
        raise Exception("TSSB did not appear to write an AUDIT.log file!!")
    
    if os.path.exists(log):
        os.remove(log)
    os.rename('AUDIT.LOG',log)
    
stage1_scripts = ['subsample.txt','createdb.txt']
stage2_scripts = ['findgroups.txt','preselect.txt']

def run_iteration(year, vars_, lag):
    print 'Running iteration for year %d' % year
    
    workdir = '%s' % year
    if os.path.exists(workdir):
        shutil.rmtree(workdir)
    os.mkdir(workdir)
        
    os.chdir(workdir)
    
    # first instantiate our each script files
    varmap = {
        '<YEAR_START>' : '%s' % (year - lag),
        '<YEAR_END>' : '%s' % year,
        '<YEAR_MAX>' : '2013',
        '<TEST_START>' : '%s' % (year + 1),
        '<TEST_END>' : '%s' % (year + 1),
        '<VAR_LIST>' : 'varlist.txt',
        '<DB_NAME>'  : 'vardb'}
    for s in stage1_scripts:
        apply_script_template(os.path.join("..",s), s, varmap)

    # first run the subsample test to narrow predictors
    log = 'sub_audit.log'
    run_tssb_wrapper(stage1_scripts[0],log)
    sub = AuditParser(log)
    varfile = open('varlist.txt','w') # must match VAR_LIST entry above
    varlist = sub.tssbrun().selection_stats().list_all_gt(3.0)   
    for var in varlist:
        varfile.write('%s: %s\r\n' % (var[0],vars_.vars()[var[0]]))
    varfile.close()    

    # now create our database
    log = 'create_audit.log'
    run_tssb_wrapper(stage1_scripts[1],log)
    
    varmap['<VAR_1>'] = varlist[0][0]
    varmap['<VAR_N>'] = varlist[-1][0]
    apply_script_template(os.path.join("..",'findgroups.txt'), 'findgroups.txt', varmap)

    # now get our groups
    log = 'fgroup_audit.log'
    run_tssb_wrapper(stage2_scripts[0],log)
    groups = AuditParser(log)
    fold = groups.tssbrun().folds()[0]
    for (name,modeliter) in fold.models().iteritems():
        groupname = '<GROUP%s>' % name
        varspec = ''
        for var in modeliter.defn().get_factors():
            if var[0] != 'CONSTANT':
                varspec = varspec + ' ' + var[0]
        varmap[groupname] = varspec
    apply_script_template(os.path.join("..",'preselect.txt'), 'preselect.txt', varmap)

    # finally execute against our test year
    log = 'pselect_audit.log'
    run_tssb_wrapper("preselect.txt",log)
    ret = AuditParser(log)
    
    os.chdir("..")
    return ret
        
if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], "", [])
    except getopt.GetoptError as err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)

    for o, a in opts:
        if True:
            # we don't support any options so anything here is a problem.
            usage()
            sys.exit(1)
                         
    if len(args) != 2:
        print 'Not enough arguments to subgroup_stability!'
        usage()
        sys.exit(1)
        
    yearstart = int(args[0])
    yearend = int(args[1])

    for s in stage1_scripts:
        if not os.path.exists(s):
            print 'Error: must have the script template %s in current directory' % s
    for s in stage2_scripts:
        if not os.path.exists(s):
            print 'Error: must have the script template %s in current directory' % s

    vars_ = VarParser('TREND_VOLATILITY3.TXT')        
    
    wf = open("perf.csv","w")      
    headers = False
    for y in range(yearstart, yearend+1):
        # we get back the results from 1 walk-forward year
        res = run_iteration(y, vars_, 13)

        if not headers:
            headers = True
            line = 'year'
            for (model,wfmstats) in sorted(res.tssbrun().walkforward_summ().iteritems()):
                line = line + ",%s" % model
            wf.write('%s\n' % line)

        line = '%s' % y 
        for (model,wfmstats) in sorted(res.tssbrun().walkforward_summ().iteritems()):
            line = line + ",%0.4f" % wfmstats.long_only_imp
        wf.write('%s\n' % line)
    wf.close()            
            