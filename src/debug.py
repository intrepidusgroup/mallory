from SimpleXMLRPCServer import SimpleXMLRPCServer
from observer import Subject
import Queue
import logging
import UserDict
import binascii
import base64
import pickle

class DebugEvent(UserDict.UserDict):
    def __init__(self):
        self.eventid = ""
        self.event = ""        
        self.source = ""
        self.destination = ""
        self.data = ""
        self.direction = ""
        self.crc = 0
        
    def fromdict(self, dict):        
        for key in self.__dict__.keys():
            if key in dict:
                self.__dict__[key] = dict[key]                    
        return self

    def __str__(self):
        s = "eventid=%s,event=%s,source=%s,destination=%s,data=%s,dir=%s,crc=%08x" % \
        (self.eventid, self.event, self.source, self.destination, 
         repr(self.data[:24]),self.direction, self.crc)
        return s

class Debugger(Subject):
    def __init__(self, rules = []):
        Subject.__init__(self)
        self.debugq = Queue.Queue()
        self.debugon = False
        self.log = logging.getLogger("mallorymain")
        self.rules = rules

    def rpcserver(self):
        """
        rpcserver is intended to be launched as a separate thread. This class
        will launch an RPC server that can pass and receive debugging events
        to debugging clients.
        """
        try:
            self.log.info("Debugger: starting XML RPC Server")
            server = SimpleXMLRPCServer(addr=("localhost", 20757), logRequests=False)
            server.register_function(self.setdebug, "setdebug")
            server.register_function(self.getdebugq, "getdebugq")
            server.register_function(self.send_de, "send_de")
            server.register_function(self.getrules, "getrules")
            server.register_function(self.updaterules, "updaterules")

            server.serve_forever()
        except:
            self.log.error("Debugger: rpcserver: error connecting to remote")
            self.log.error(sys.exc_info())


    def setdebug(self, state):
        self.log.debug("Debugger: self.debugon being set to: %s" % state)       
        if state:
            self.debugon = True
        else:
            self.debugon = False            
        self.notify(event="setdebug", state=self.debugon)
        
        return ""
    
    def getdebugq(self):
        """Clear the debug queue and send them off to the client"""
        debug_events = []
        while not self.debugq.empty():
            de = self.debugq.get()
#            self.log.debug("Debugger: got DebugEvent: %s:%s" % 
#                           (de.__class__,de))

            debug_events.append(de)
        return debug_events       
        
    def update(self, publisher, **kwargs):
        #print "[*] Debugger: got update event. Not ignoring it."
        event = kwargs["event"]
                        
        if event == "debug":                    
#            self.log.debug("Debugger: update: adding event to debug queue")
            de = DebugEvent()
            de.eventid = kwargs["eventid"]
            de.event = kwargs["event"]
            de.source = kwargs["src"]
            de.destination = kwargs["dest"]
            de.data = kwargs["thedata"].encode("string-escape")
            de.direction = kwargs["direction"]
            de.crc = binascii.crc32(kwargs["thedata"])
        
            self.log.debug("Debug.update: newevent: %08x [eventid:%s]" % (binascii.crc32(kwargs["thedata"]), kwargs["eventid"]))
            
            self.debugq.put(de)
             
    def send_de(self, debugevent):
        """Notify subscribers of an incoming debug event"""
        
        # Wrap it up nice and safe for transport to the debugger
        debugevent['data'] = debugevent['data'].decode("string-escape")                
        de = DebugEvent().fromdict(debugevent)
        localcrc = binascii.crc32(debugevent['data'])
        
        if de.crc != localcrc:
            self.log.error("Debugger: CRC MISMATCH: expecting %08x got %08x" %
                           (de.crc, localcrc))
            
        self.log.debug("Debug.send_de: eventback: %08x [eventid:%s]" % (localcrc, debugevent["eventid"]))
        
        self.notify(event="debugevent",debugevent=de)
        
        self.log.debug("Debug.send_de: Notify for [eventid:%s]" % (debugevent["eventid"]))
        #self.log.debug("Debugger: send_de: got debugevent %s: " %  (debugevent))
#        self.log.debug("Debugger: send_de: got debugevent %s: " %  (de))
        return ""
    
    def getrules(self):        
        if self.rules is None:
            return []
        
        for rule in self.rules:
            self.log.debug("Debugger.getrules: %s" % (str(rule)))

        self.log.debug("Debugger.getrules: client requested rules -  %s" % (self.rules))
        #p_rules = []
            
        #for i in self.rules:
        #   p_rules.append(pickle.dumps(i))
        #self.log.debug(p_rules)
        e = base64.b64encode(pickle.dumps(self.rules))
        
        return e
    
    def updaterules(self, rulearray):
        d = base64.b64decode(rulearray)
        unpickled = pickle.loads(d)
        self.rules = unpickled
        
        for rule in self.rules:
            self.log.debug("Debugger.updaterules: %s" % (str(rule)))
#            if rule.action.name == "muck":
#                self.log.debug("Debugger.updaterules: %s" % (rule.action.mucks))
#                for muck in rule.action.mucks:
#                    self.log.debug("Debugger.updaterules.muck: %s" %(binascii.hexlify(muck)))
                
            
        self.log.debug("Debugger.updaterules: %s" % (unpickled))
        self.notify(event="updaterules", rules=unpickled)
        
        return ""             
