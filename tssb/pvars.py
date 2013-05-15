'''
Created on May 14, 2013

@author: bwilkinson
'''
import sys

class VarParser(object):
    '''
    VarParser parses a list of TSSB indicator definitions.  The syntax is 
    assumed as follows:
    
      ; anything after a semicolon is a comment
      <whitespace> is ignored
    any non-empty line (after stripping comments and whitespace) must be
    have exactly one colon that splits the line into an indicator name
    and the indicator definition
      <indicator name> : <indicator defn>
    '''

    def __init__(self,filename):
        '''
        Constructor
        '''
        self._fname = filename
        self._vars = {}
        self.parse()
        
    def parse(self):
        f = open(self._fname)
        for l in f.readlines():
            # first strip any comments
            if l.find(';'):
                l = l[:l.find(';')]
            # now get rid of any extraneous whitespace
            l = l.strip()
            
            # Now if anything left it should be a variable of the form
            # <var name>: <var defn>
            if len(l):
                parts = l.split(':')
                if len(parts) != 2:
                    print 'Error while parsing ^%s^' % l
                varname = parts[0].strip()
                vardefn = parts[1].strip()
                self._vars[varname] = vardefn
                
    def vars(self):
        return self._vars
    
if __name__ == '__main__':
    v = VarParser(sys.argv[1])
    for (var,defn) in v.vars().iteritems():
        print 'var:%s,defn:%s' % (var,defn)            