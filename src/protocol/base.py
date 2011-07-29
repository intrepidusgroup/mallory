import time
import socket
import config
import uuid
import Queue
import logging
import netfilter
import traceback
import select
import random
import thread
import rule


import dns
import dns.message
import dns.rdatatype

from observer import Subject
from debug import DebugEvent
from binascii import hexlify, unhexlify, crc32

class ConnData():
    """This class encapsulates all of the information about a connection it 
    is mostly designed to be a data holding class and provide convenience
    methods to turn the data into a string for easy logging, etc."""

    # TODO: Use the defines...
    DIR_C2S = 'c2s'
    DIR_S2C = 's2c'
    DIR_NONE = ''

    def __init__(self, data={'clientip':'', 'clientport':0, \
                                 'serverip':'', 'serverport':0, \
                                 'conncount':'', 'direction':''}):
        """
        Initialize the connection data.

        @param data: This is the data associated with the connection.
        clientip: the client's (victim's) ip address).
        clientport: the victim's source port.
        serverip: the destination IP address.
        serverport: the destination port.
        conncount: Used to track connections in the data store.
        direction: C2S or S2C (client to server or server to client).

        @return: No return value

        """
        self.clientip = data['clientip']
        self.clientport = data['clientport']
        self.serverip = data['serverip']
        self.serverport = data['serverport']
        self.conncount = data['conncount']
        self.direction = data['direction']

    def __str__(self):
        return "clientip:%s, clientport:%d, serverip:%s, serverport:%d " \
            "conncount:%d, direction:%s" % (self.clientip, self.clientport, \
            self.serverip, self.serverport, self.conncount, self.direction)


class Protocol(Subject):
    def __init__(self, rules = [], config = config.Config()):
        Subject.__init__(self)
        self.log = logging.getLogger("mallorymain")        
        self.config = config
        self.rules = rules
        self.plugin_manager  = None
        self.friendly_name = "Undefined"
        self.done = False
    
    def is_done(self):
        return self.done

    def set_done(self, done):
        self.done = done
        
    def close(self):
        pass
        
    def setrules(self, rules):
        self.rules = rules     
        
    def update(self, publisher, **kwargs):
        if "rules" in kwargs:
            self.rules = kwargs["rules"]
    
    def attach_plugin_manager (self, new_plugin):
        self.plugin_manager = new_plugin
    
    
class UdpProtocol(Protocol):
    """
    UDP presents a significantly different challenge for a transparent man in
    the middle proxy. UDP is a connectionless protocol and thus has no state.
    Without state the proxy must figure out, based on the incoming datagram,
    which victim the packet must be returned to. This is accomplished by mapping
    victim addresses to the outbound source port used to communicate with the
    victims intended destination. A socket is bound on a specific source port
    adfadsfasdfadfasdfadsf and used to receive all data up to a certain timeout
    in a separate thread per sourcepor

    
    Mallory must keep track of these UDP sessions for protocols, such as VPNs,
    which will have long lived "sessions" of data. This means that much of the
    protocol handling architecture for interpreting protocols that implement
    UDP will look a little different from TCP. Fundamentally, Mallory will still
    interpret the protocol but will have to build the state of that protocol 
    if the protocol implements some sort of state or reliability mechanism 
    on top of UDP. This is unavoidable if Mallory wishes to understand that
    protocol. For simple protocols, such as DNS, this is not a challenge.
    
    Note: Once instance of the UdpProtocol class manages all of the UDP data 
    for mallory. For TcpProtocol and subclasses each source and destination 
    pair (required to implement one bi-directional channel) is held in one
    instance. TcpProtocol requires a lot more setup and management during the 
    socket life cycle. 
    """
    def __init__(self, trafficdb, source, configured_protos):
        Protocol.__init__(self)
        
        self.trafficdb = trafficdb
        self.source = source
        self.session = {}
        self.lock = thread.allocate_lock()
        self.configured_protos = configured_protos
        self.supports = {}
        self.friendly_name = "UDP"
        
