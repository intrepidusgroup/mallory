import re
import logging

class Muckr(object):
    def __init__(self, pattern = None, repl = None, count = 0):
        self.pattern = pattern
        self.repl = repl
        self.count = count
    
    def muck(self, data):
        #print("Muckr.muck: datain: %s" % repr(data))
        x = re.sub(self.pattern, self.repl, data, self.count)
        #print("Muckr.muck: dataout: %s" % repr(x))
        return x

    def fromstr(self, muck):
        # Find a forward slash that is NOT followed by a backslash
        # Yes, you need four backslashes just for ONE backslash in a regex
        regx = "(?<!\\\\)/"
        match = re.search(regx, muck)
        self.pattern = muck[:match.start(0)]
        str_nolookfor = muck[match.start(0)+1:]
        match = re.search(regx, str_nolookfor)
        self.repl = str_nolookfor[:match.start(0)]
        count = str_nolookfor[match.start(0)+1]
        
        if count == 'g':
            self.count = 0
        else:
            self.count = int(count)
                
        return self

    def __str__(self):
        return "<Muckr pattern:%s repl:%s count:%d>" % (self.pattern, self.repl, self.count)
    
class MuckPipe(object):
    """    
    Example usage:
    
    data = "GET / HTTP/1.1"
    mp = MuckPipe(data)
    mp.append_str("\//fslash/g")
    mp.append_str("T/t/2")
    print mp.muck()
    Result: GEt fslash HtTPfslash1.1
    """
    def __init__(self, data, mucks = []):
        self.mucks = mucks
        self.data = data
        
    def muck(self):
        for muckr in self.mucks:
            self.data = muckr.muck(self.data)
        return self.data
        
    def mucks(self):
        return self.mucks 
        
    def data(self):
        return self.data
    
    def append(self, muckr):
        self.mucks.append(muckr)
        
    def append_str(self, mstr):
        self.mucks.append(Muckr().fromstr(mstr))
        
    def fromlist(self, muckrlist):
        self.mucks = []
        for muckr in muckrlist:
            self.append_str(muckr)
        return self
            
    def __str__(self):
        return self.data