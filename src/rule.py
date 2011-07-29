import muckpipe
import binascii
import fuzz

class RuleAction(object):
    def __init__(self):
        self.name = "base"
    
    def execute(self, **kwargs):
        pass
    
class Fuzz(RuleAction):
    def __init__(self, bit_flip_percentage=20, bof_injection_percentage=20, bit_flip_density=7):
        RuleAction.__init__(self)
        self.name = "fuzz"
        self.bfp = bit_flip_percentage
        self.bip = bof_injection_percentage
        self.bfd = bit_flip_density
        
    def execute(self, **kwargs):
        if "data" in kwargs:
            data = kwargs["data"]
        else:
            return ""
        return fuzz.fuzz(data,self.bfp,self.bip)

class Muck(RuleAction):
    def __init__(self, mucks = []):
        RuleAction.__init__(self)
        self.name = "muck"
        self.mucks = mucks
        
    def execute(self, **kwargs):        
        if "data" in kwargs:
            data = kwargs["data"]
        else:
            return ""
        
#        for muck in self.mucks:
#            print ("[STDOUT] Muck.execute: str:%s repr:%s hex:%s" % 
#                   (muck, repr(muck), binascii.hexlify(muck)))
            
        self.mp = muckpipe.MuckPipe("").fromlist(self.mucks)
        
        self.mp.data = data
                
        return self.mp.muck()
    
    def __str__(self):
        muck_str = ("<Muck %s>" % self.mucks)
        
        return muck_str
    
class Debug(RuleAction):
    def __init__(self):
        RuleAction.__init__(self)
        self.name = "debug"
        
    def execute(self, **kwargs):
        return True

class Nothing(RuleAction):
    def __init__(self):
        self.name = "nothing"
        RuleAction.__init__(self)
        
        
class Data(object):
    def __init__(self):
        self.data = ""
        
             
class Rule(object):
    """
    A Rule is an entity that triggers when certain matching criteria are met. These
    criteria are when the rule is triggered. Each rule has a rule action that
    determines what happens when the rule is triggered. Generally rule actions
    are for special activities in Mallory (such as debugging) or for stateless
    data modification, such as data mangling or fuzzing. 
    """
    def __init__(self, name, **kargs):
        self.init_invariants()
        self.init_variants(**kargs)
        
    
    def make_bool(self, s):
        if isinstance(s, str) and len(s) > 0 and s.lower() == "true":
            return True
        else:
            return False
     
    def make_port(self, x):
        if (isinstance(x,str) and x != "-1") or \
            (isinstance(x,int) and not x == -1):
            return str(x)
        else:
            return "*"
        
    def make_str(self, x):
        if isinstance(x,str) and len(x) > 0:
            return x
        else:
            return "*"
         
    def init_variants(self, **kargs):                
        self.matching = []
        
        self.name = str(kargs.get('name', ""))
        self.passthru = self.make_bool(str(kargs.get('passthru', False)))                
        # The seemingly redundant string calls are important for PyQt based code
        self.addr = self.make_str(str(kargs.get('addr', "*")))
        self.port = self.make_port(str(kargs.get('port', "*")))
        self.direction = self.make_str(str(kargs.get('direction', "*")))
        self.proto = self.make_str(str(kargs.get('proto', "*")))
        self.payload = self.make_str(str(kargs.get('payload', "*")))
        self.action = kargs.get('action', Nothing())
                
        # update our matching criteria
        self.update_matching_crit()


    
    def init_invariants(self):
        self.matching_funcs ={"addr":self.addrmatch,
                             "port":self.portmatch,
                             "direction":self.dirmatch,
                             "port":self.portmatch,
                             "payload":self.payloadmatch,
                             #"proto":self.protomatch
                            } 
        # set the available matching types
        self.matching_crit = ['addr','port','proto','direction','payload',]
        # matching will be the functions we perform when we need to match a rule
        # a list will give an ordered/precedent matching capability
        self.matching = []
        
    def update_matching_crit(self, ordering=[]):
        # if we want to match in a particulart order, we arranged the 
        # matching like that, if and only if we can match on that criteria
        o_matching_crit = [i for i in ordering if i in set(self.matching_crit)]
        if len(o_matching_crit) == 0:
            o_matching_crit = self.matching_crit
        # put our ordered list in to the matching list
        # if it is not empty.  emptiness returns true by
        # default, but if this changes, we need to change the loop below
        for crit in o_matching_crit:
            #print "Rule: %s checking for %s criteria"%(self.name,crit)
            value = self.__dict__.get(crit, "*")
            if value == "*":
               #print "Rule %s: %s has a wild card or no matching criteria"%(self.name,crit)
               continue
            #print "Rule %s adding for %s: %s"%(self.name,crit, value)
            self.matching.append(crit)
            

    def fromdict(self, dict):
        for key in self.__dict__.keys():
            if key in dict: # and key is not "action":
                self.__dict__[key] = dict[key] 
        self.update_matching_crit()                   
        return self
            
    def quickrule(self, addr="*", port="*", direction="*", action=Nothing()):
        #print "Quick Rule called with the following: "
        #print "addr: %s, port: %s, direction: %s"%(addr, str(port), direction)
        self.addr = self.make_str(addr)
        self.port = self.make_port(port)
        self.direction = self.make_str(direction)
        self.update_matching_crit()
        self.action = action
        self.passthru = False
        
    def match(self, **kargs):#addr="", port="", direction="",payload=""):
        #print "kargs: ",kargs
        #print "kargs keys: ",kargs.keys()
        #print "crit: ", self.matching
        #print "matching functions: ",self.matching_funcs
        for crit in self.matching:
            #print "Performint a match on crit: %s"%(crit)
            if kargs.get(crit,None) is None:
               #print "Performint a match on crit: %s not found in the arguments, skipping"%(crit)
               continue
            # return false if we cant match the criteria
            elif not crit in self.matching_funcs:
               print "Performing a match on crit: %s not found in the matching funcs, skipping"%(crit)
               continue
            # get the arg, func, determine if it was a match
            # TODO: interesting feature is ability to do
            # confidence and fuzzy/partial matching
            arg = kargs.get(crit)
            
            # Convert everything to a string (catches ports and others)
            if isinstance(arg, int) or isinstance(arg,long):
               arg = str(arg)
            
            match_func = self.matching_funcs.get(crit)
            #print "Performint a match on crit: %s with argument %s"%(crit, arg)
            if not match_func(arg):
                #print "**********Failed the match "
                return False
        return True
    
    def payloadmatch(self, payload):
        # partial match at the moment
        if self.payload == "*":
            return True
        return payload.find(self.payload) > -1
        
    def addrmatch(self, addr):
        if self.addr == "*":
            return True
        return self.addr == addr
    
    def portmatch(self, port):
        if self.port == "*":
            return True
        return self.port == port
    
    def dirmatch(self, dir):
        if self.direction == "*":
            return True
        x = self.direction.lower() == dir.lower()
        print "Dirmatch: %s" % (x)
        return x
    
    def __getstate__(self):
        odict = self.__dict__.copy()   
        del odict['matching_funcs']
        return odict
    
    def __setstate__(self, mdict):
        self.init_invariants()
        self.init_variants(**mdict)
        #self.fromdict(mdict)
       

    def __str__(self):
        crit = []
        for i in self.matching_crit:
            crit.append( "%s:%s"%(i, self.__dict__.get(i,"*")))
        
        crit.append("passthru:%s" % (str(self.passthru)))
        
        return "<class Rule %s -- %s (%s)>" % \
            (self.name, " ".join(crit), self.action)
            