#    def supports(self):
#        pass
    
    def getsession(self, caddr):
        """
        caddr must be a (ip,port) tuple that most socket module functions
        use to specify a destination
        
        Return 0 (false) if a data retrieval thread does not exist for this 
        caddr. If it does exist return the external facing sourceport that
        thread is using
        """
        ret = 0
        self.lock.acquire()
        for sport in self.session:
            if caddr == self.session[sport][0]:
                ret = sport
        self.lock.release()                    
        return ret

    
    def delsession(self, sport):
        self.lock.acquire()
        if sport in self.session:
            del self.session[sport]
        self.lock.release()        
        return None
    
    def addsession(self, caddr, raddr, sport, dest):
        self.lock.acquire()
        if sport not in self.session:
            self.session[sport] = [caddr, raddr, dest]
        self.lock.release()
        return True
    
    def proto_lookup(self, raddr, rport):
        # This is not thread safe. Nothing else modified configured_protos yet.
        for proto in self.configured_protos:
            if proto.serverPort == rport:
                # Make sure it has a traffic DB
                if not proto.trafficdb:
                    proto.trafficdb = self.trafficdb
                return proto
        return None
        
    def spawn_recv_thread(self, dest, caddr, raddr, sport):
        self.log.info("UDPProtocol[t]: Starting receive thread for caddr=%s" \
                       "using sport=%d" \
                        % (caddr, sport))
        csock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        failticks = 0
        selecttimeout = 3.0
        maxfailticks = 5
        
        while True:
            try:
                # use select because recvfrom will block and can leave 
                # a dormant threads hanging about
                r, w, e = select.select([dest], [], [], selecttimeout)
                
                if dest in r:
                    pkt, raddr = dest.recvfrom(65507)
                    
                    conndata = ConnData({'clientip' : raddr[0], \
                        'clientport' : raddr[1], \
                        'serverip' : caddr[0], 'serverport' : caddr[1], \
                        'conncount' : 1, 'direction' : 's2c' })
                    dgram_time = time.time() 
                    if self.rules is not None:
                        pkt = self.processrules(pkt, conndata,dgram_time)
                    
                    
                    tdata = (raddr[0], raddr[1], caddr[0], caddr[1], "s2c",
                             repr(pkt), dgram_time)
                    self.trafficdb.dgram.put(tdata)       
                                  
                    proto = self.proto_lookup(raddr[0], raddr[1])
   
                    if proto:
                        pkt = proto.s2c_data(pkt)
                         
                    bsent = self.source.sendto(pkt, caddr)
                    self.log.debug("UDPProtocol[t]: recv_thread  sent %d " 
                                   "bytes to [%d](%s,%s)" 
                                   % (bsent, sport, caddr[0], caddr[1]))
                    failticks = 0
                    
                failticks += 1
                
                # We are done. Waited selecttimeout * maxfailticks seconds 
                if failticks == maxfailticks:
                    self.log.debug("UDPProtocol[t]: Terminating thread for "
                                   "[%d](%s,%s) No more data"
                                   % (sport, caddr[0], caddr[1]))
                    self.delsession(sport)
                    break
            except:
                traceback.print_exc()
        
    def forward_any(self):
        #TODO: Debugger support for UDP
        self.log.info("UDPProtocol: Starting main UDP thread")
        nftool = netfilter.NetfilterTool()
           
        while True:
            try:
                # Get the packet and client address
                self.log.debug("UDPProtocol[m]: Waiting for data")
                pkt, caddr  = self.source.recvfrom(65507)
                self.log.debug("UDPProtocol[m]: %s sent us %s" 
                               % (caddr, repr(pkt[:32])))
                
                # Get real destiation
                rdst, rpt = nftool.getrealdest_ct(caddr[0], caddr[1])        
                raddr = (rdst, rpt)
                
                conndata = ConnData({'clientip' : caddr[0], \
                        'clientport' : caddr[1], \
                        'serverip' : rdst, 'serverport' : rpt, \
                        'conncount' : 1, 'direction' : 'c2s' })
                dgram_time = time.time() 
                
                if self.rules is not None:
                    pkt = self.processrules(pkt, conndata, dgram_time)


                tdata = (caddr[0], caddr[1], rdst, rpt, "c2s", repr(pkt), 
                         dgram_time)
                self.trafficdb.dgram.put(tdata)                  
                self.log.debug("UDPProtocol[m]: sending data from %s to %s" 
                               % (caddr, raddr))
                
                # See if we have a session for this caddr                           
                sport = self.getsession(caddr)                        
                                
                self.log.debug("UDPProtocol[m]: self.getssion returned %d" 
                               % (sport))
                
                if sport != 0:
                    dest = self.session[sport][2]
                    bsent = dest.sendto(pkt, raddr)              
                else:
                    dest = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    dest.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                    sport = random.randrange(40000, 60001)
                    
                    # TODO: This should be in a try/catch loop in case there is
                    # an error binding on a port. Existing ports in use by other
                    # UDP sessions must also be checked.
                    dest.bind(("", sport))
                                        
                    self.log.debug("UDPProtocol[m]: main thrd sending data to " \
                                   "%s,%s " % (raddr[0],raddr[1]))
                                     
                    dest.sendto(pkt, raddr)
                    
                    
                    self.log.debug("UDPProtocol[m]: no session found for caddr " \
                                    "%s. Creating one on sport=%d" 
                                    % (caddr, sport))
                               
                    # TODO: Create a fresh protocol instance and store it with
                    # the session. This will be used to maintain "state" and
                    # history within a protocol instance object for more complex
                    # protocols like SIP/RTP, etc.          
                    self.addsession(caddr, raddr, sport, dest)
                    
                    #self.log.debug("UDPProtocol: added session")
                                      
                    thread.start_new_thread(self.spawn_recv_thread, 
                                                    (dest, caddr, raddr, sport))
                    
                    #self.log.debug("UDPProtocol: spawned new receive thread")
                    
            except:
                self.log.warn("***************************ARGH")
                traceback.print_exc()
                
    def forward_s2c(self, pkt):
        """
        Subclasses will implement this method to modify data from the server. 
        This method will get called per datagram.
        """
        return pkt
    
    def forward_c2s(self, pkt):
        """Generic client to server forwarding method. Reimplement this method 
        to modify bytes that is being sent from the client to the server
        """

    def processrules(self, string, conndata, dgram_time):
        """
        TODO: This code is not 100% ideal. It places a lot of responsibility on
        the caller for processing the rule chain, etc. This should be abstracted
        out and hidden in in the rule module. This is a nice, functional
        version, though.
        
        Very little of this code depends on the class it is in. All it needs
        is a rule chain. Perhaps a RuleChain class is in order?
        """
        if self.rules is None:
            return string
        if len(self.rules) == 0:
            return  string
                
        addr = ""
        port = conndata.serverport
                
        if conndata.direction == "c2s":
            addr = conndata.clientip
        elif conndata.direction == "s2c":
            addr = conndata.serverip

        matchingrules = []
        result = None
        kargs = {'addr':addr,
                 'port':port,
                 'direction':conndata.direction,
                 'payload':string}
        for rule in self.rules:
            #matched = rule.match(addr, port, conndata.direction)
            matched = rule.match(**kargs)
            
            if matched:
                matchingrules.append(rule)                
                # Stop processing unless the rule is a passthru Rule
                if not rule.passthru:
                    break
        
        for rule in matchingrules:
            self.log.debug("Matched UDP Rule: %s" % (rule))
           
            was_fuzzed = False
            if rule.action.name == "muck":
                string = rule.action.execute(data=string)
            if rule.action.name == "fuzz":
                old_string = string
                was_fuzzed, string = rule.action.execute(data=string)
                if was_fuzzed:
                    tdata = (conndata.clientip, conndata.clientport, 
                             conndata.serverip, conndata.serverport,
                             conndata.direction, repr(old_string),
                             repr(string), dgram_time)
                    self.trafficdb.qfuzzudp.put(tdata)
        return string 
        
    def update(self, publisher, **kwargs):
        super(UdpProtocol, self).update(publisher, **kwargs)
        
        if "event" not in kwargs:
            self.log.debug("BaseUDP: Event not in kwargs.")
            return

        event = kwargs["event"]

        if event == "updaterules":
            if "rules" not in kwargs:
                return

            rulesin = kwargs["rules"]
            self.rules = rulesin

        
