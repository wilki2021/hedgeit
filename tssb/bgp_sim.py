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
        print 'Executing: %s' %cmd
        os.system(cmd)
        
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
stage2_scripts = ['findgroups.txt']

def run_iteration(year, vars):
    print 'Running iteration for year %d' % year
    
    workdir = '%s' % year
    if not os.path.exists(workdir):
        os.mkdir(workdir)
    os.chdir(workdir)
    
    # first instantiate our each script files
    varmap = {
        'YEAR_END' : '%s' % year,
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
        varfile.write('%s: %s\r\n' % (var[0],vars.vars()[var[0]]))
    varfile.close()    

    # now create our database
    log = 'create_audit.log'
    run_tssb_wrapper(stage1_scripts[1],log)
    
    varmap['VAR_1'] = varlist[0][0]
    varmap['VAR_N'] = varlist[-1][0]
    for s in stage2_scripts:
        apply_script_template(os.path.join("..",s), s, varmap)

    # now get our groups
    log = 'fgroup_audit.log'
    run_tssb_wrapper(stage2_scripts[0],log)
    
    os.chdir("..")
        
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

    vars = VarParser('TREND_VOLATILITY3.TXT')                
    for y in range(yearstart, yearend+1):
        run_iteration(y, vars)
