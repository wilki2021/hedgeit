'''
Created on May 10, 2013

@author: rtw
'''
import re
import sys

class SelectionStats(object):
    def __init__(self):
        self._vars = {}
        
    def add_model_variable(self,model,variable,pct):
        if not self._vars.has_key(variable):
            self._vars[variable] = []
        self._vars[variable].append(pct)
        
    def list_all_gt(self, threshold):
        ret = []
        for (var,pctlist) in self._vars.iteritems():
            avg = sum(pctlist) / len(pctlist) 
            if (avg >= threshold):
                ret.append((var,avg))
                
        # now we want to sort this by decreasing pct
        ret = sorted(ret, key=lambda x: x[1],reverse=True)
                
        return ret
            
class WalkForwardModelStats(object):
    '''
    struct-like object to stort the statistics we grab
    '''
    
    def __init__(self):
        self.target_grand_mean = 0.0
        self.total_cases       = 0
        self.num_above_high    = 0
        self.num_below_low     = 0
        self.mean_above_high   = 0.0
        self.mean_below_low    = 0.0
        self.roc_area          = 0.0
        self.long_only_imp     = 0.0
        self.short_only_imp    = 0.0
        self.long_total_ret    = 0.0
        self.long_maxdd        = 0.0
        self.short_total_ret   = 0.0
        self.short_maxdd       = 0.0
        
    def __str__(self, *args, **kwargs):
        ret = ''
        for i in self.__dict__:
            ret = ret + '%s: %s\n' % (i, self.__dict__[i])
        return ret[:-1]

class WalkForwardStats(object):
    def __init__(self):
        self._models = {}
        
    def add_model(self, model, wfmstats):
        self._models[model] = wfmstats
        
    def get_model(self, model):
        return self._models[model] 

    def models(self):
        return self._models 
            
class AuditParser(object):
    '''
    classdocs
    '''

    def __init__(self, filename):
        '''
        Constructor
        '''
        self._filename = filename
        self._file = open(filename)
        self._lineno = 0

        # set up patterns that designate different sections        
        self._selstatspatt = re.compile('^Selection statistics for model (\w+)$')
        self.selstats = SelectionStats()

        self._wfstatspatt = re.compile('.*Walkforward is complete\.  Summary.*')
        self.wfstats = WalkForwardStats()

        self._termpatt  = re.compile('# # # # # # # # # # # # # # # # # # # # # # #')
        
        self.parse()
        
    def parse(self):
        line = self._get_line()
        while line != None:
            #print line
            res1 = self._selstatspatt.match(line)
            res2 = self._wfstatspatt.match(line)
            if res1:
                self.parse_selstats(res1)
            elif res2:
                self.parse_wfstats()
                
            line = self._get_line()
        
    def parse_wfstats(self):
        print 'parsing walk-forward summary...'
        modelstart = re.compile('^Model (\w+).*')
        line = self._get_line()
        while line != None and not self._termpatt.match(line):
            res1 = modelstart.match(line)
            if res1:
                wfmstats = self.parse_wfmodel(res1)
                self.wfstats.add_model(res1.group(1), wfmstats)
                
            line = self._get_line()
    
    def parse_wfmodel(self, mat):        
        print 'parsing walk-forward statistics for model %s' % mat.group(1)
        
        wfmstats = WalkForwardModelStats()
        patt1 = re.compile('^Pooled out-of-sample.*')
        patt2 = re.compile('^Target grand mean = ([-\.\d]+)')
        patt3 = re.compile('^(\d+) of (\d+) cases.*above outer high.*Mean = ([-\.\d]+)')
        patt4 = re.compile('^(\d+) of (\d+) cases.*below outer low.*Mean = ([-\.\d]+)')
        patt5 = re.compile('.*ROC area = ([-\.\d]+)')
        patt6 = re.compile('^Outer (\w+).*Improvement Ratio = ([-\.\d]+)')
        patt7 = re.compile('^.* (\w+) trades; total return = ([-\.\d]+)')
        patt8 = re.compile('^Max drawdown = (\d+\.\d+)')
        term  = re.compile('vvvvvvvvvvvvvvvvvvvvvvvvv')
        pstate = 0
        line = self._get_line()
        while line != None and not term.match(line) and not self._termpatt.match(line):
            if pstate == 0 and patt1.match(line):
                pstate = 1
            elif pstate == 1 and patt2.match(line):
                wfmstats.target_grand_mean = float(patt2.match(line).group(1))                
                pstate = 2
            elif pstate == 2:
                mat1 = patt3.match(line)
                wfmstats.num_above_high = int(mat1.group(1))
                wfmstats.total_cases = int(mat1.group(2))
                wfmstats.mean_above_high = float(mat1.group(3))
                
                mat2 = patt4.match(self._get_line())
                wfmstats.num_below_low = int(mat2.group(1))
                wfmstats.mean_below_low = float(mat2.group(3))
                pstate = 3
            elif pstate == 3:
                mat = patt5.match(line)
                wfmstats.roc_area = float(mat.group(1))
                pstate = 4
            elif pstate == 4 and patt6.match(line):
                mat1 = patt6.match(line) 
                assert(mat1.group(1) == 'long')
                wfmstats.long_only_imp = float(mat1.group(2))

                mat2 = patt6.match(self._get_line()) 
                assert(mat2.group(1) == 'short')
                wfmstats.short_only_imp = float(mat2.group(2))
                pstate = 5
            elif pstate == 5 and patt7.match(line):
                mat1 = patt7.match(line)
                assert(mat1.group(1) == 'long')
                wfmstats.long_total_ret = float(mat1.group(2))
                
                mat2 = patt8.match(self._get_line())
                wfmstats.long_maxdd = float(mat2.group(1))

                line = self._get_line()
                mat1 = patt7.match(line)
                assert(mat1.group(1) == 'short')
                wfmstats.short_total_ret = float(mat1.group(2))
                
                mat2 = patt8.match(self._get_line())
                wfmstats.short_maxdd = float(mat2.group(1))
                
            line = self._get_line()
        
        return wfmstats
    
    def parse_selstats(self, mat):
        print 'parsing selection statistics for model %s' % mat.group(1)
        
        patt1 = re.compile('Variables selected...')
        patt2 = re.compile('Name   Percent')
        
        pstate = 0
        
        # the selection statistics section has two fixed lines we need to see 
        # before we start collecting variable names
        line = self._get_line()
        while line != None and not self._termpatt.match(line):
            if pstate == 0 and patt1.match(line):
                pstate = 1
            elif pstate == 1 and patt2.match(line):
                pstate = 2
            elif pstate == 2:
                if line:
                    (variable, pct) = line.split()[0], line.split()[1]
                    self.selstats.add_model_variable(mat.group(1), variable, float(pct))
            line = self._get_line()
        
    def _get_line(self):
        line = self._file.readline()
        if line:
            ++self._lineno
            return line.strip()
        else:
            return None
        
if __name__ == '__main__':
    a = AuditParser(sys.argv[1])
    print "Selection Statistics Summary:"
    for var in a.selstats.list_all_gt(2.5):
        print '%s,%0.2f%%' % (var[0],var[1])

    for (model,wfmstats) in a.wfstats.models().iteritems():
        print 'Model %s walk-forward stats:' % model
        print wfmstats