class TcpProtocol(Protocol):
    """This class is the base class that TCP protocols will inherit from
    
    Primarily this class will show what methods can be implemented and provide
    a generic protocol handler.  
        
    The other important aspect of a protocol is the lifetime of the object. Some
    protocol objects will exist purely to take advantage of methods that know
    how to interpret a connection so Mallory can make decisions about how to 
    deal with that data. Others instances will exist for the full lifetime of 
    the socket and define how the socket should behave (differently) from a
    standard socket.
    
    Some protocols (HTTP) are built on top of a full TCP socket. Other protocols
    are a more basic construct (SSL) and are abstracted by providing socket like
    functionality.  Protocols that wrap TCP will still use this class most
    likely. 
    
    """    
    def __init__(self, trafficdb, source, destination):
        Protocol.__init__(self)
        
        self.friendly_name = "TCP"
        
        self.trafficdb = trafficdb
        
        # The source is always the "client" or "victim" in the code
        self.source = source        
        
        # The destination is always the victim's intended server.
        self.destination = destination
        self.serverPort = -1

        self.supports = {}

        ### Rules TODO: they must not come from a global source. Rules will
        ### be loaded at run time and updated via the pub/sub model to 
        ### allow the debug client to modify the rules easily
        #self.rules = ruleconfig.globalrules
        
        
        ### Debugging members
        self.debugon = False
        #self.waitingforevent = "" 
        
        # One debug queue for each direction. 
        self.debugqs = {"c2s":Queue.Queue(), "s2c":Queue.Queue()}
        self.waitfor = {"c2s":"", "s2c":""}  
        
        # Done processing data
        self.done = False     


    def __getstate__(self):
        """
        We can't serialize (pickle) anything with a lock (thread.lock). 
        
        Get rid of traffic DB, mostly because.
        
        Get rid of log and debugqs because they have locks and would be
        messy to deserialize in a lot of situations        
        """
        d = self.__dict__.copy()
        del d["debugqs"]
        del d["trafficdb"]
        del d["log"]
                
        return d
    
    def close(self):
        """
        Provide an interface to close sockets down
        """
        try:
            #self.source.shutdown(socket.SHUT_RDWR)
            self.source.close()
            
            #self.destination.shutdown(socket.SHUT_RDWR)
            self.destination.close()
        except:
            self.log.info("Could not close the socket")
        
            
    def forward_s2c(self):
        """Generic server to client forwarding method. Reimplement this
        method to modify bytes that is being sent back to the client"""
    
    def forward_c2s(self):
        """Generic client to server forwarding method. Reimplement this method 
        to modify bytes that is being sent from the client to the server"""
    
