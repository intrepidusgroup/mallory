from observer import Subject
import Pyro.core
import Queue
import logging
import UserDict
import binascii
import base64
import pickle

# import Pyro here

class DebugEvent(object):
    """
    Encapsulate a debugging event.
    
    eventid is string and a UUID
    event is string and an action specifier
    source is string and the source IP:port
    destination is string and the destination IP:port
    direction is string and c2s (client to server) or s2c (server to client)
    crc is internal and checks for consistency across the network 
    """
    def __init__(self):
        self.eventid = ""
        self.event = ""        
        self.source = ""
        self.destination = ""
        self.data = ""
        self.direction = ""
        self.crc = 0
        
#    def fromdict(self, dict):
#        for key in self.__dict__.keys():
#            if key in dict:
#                self.__dict__[key] = dict[key]
#        return self

    def __str__(self):
        s = (("eventid=%s,event=%s,source=%s,destination=%s,data=%s,dir=%s,"
             "crc=%08x") % 
        (self.eventid, self.event, self.source, self.destination, 
         repr(self.data[:24]),self.direction, self.crc))
        return s


class Debugger(Subject, Pyro.core.ObjBase):
    """
    The Debugger class is the primary remote interface for any remote stream
    debugging clients. 
    """
    def __init__(self):
        Subject.__init__(self)
        Pyro.core.ObjBase.__init__(self)
        
        self.debugq = Queue.Queue()
        self.debugon = False
        self.log = logging.getLogger("mallorymain")

    def setdebug(self, state):
        """
        This method updates the state of debugging and notifies all observers,
        typically TCP stream protocol handlers, that debugging should now be
        performed.
        
        @param state: Boolean representing the debugging state
        """
        self.log.debug("Debugger: self.debugon being set to: %s" % state)       
        if state:
            self.debugon = True
        else:
            self.debugon = False            
        self.notify(event="setdebug", state=self.debugon)
        
        return ""
    
    def getdebugq(self):
        """
        Returns the debugging queue to the client. The queue is typically a 
        list of debugging events. If the client never returns the event Mallory
        will wait forever, eventually growing sad that the event has not been
        returned. 
        
        @return: Array of L{debug.DebugEvent}
        """
        debug_events = []
        while not self.debugq.empty():
            de = self.debugq.get()
            
            #self.log.debug("Debugger: got DebugEvent: %s:%s" % 
            #               (de.__class__,de))

            debug_events.append(de)
            
        
        for event in debug_events:
            print "Event in debug_events: %s" % (de)
            
        return debug_events       
        
    def update(self, publisher, **kwargs):
        """
        Handle notifications from other classes we are observing. Typically
        this is a new event that needs to be placed into the debug queue.
        
        @param publisher: The object that sent the update
        """
        #print "[*] Debugger: got update event. Not ignoring it."
        event = kwargs["event"]
                        
        if event == "debug":                    
#            self.log.debug("Debugger: update: adding event to debug queue")
            de = DebugEvent()
            de.eventid = kwargs["eventid"]
            de.event = kwargs["event"]
            de.source = kwargs["src"]
            de.destination = kwargs["dest"]
            de.data = kwargs["thedata"]
            de.direction = kwargs["direction"]
            de.crc = binascii.crc32(kwargs["thedata"])
        
            self.log.debug("Debug.update: newevent: %08x [eventid:%s]" % 
                           (binascii.crc32(kwargs["thedata"]), 
                                            kwargs["eventid"]))
            
            self.debugq.put(de)
             
    def send_de(self, debugevent):
        """
        Notify subscribers of an incoming debug event. It is easiest to 
        understand this class name when it is thought of as a remote object
        that a remote RPC client will be invoking. In that way the event
        is "sent" and then we notify any of our observers it has come
        in from the remote client. In this case the remote client will usually
        be the Mallory GUI and the observer will be a TCPProtocl class managing
        a TCP stream
        
        @param debugevent: The DebugEvent that the client is trying to send. 
        """
        
        # Wrap it up nice and safe for transport to the debugger                
        de = debugevent
        localcrc = binascii.crc32(debugevent.data)
        
        if de.crc != localcrc:
            self.log.error("Debugger: CRC MISMATCH: expecting %08x got %08x" %
                           (de.crc, localcrc))
            
        self.log.debug("Debug.send_de: eventback: %08x [eventid:%s]" %
                        (localcrc, debugevent.eventid))
        
        self.notify(event="debugevent",debugevent=de)
        
        self.log.debug("Debug.send_de: Notify for [eventid:%s]" % 
                       (debugevent.eventid))
        
        #self.log.debug("Debugger: send_de: got debugevent %s: " %  (debugevent))
        #self.log.debug("Debugger: send_de: got debugevent %s: " %  (de))
        return ""