import re
import logging

class Muckr(object):
    def __init__(self, pattern = None, repl = None, count = 0):
        self.pattern = pattern
        self.repl = repl
        self.count = count
        self.log = logging.getLogger("mallorymain")
    
    def muck(self, data):
        #print("Muckr.muck: self.pattern: %s, self.repl: %s, self.count:%s" % (self.pattern, repr(self.repl), str(self.count)))
        x = re.sub(self.pattern, self.repl, data, self.count)
        #print("Muckr.muck: dataout: %s" % repr(x))
        return x
        

    def find_terms(self, muck_string, sep_chr, num_terms, chr_idx = -1):
        """
        Find the "terms" (search, replace and count) for this regex.
        
        @param muck_string: The muck expression to be parsed
        @param sep_chr: Separator character to split terms on
        @param num_terms: Number of terms to look for
        @param char_idx: defaults to -1. The position to start counting. Note
        unlike most string functions, you must index one  before the
        start character you wish to search. The default is to parse the entire
        muck_string you probably won't change that.
        
        @return: Array of positions in the string where sep_chr was found. Array
        must have num_terms number of elements, otherwise the expression should
        be considered invalid.
        """        
        sep = []

        while chr_idx < len(muck_string)-1:
            chr_idx += 1
            
            if muck_string[chr_idx] == "\\":
                chr_idx += 1  # Skip next char, it can't be a separator
                continue
            
            if muck_string[chr_idx] == sep_chr:
                sep.append(chr_idx)
                            
            if len(sep) == num_terms:
                break
                
        return sep
            
    def fromstr(self, muck):
        self.pattern = ""
        self.repl = ""
        self.count = 0
        num_seps = 2
        
        seps = self.find_terms(muck, "/", num_seps)
        
        if(len(seps) != 2):
            self.log.info("Muckr.fromstr(): Malformed muck expression."
                          "Check your muck syntax: '%s'" % (muck))
            return self
        
        self.pattern = muck[0:seps[0]]
        self.repl = muck[seps[0]+1:seps[1]]
        tmp_count = muck[seps[1]+1:]
        
        if tmp_count == 'g':
            self.count = 0
        try:
            self.count = int(tmp_count)
        except:
            self.count = 0
        
        return self

    def __str__(self):
        return "<Muckr pattern:'%s' repl:'%s' count:'%d'>" % (self.pattern, self.repl, self.count)
    
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

if __name__ == '__main__':
    # Muckpipe testing
    
    print "[STDOUT] MUCK TESTING"
    import binascii
    mucks = []
    mucks.append(r"\/B/g") # A/B/g
    mucks.append(r"\\/B/g") # A/B/g
    mucks.append(r"\\\/B/g") # A/B/g
    mucks.append(r"\\\\/B/g") # A/B/g
    mucks.append(r"//g") # A/B/g
    mucks.append(r"/////////") # A/B/g
    mucks.append(r"\//FSLASH/g") #\//FSLASH/g
    mucks.append(r"\x5c\\/BSLASH/g")
    mucks.append(r"asd\/asdf\/asdfasdf\/asdfsadf\\/asdfasdf/asdf")
    
    s = "ABCDEFGHIJKLMN"        
    
    for muck in mucks:
        print ("[STDOUT] Muck.execute: str:%s repr:%s hex:%s" % 
               (muck, repr(muck), binascii.hexlify(muck)))    
        
    mp = MuckPipe(s)
    mp.fromlist(mucks)
    
    print mp.muck()
    