#    def supports(self, mevt):
#        """This lets the consumer know which mallory events the class will 
#        support"""        
#        pass
    
    def forward_any(self, conndata):
        """Generic forwarding method. Use this method if both the client to 
        server and server to client handling can be done with the same method"""
        string = ' '
        msgCnt = 0
                
        source = self.source
        destination = self.destination

        self.log.info("TcpProtocol.forward_any(): Setting up forward for " 
                      "client-->server %s-->%s" 
                      % (source.getpeername(), destination.getpeername()))
        if self.config.debug > 1:
            self.log.debug("TcpProtocol.forward_any: before switch: direction:%s, source: %s dest:%s" % \
            (conndata.direction, source.getpeername(), destination.getpeername()))
                
        # Swapping source and destinationso  method can work in both directions
        if conndata.direction == "s2c":
            source = self.destination
            destination = self.source
        
        if self.config.debug > 1:
            self.log.debug("TcpProtocol.forward_any: after switch: direction:%s, source: %s dest:%s" % \
            (conndata.direction, source.getpeername(), destination.getpeername()))
        
        # pre condition: source, conndata and destination must be valid
        if not source or not destination or not conndata:
            raise Exception("TcpProtocol was improperly configured")
            return
        
        if self.config.debug > 1:
            self.log.debug("TcpProtocol: Begin read loop direction:%s, source: %s dest:%s" % \
            (conndata.direction, source.getpeername(), destination.getpeername()))
        
        while string:
            if self.config.debug > 1:
                self.log.debug("TcpProtocol: recv bytes:%s" % (conndata.direction))
            
            
            try:
                # There needs to be some exception catching here.      
                string = source.recv(8192)
            except:
                self.done = True
                string = ""
                raise Exception("base.TcpProtocol: error with source.recv")
            
            crc1 = crc32(string)
            if string:
                if self.config.debug > 1:
                    self.log.debug("TcpProtocol: sendall:%s" % (conndata.direction))
                
                sorig = string
                
                if self.config.debug > 2:
                    self.log.debug("CRC: %08x" % (crc32(sorig)))
                
                shoulddebug = True
                

                if self.rules is not None:
                    shoulddebug, string = self.processrules(string, conndata, msgCnt)
                    
                # Potentially pause here while waiting for incoming data
                if shoulddebug:
                    # self.debugon must also be true. Allows debugger to
                    # mallory-wide turn debugging on/off
                    string = self.waitfordebug(string, conndata)
                
                if self.config.debug > 2:
                    crc2 = crc32(string)
                    if crc1 != crc2:
                        self.log.debug("TcpProtocol: Internal CRC FAIL: %08x - %08x" % (crc1, crc2))
                        self.log.debug("TcpProtocol: %s****\n\n****%s" % (repr(sorig), repr(string)))
    
                try:
                    destination.sendall(string)
                except:
                    self.done = True
                    raise Exception("TcpProtocol.forward_any: sendall error")
                
                # Store the stream data
                self.trafficdb.qFlow.put((conndata.conncount, \
                    conndata.direction, msgCnt, time.time(), repr(string)))
                
                self.log.debug("forward_any(): cc:%s dir:%s mc:%s time:%s bytes:%d" \
                    " peek:%s" % (conndata.conncount, \
                    conndata.direction, msgCnt, time.time(), len(string), \
                    repr(string[0:24])))
                    
            else:
                if self.config.debug == 1:
                    self.log.debug("forward_any(): [%s] CLOSE" % (conndata.direction))
                    self.log.debug("forward_any(): conndata:%s" % (conndata))
                try:   
                    if self.config.debug > 1:
                        self.log.debug("TcpProtocol: shutting down SOURCE.READ and DESTINATION.WRITE direction:%s, source: %s dest:%s" % \
                        (conndata.direction, source.getpeername(), destination.getpeername()))
                                         
                    source.shutdown(socket.SHUT_RD)
                    destination.shutdown(socket.SHUT_WR)
                    self.done = True
                    return
                except:
                    return
                
            msgCnt = msgCnt+1
       
    ####################################
    ### Rules Processing
    ####################################
    # TODO: Talk to JA about the last parameter i added
    def processrules(self, string, conndata, msg_cnt = -1):
        """
        TODO: This code is not 100% ideal. It places a lot of responsibility on
        the caller for processing the rule chain, etc. This should be abstracted
        out and hidden in in the rule module. This is a nice, functional
        version, though.
        
        Very little of this code depends on the class it is in. All it needs
        is a rule chain. Perhaps a RuleChain class is in order?
        """
