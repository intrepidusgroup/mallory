import sys
import xmlrpclib
import time
import thread
import Queue

#from debug import DebugEvent
from binascii import hexlify, unhexlify, crc32



#events = []
#mode = "m"


class CLIDebug(object):
    """
    CLIDebug Documentation
    """
    def __init__(self): 
        """
        Most important init method
        """       
        self.events = []
        self.mode = "m"
        self.proxy = xmlrpclib.ServerProxy("http://localhost:20757") 
        self.lock = thread.allocate_lock()
        self.event_to_send = -1
        
        
    def start_threads(self):
        thread.start_new_thread(self.cli_input_thread, ())
        thread.start_new_thread(self.client_thread, ())
              
    def format_event(self, event):
        dirthing = "-->"
        if event['direction'] == "s2c":
            dirthing = "<--"
            
        rawdata = event["data"].decode("string-escape")
        return "eid: %s|dir:%s [%08x] (%s)%s(%s) -- %s\n" % \
            (event['eventid'], event['direction'], crc32(rawdata), event['source'], \
               dirthing, event['destination'], repr(rawdata[:24]))
          
    def getmenu(self):
        menu = ""
        menu += "  [a] auto send mode\n"             
        menu += "  [m] manual mode\n"
        menu += "  [o] debugger off at server\n"
        menu += "  [n] debugger on at server\n"
        menu += "  [q] quit\n"
        return menu
    
    def cli_input_thread(self):
        while True:
            strevents = ""
            cnt = 0
                      
            for event in self.events:
        

                    
                strevents += "  [%d] %s" % (cnt, self.format_event(event))
                
                cnt += 1
            

            
            
            print strevents
            
            cmd = raw_input("Command: ").strip()        
                
            if cmd == "a":
                print "Setting auto mode."
                self.lock.acquire()
                self.mode = "a"
                self.lock.release()
            elif cmd == "m":
                print "Setting manual mode."
                self.lock.acquire()
                self.mode = "m"
                self.lock.release()
            elif cmd == "o":
                print "Debugger turned off at server."
                self.proxy.setdebug(False)
            elif cmd == "n":
                print "Debugger turned on at server."
                self.proxy.setdebug(True)                                        
            elif cmd == "q":
                print "You can never leave :("
            elif cmd == "h" or cmd == "help" or cmd == "?":
                print self.getmenu()
            else:                
                try:
                    eventnum = int(cmd)
                except:
                    eventnum = -1
                
                
                sendevt = True
                
                self.lock.acquire()
                            
                if len(self.events) == 0 or eventnum < 0 or eventnum > len(self.events):
                    sendevt = False
                    print "Invalid Event"
                    
                print "Setting event to send to: " + str(eventnum)
                if sendevt:
                    self.event_to_send = eventnum
                        
                self.lock.release()
            
            

    def client_thread(self):
        while True:
            self.lock.acquire()
  
            if self.mode == "a":
                self.event_to_send = len(self.events) - 1
                                
            if self.event_to_send != -1:
                print "Sending event: %s" % (self.format_event(event)) 
                
                theevent = self.events[self.event_to_send]
                rawdata = theevent["data"].decode("string-escape")
                theevent["crc"] = crc32(rawdata)
                self.proxy.send_de(self.events[self.event_to_send])        
                del self.events[self.event_to_send]
                self.event_to_send = -1
                            
            newevents = self.proxy.getdebugq()
            
            for event in newevents:
                d = event["data"].decode("string-escape")
                dcrc = crc32(d)
                print "CRC: %08x for eventid:%s" % (dcrc, event["eventid"])                
                self.events.append(event)
                
            self.lock.release()
            
            time.sleep(.1)
            
        
        
if __name__ == '__main__':              
    argh = CLIDebug()
    
    argh.start_threads()
        
    while True:
        time.sleep(1)

#client.cli_input_thread()

#thread.start_new_thread(input_thread, (), lock)
#thread.start_new_thread(send_thread, (), lock)
     
     
#while True:
#    newevents = proxy.getdebugq()
#    
#    for event in newevents:
#        print "Got new event!"
#        events.append(event)
#    
#    strevents = ""
#    cnt = 0
#    for event in events:
#        
#        dirthing = "-->"
#        if event['direction'] == "s2c":
#            dirthing = "<--"
#                    
#        strevents += "[%d] eid: %s|dir:%s (%s)%s(%s)\n" % (cnt, event['eventid'], event['direction'], event['source'], dirthing, event['destination'])
#        cnt += 1
#        
#    try:
#        print "[a] auto send mode"
#        print "[m] manual mode"
#        print strevents
#        
#        if mode == "m":
#            instr = raw_input("Which event do you want to send? ").strip()
#
#            if instr == "m":
#                mode = "m"
#                continue
#            elif instr == "a":
#                mode = "a"
#                continue
#        
#        if mode == "m":
#            eventnum = int(instr)
#        else:
#            eventnum = 0
#            
#        if len(events) == 0 or eventnum < 0 or eventnum > len(events):
#            print "Invalid event"
#            
#            if mode == "a":
#                time.sleep(.5)
#            continue
#                
#        proxy.send_de(events[eventnum])
#        
#        del events[eventnum]
#        
#    except KeyboardInterrupt:
#        break
#    except:
#        print "Invalid event (e)"
    

    
    
    

#while True:
#        eventlist = proxy.getdebugq()
#                 
#        # Should be acquiring a mutex here
#        for event in eventlist:
#            dirthing = "-->"
#            if event['direction'] == "s2c":
#                dirthing = "<--"
#                
#            print "eid: %s|dir:%s (%s)%s(%s)" % (event['eventid'], event['direction'], event['source'], dirthing, event['destination'])
#            proxy.send_de(event)
#            
#        time.sleep(.1)