def test():
    s2c = "s2c"
    c2s = "c2s"
    
    # Create test data
    data = [
            {"addr":"192.168.1.60","port":80,"direction":s2c, "matches":"bcdf"}, # b, c, d
            {"addr":"192.168.1.60","port":22,"direction":c2s, "matches":"cef"}, # c, e      
            {"addr":"192.168.1.60","port":80,"direction":c2s, "matches":"abcdef"}, # a, b, c, d, e       
            {"addr":"192.168.1.60","port":80,"direction":c2s, "matches":"abcdef"}, # a, b, c, d, e
            {"addr":"192.168.1.100","port":80,"direction":c2s, "matches":"def"}, # d, e
            {"addr":"192.168.1.100","port":22,"direction":c2s, "matches":"ef"}, # e            
           ] 

    #data = [{"addr":"192.168.1.60","port":80,"direction":s2c}]
        
    # Create some test rules
    a = Rule("a") 
    a.quickrule("192.168.1.60", 80, c2s)
    b = Rule("b")
    b.quickrule("192.168.1.60", 80, "")
    c = Rule("c")
    c.quickrule("192.168.1.60", -1, "")
    d = Rule("d")
    d.quickrule("", 80, "")
    e = Rule("e")
    e.quickrule("", -1, c2s)
    f = Rule("f").fromdict({})

    rules = [a, b, c, d, e, f]
    
    for d in data:
        print "Data: %s" % (d) 
        matches = ""
        for rule in rules:
            matched = rule.match(**d)#d["addr"], d["port"], d["direction"])
            if matched:
                matches += rule.name
                print "     matched %s" % (str(rule))
                
        if matches == d["matches"]:
            print "RULE PASSED"
        else:
            print "RULE FAILED"
            
        print "------------"
            

    print "\n\n\n***** action determination *****\n\n\n"
    
    for d in data:
        print "Data: %s" % (d) 
        for rule in rules:
            matched = rule.match(**d)#d["addr"], d["port"], d["direction"])
            if matched:
                print "would take action from %s" % (str(rule))
                break
        print "------------"
     
    mucklist = ["[a-z]/A/5","[0-9]/0/2"," /./g"]
    data =  "Letters and Numbers 999"
    x = Muck(mucklist)
    result = x.execute(data=data) 
    if result == "LAAAAAs.and.Numbers.009":
        print "MUCK PASSED input was %s on data '%s' with result:'%s'" % \
            (mucklist, data, result)
    else:
        print "(mucklist=%s:data=%s:result=%s)" % (mucklist, data, result)
        print "MUCK FAILED"

"""
    a.addr = "192.168.1.60"
    a.port = "80"
    a.direction = "c2s"

    b.addr = "192.168.1.60"
    b.port = "80"
        
    c.addr = "192.168.1.60"
    
    d.port = "80"
    
    e.direction = "c2s"
"""

        