#        return False, string
        # Make sure there are rules to process
        
        if self.rules is None:
            return False, string
        if len(self.rules) == 0:
            return False, string
                
        addr = ""
        port = conndata.serverport
                
        if conndata.direction == "c2s":
            addr = conndata.clientip
        elif conndata.direction == "s2c":
            addr = conndata.serverip

        matchingrules = []
        result = None
        kargs = {'addr':addr,
                 'port':port,
                 'direction':conndata.direction,
                 'payload':string}
        for rule in self.rules:
            #matched = rule.match(addr, port, conndata.direction)
            matched = rule.match(**kargs)
            
            if matched:
                matchingrules.append(rule)                
                # Stop processing unless the rule is a passthru Rule
                if not rule.passthru:
                    break
        
        shoulddebug = False
        was_fuzzed = False 
        for rule in matchingrules:
            self.log.debug("Matched rule: %s" % (rule))
            
            # Debug flag set
            if rule.action.name == "debug":
                shoulddebug = True
            # Muck pipe execution
            if rule.action.name == "muck":
                string = rule.action.execute(data=string)
                
            # Fuzz rule execution
            if rule.action.name == "fuzz":
                old_string = string
                was_fuzzed, string = rule.action.execute(data=string)
        
        # Put the old string and new string in the DB
        if was_fuzzed: 
            self.trafficdb.qfuzztcp.put((conndata.conncount, msg_cnt,
                    conndata.direction, repr(old_string), repr(string)))
 
        # Logging cruft
        if matched and self.config.debug > 2:
            self.log.debug("==== RULE MATCH ====")
            self.log.debug("Matching rule action name:%s" % 
                           (matchingrule.action.name))
            self.log.debug("Matching rule action:%s" % (matchingrule.action))
            self.log.debug("Matched rule: %s" % (matchingrule))        
            self.log.debug(conndata)
            self.log.debug("Matched class%s" % (matchingrule.__class__))
            self.log.debug("addr = %s, port = %d, direction = %s" %
                            (addr, port, conndata.direction))
            if shoulddebug:
                self.log.debug("I should be debugged!!")
                          
            self.log.debug("==== END RULE ====")
        
        # TODO: Seems that processrules should not return a bool only related to debug    
        return shoulddebug, string
        
    ####################################   
    ### Debugging / Interactive Code
    ####################################
    def waitfordebug(self, data, conndata):
        # TODO: Use a metaclass/mixin to add debugging to instances be they UDP
        # or TcpProtocol classes. This will make the debugging functionality
        # Easy to attach to any class instance and allow it to remain more
        # separate as it really does not belong in a protocol
        
        if self.debugon == False:# or conndata.direction == "c2s": #(USE THIS TO TEST SOME PROTOS. TURN THIS INTO A FEATURE)
            return data
        
        eventid = str(uuid.uuid4())
        
        deststr = self.destination.getpeername()
        srcstr = self.source.getpeername()
        
        self.log.debug("TcpProtocol.waitfordebug[%d]bn: eventid:%s CRC: %08x" % (id(self), eventid, crc32(data)))
        
        self.notify(event="debug", eventid=eventid, src=srcstr, dest=deststr, 
                    thedata=data,direction=conndata.direction)
        
