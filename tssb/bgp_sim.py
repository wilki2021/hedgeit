'''
Created on May 13, 2013

@author: rtw
'''
from paudit import *
from pvars import *
from runtssb import run_tssb
import getopt
import os
import shutil
import glob

def usage():
    print '''
usage: subgroup_stability <year-start> <year-end>
    
    Options:  None
'''
    
def apply_script_template(template, output, varmap):
    assert(os.path.exists(template))
    if os.path.exists(output):
        os.remove(output)
    shutil.copyfile(template, output)
    for (var,value) in varmap.iteritems():
        cmd = 'sed -i "s/<%s>/%s/g" %s' % (var,value,output)
        os.system(cmd)
    # for some reason sed from GnuWin32 leaves temp files around when
    # the -i option is used
    for f in glob.glob('sed*'):
        os.remove(f)
        
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
        'YEAR_START' : '%s' % (year - lag),
        'YEAR_END' : '%s' % year,
        'YEAR_MAX' : '2013',
        'TEST_START' : '%s' % (year + 1),
        'TEST_END' : '%s' % (year + 1),
        'VAR_LIST' : 'varlist.txt',
        'DB_NAME'  : 'vardb'}
    for s in stage1_scripts:
        apply_script_template(os.path.join("..",s), s, varmap)

    # first run the subsample test to narrow predictors
    log = 'sub_audit.log'
    run_tssb_wrapper(stage1_scripts[0],log)
    sub = AuditParser(log)
    varfile = open('varlist.txt','w') # must match VAR_LIST entry above
    varlist = sub.selstats.list_all_gt(3.0)   
    for var in varlist:
        varfile.write('%s: %s\r\n' % (var[0],vars_.vars()[var[0]]))
    varfile.close()    

    # now create our database
    log = 'create_audit.log'
    run_tssb_wrapper(stage1_scripts[1],log)
    
    varmap['VAR_1'] = varlist[0][0]
    varmap['VAR_N'] = varlist[-1][0]
    apply_script_template(os.path.join("..",'findgroups.txt'), 'findgroups.txt', varmap)

    # now get our groups
    log = 'fgroup_audit.log'
    run_tssb_wrapper(stage2_scripts[0],log)
    groups = AuditParser(log)
    for (group,stats) in groups.fgstats.groups().iteritems():
        groupname = 'GROUP%s' % group
        varspec = ''
        for var in stats.get_vars():
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
            for (model,wfmstats) in sorted(res.wfstats.models().iteritems()):
                line = line + ",%s" % model
            wf.write('%s\n' % line)

        line = '%s' % y 
        for (model,wfmstats) in sorted(res.wfstats.models().iteritems()):
            line = line + ",%0.4f" % wfmstats.long_only_imp
        wf.write('%s\n' % line)
    wf.close()            
            