#        self.log.debug("BaseTcp: Got a %s event. Notifying listeners." \
#            % (conndata.direction))
            
        self.waitfor[conndata.direction] = eventid
        
        ticks = 0
        while True:
            if not self.debugqs[conndata.direction].empty():                
                # Assertion: there is only one item in the queue
                # Assertion: the eventid is the one we are waiting for
                self.log.debug("TcpProtocol.waitfordebug[%d]bqc: %d" % (id(self), self.debugqs[conndata.direction].qsize()))
                de = self.debugqs[conndata.direction].get()
                self.log.debug("TcpProtocol.waitfordebug[%d]aqg: eventid:%s waitingfor:%s CRC: %08x" % (id(self), eventid, self.waitfor[conndata.direction], crc32(data)))
                #self.log.debug("BaseTcp: event is back: %s" % (de))
                self.waitfor[conndata.direction] = ""
                return de.data
            
            # If we have been waiting a while... maybe we should just
            # give up? We will get an exception or put the socket
            # into a weird state. We should really let the socket
            # handling code go through its final paces. For now
            # determine if this idea works out properly though
            
            # check let us know if an event got lost. Should not happen
            if ticks > 50 and ticks % 50 == 0:
                self.log.debug("TcpProtocol [%d]: waiting for: %s" % (id(self), self.waitfor[conndata.direction]))
                            
            ticks += 1 
            time.sleep(.1)
            
            
        return data
    
    def update(self, publisher, **kwargs):
        """
        Incoming updates that TcpProtocol is interested in. This will include
        events that TcpProtocol is waiting for from the stream debugger
        """
        super(TcpProtocol, self).update(publisher, **kwargs)
        
        if "event" not in kwargs:
            self.log.debug("BaseTcp: Event not in kwargs.")
            return
        
        event = kwargs["event"]
        

        
        if event == "updaterules":
            # TODO: Make this thread safe
            if "rules" not in kwargs:
                return

            #self.log.info("TcpProtocol.update - Got some rules %s" % (kwargs["rules"]))
                    
            rulesin = kwargs["rules"]
            self.rules = rulesin
            
        if event == "setdebug":
            self.debugon = kwargs["state"]
            self.log.info("BaseTcp: Setting debugon to: %s" % (self.debugon))
        
        if event=="debugevent":
            de = kwargs["debugevent"]
            if de.eventid == self.waitfor[de.direction]:
                self.debugqs[de.direction].put(de)                
                self.log.debug("BaseTcp[%d]: putting: [%s] in queue debugevent. waiting for[%s]" % (id(self), de.eventid, self.waitfor[de.direction]))
            
