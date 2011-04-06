#Copyright Intrepidus Group 2010
#All Rights Reserved
#Released under the following license
#
#PYTHON SOFTWARE FOUNDATION LICENSE VERSION 2
#--------------------------------------------
#
#0. This Python Software Foundation License (the "License") applies to
#any original work of authorship (the "Software") whose owner (the
#"Licensor") has placed the following notice immediately following the
#copyright notice for the Software:
#
# "Licensed under the Python Software Foundation License Version 2"
#
#1. This LICENSE AGREEMENT is between the Licensor, and the Individual
#or Organization ("Licensee") accessing or otherwise using the
#Software in source or binary form and its associated documentation.
#
#2. Subject to the terms and conditions of this License Agreement,
#Licensor hereby grants Licensee a nonexclusive, royalty-free,
#world-wide license to reproduce, analyze, test, perform and/or display
#publicly, prepare derivative works, distribute, and otherwise use the
#Software alone or in any derivative version, provided, however, that
#Licensor's License Agreement and Licensor's notice of copyright are
#retained in the Software alone or in any derivative version prepared
#by Licensee.
#
#3. In the event Licensee prepares a derivative work that is based on
#or incorporates the Software or any part thereof, and wants to make
#the derivative work available to others as provided herein, then
#Licensee hereby agrees to include in any such work a brief summary of
#the changes made to the Software.
#
#4. Licensor is making the Software available to Licensee on an "AS IS"
#basis.  Licensor MAKES NO REPRESENTATIONS OR WARRANTIES, EXPRESS OR
#IMPLIED, WITH RESPECT TO THE SOFTWARE, TO Licensee OR TO ANY OTHER USERS
#OF THE SOFTWARE.  BY WAY OF EXAMPLE, BUT NOT LIMITATION, Licensor MAKES
#NO AND DISCLAIMS ANY REPRESENTATION OR WARRANTY OF MERCHANTABILITY OR
#FITNESS FOR ANY PARTICULAR PURPOSE OR THAT THE USE OF THE SOFTWARE WILL
#NOT INFRINGE ANY THIRD PARTY RIGHTS.
#
#5.Licensor SHALL NOT BE LIABLE TO Licensee OR ANY OTHER USERS OF THE 
#SOFTWARE FOR ANY INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES OR LOSS
#(INCLUDING, WITHOUT LIMITATION, DAMAGES FOR LOSS OF BUSINESS PROFITS,
#BUSINESS INTERRUPTION, LOSS OF BUSINESS INFORMATION, OR OTHER PECUNIARY
#LOSS) AS A RESULT OF USING, MODIFYING OR DISTRIBUTING THE SOFTWARE, OR 
#ANY DERIVATIVE THEREOF, EVEN IF ADVISED OF THE POSSIBILITY THEREOF.
#
#6. This License Agreement will automatically terminate upon a material
#breach of its terms and conditions.
#
#7. Nothing in this License Agreement shall be deemed to create any
#relationship of agency, partnership, or joint venture between Licensor
#and Licensee.  This License Agreement does not grant permission to use
#Licensor trademarks or trade name in a trademark sense to endorse or
#promote products or services of Licensee, or any third party.
#
#8. By accessing, copying, installing or otherwise using the Software,
#Licensee agrees to be bound by the terms and conditions of this License
#Agreement.


#! /usr/bin/env python
"""
Usage: %s [ database_filename ]
"""
import config
import copy
import os
import os.path
import re
import socket
import sqlite3
import ssl
import sys
import thread
import time
import Queue
import select
import xmlrpclib
import logging
import traceback
import struct
import ruleconfig
import rpc

### MALLORY IMPORTS ###
import netfilter
import malloryevt
import config_proto
from cmdlineopts import CmdLineOpts
from trafficdb import TrafficDb
from observer import Subject
from debug import DebugEvent, Debugger
from binascii import hexlify, unhexlify
import cert_auth

# These protocols have no dependencies and are safe to import
from protocol import base, dnsp

try:
    # These protocols have dependencies and may not be safe to import 
    from protocol import sslproto, http, ssh, https
    from plugin_managers import http_plugin_manager
except ImportError:
    print "ImportError: Trouble importing protocols with dependencies. " \
            "Proceeding with minimal protocol support."


# Config object is global. Buyer beware.
config = config.Config()

FLIP_IMAGES = True

def usage():
    sys.stderr.write ( __doc__ % os.path.basename(sys.argv[0]) )


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
        

class Mallory(Subject):
    """
    The main Mallory class used to instantiate and start the proxy. Protocols
    can be configured through methods in the main Mallory class. This is
    where it all starts.
    """    
    def __init__(self, options):        
        Subject.__init__(self)
        self.configured_protos = []
        self.configured_plugin_managers = []
        self.protoinstances = []
        self.opts = options.options
        self.dbname = self.opts.trafficdb
        self.debugon = False
        self.debugger = Debugger(ruleconfig.globalrules)
        self.config_protocols = config_proto.ConfigProtocols()
        self.rpcserver = rpc.RPCServer()
        self.nftool = netfilter.NetfilterTool()
        self.log = logging.getLogger("mallorymain")
        config.logsetup(self.log)
                        
    def configure_protocol(self, protocol, action):
        """
        Configure a protocol. Use this method to configure Mallory protocols.

        @param protocol: The Mallory protocol, from the protocol module, to
        be configured.

        @param action: when the value is "add" the protocol will be added to the
        protocol classes Mallory uses to decode protocols

        @type action: string

        @return: No return value
        """        
        if action == "add":
            self.configured_protos.append(protocol)
            print protocol.serverPort
    
    def configure_protocols(self):
        protocols = self.config_protocols.get_protocols()
        
        for protocol in protocols:
            print "Configuring protocol : %s" % (protocol)
            self.configure_protocol(protocol, "add")
        
   
    def add_plugin_manager(self, pluginManager):
        """
        Add a new plugin manager to Mallory's configured plugin managers.

        @param plugin_manager: The plugin manager to be added.
        @type plugin_manager:
        plugin_managers.plugin_managers_base.PluginManagerBase.
        """        
        self.configured_plugin_managers.append (pluginManager)    

    def configure_socket(self, mevt, **kwargs):
        """
        Private method to configure a socket.

        @param mevt: This is a mallory event from module malloryevt
        @param kwargs: keyworded arguments. Currently expects one named
        argument, protoinst. The protoinst must be a protocol instance.
        @type kwargs: protoinst=L{Protocol<src.protocol.base.Protocol>}
        """        
        protoinst = kwargs["protoinst"]
        
        if not protoinst:
            return
        
        for proto in self.configured_protos:     
            if mevt in proto.supports:
                if proto.serverPort == protoinst.serverPort:
                    if mevt == malloryevt.CSACCEPT or mevt == malloryevt.CSAFTERSS:
                        protoinst.configure_client_socket()
                    elif mevt == malloryevt.SSCREATE: 
                        protoinst.configure_server_socket()
                          
                                    
    def forward(self, protoinst, conndata): 
        """
        Internal method for setting up data pumps for sockets.

        @param protoinst: A protocol instance to set up.
        @type protoinst: L{Protocol <src.protocol.base.Protocol>}


        """
        if malloryevt.STARTS2C in protoinst.supports and conndata.direction == "s2c":
            protoinst.forward_s2c(conndata)
        elif malloryevt.STARTC2S in protoinst.supports and conndata.direction == "c2s":
            protoinst.forward_c2s(conndata)
        else:
            protoinst.forward_any(conndata)


    def update(self, publisher, **kwargs):
        if "action" not in kwargs:
            return
        
        if kwargs["action"] == "load_protos":
            self.configure_protocols()
        
            
                

    def main(self):
        """
        Mallory's main method. When this is called the following activities
        occur.

            - A new traffic database is created
            - A new thread for debugger RPC is created
            - a listening socket for the proxy is created
            - A UDP socket is created
            - A new thread for processing the DB Queue is created
            - The proxy begins listening for incoming connections
        """        
        dbConn = TrafficDb(self.dbname)

        # Kick off a thread for the debugger
        #thread.start_new_thread(self.debugger.rpcserver, ())
        
        # Mallory needs to know if the protocol config changes
        self.config_protocols.attach(self)
        
        self.rpcserver.add_remote_obj(self.debugger, "debugger")
        self.rpcserver.add_remote_obj(self.config_protocols, "config_proto")
        
        self.configure_protocols()
        
        thread.start_new_thread(self.rpcserver.start_server, ())

        try:
            # Create proxy and wait for connections
            proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            proxy.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            udpproxy = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            if self.opts.listen:
                bindaddr = ('', int(self.opts.listen))

            self.log.info("Binding mallory to: %s:%d" \
                          % (bindaddr[0], bindaddr[1]))

            proxy.bind(bindaddr)
            udpproxy.bind(bindaddr)

            proxy.listen(5)

            if config.debug == 1:
                self.log.debug("main: Waiting for connection")

            connCount = 0

            # This thread puts data in the database. 
            thread.start_new_thread(dbConn.fillDB, ())

            try:
                # Not a standard part of mallory. For ssh ownage only.
                sshshellpwn = ssh.SSHProtocol(None, None, None)
                thread.start_new_thread(sshshellpwn.provideshell, (self, ))
            except NameError:
                self.log.warn("main: SSHProtocol not defined. sshshellpwn "
                              "unavailable")
                
            
            # Handle UDP
            udp = base.UdpProtocol(dbConn, udpproxy, self.configured_protos)
            
            # Setup bi-directional pub/sub setup for debugger events. This
            # is a very important step. Without it the debugging client and or
            # mallory will not know when an event has occured
            #self.debugger.attach(udp)
            #udp.attach(self.debugger)
            
            thread.start_new_thread(udp.forward_any, ())
                    
            # Handle TCP
            while 1:
                (csock, caddr) = proxy.accept()
                        
                
                if config.debug == 1:
                    self.log.info("main: got connection from: %s:%s" % 
                        (caddr[0], caddr[1]))
                try:
                    # TODO: Move this option into the netfilter class 
                    # destination lookup methods
                    if self.opts.notransparent:
                        shost,sport = self.opts.notransparent.split(":")
                        sport = int(sport)
                        self.log.debug("Sending to:%s:%d" % (shost, sport))
                    else:
                        (shost,sport) = self.nftool.getrealdest(csock)
                except:
                    traceback.print_exc()
                    self.log.warn("main: error getting real destination")
                    
                try:
                    # Create protocol instance using server port as guide
                    protoinst = None
                                        
                    for proto in self.configured_protos:
                        if sport == proto.serverPort:
                            protoinst = proto.__class__(dbConn, csock,
                                                        None)
                    if not protoinst:                    
                        protoinst = base.TcpProtocol(dbConn, csock, None)
                        
                    self.log.debug("Mallory.main: created a %s class" % (protoinst.__class__))
                    protoinst.setrules(self.debugger.rules)
                                                
                    # Set the proper debugging flag.  
                    protoinst.debugon = self.debugger.debugon
                    
                    # Connect up the proper publishers and subscribers                    
                    self.attach(protoinst)
                    
                    # Have the debugger listen for updates               
                    self.debugger.attach(protoinst)
                    protoinst.attach(self.debugger)
                    
                    # Which Protocol manager to which protocol
                    for plugin_manager in self.configured_plugin_managers:
                        if sport == plugin_manager.server_port:
                            protoinst.attach_plugin_manager(plugin_manager)
                    
                    # Subscribe updates between mallory and the proto instance
                    protoinst.attach(self)                    
                    self.protoinstances.append(protoinst)
                      
                    # Create the server socket (victim's destination)
                    ssock = socket.socket(socket.AF_INET, \
                                                 socket.SOCK_STREAM)
                    
                    # Set server sock data in protocol instance then config it
                    protoinst.destination = ssock
                    protoinst.serverPort = sport                    
                    self.configure_socket(malloryevt.SSCREATE, 
                                          protoinst=protoinst)
                    
                    if self.opts.proxify:
                        shost,sport = self.opts.proxify.split(":")
                        sport = int(sport)       
                        
                    # Connect the server socket 
                    protoinst.destination.connect((shost, int(sport)))
                        
                    # Client socket configuration after server socket creation                    
                    protoinst.source = csock                    
                    self.configure_socket(malloryevt.CSAFTERSS,
                                          protoinst=protoinst)
                    
                    
                except KeyboardInterrupt:
                    self.log.warn("mallory: got keyboard interrupt in" \
                                  " conn attempt")
                    sys.exit(0)
                except:
                    # Deal with the freaky folks
                    self.log.error("main: error connecting to remote")
                    traceback.print_exc()
                    print sys.exc_info()
                    continue
                            
                # Retrieve the connection data.
                clientconn = ConnData({'clientip' : caddr[0], \
                        'clientport' : caddr[1], \
                        'serverip' : shost, 'serverport' : sport, \
                        'conncount' : connCount, 'direction' : 'c2s' })
                
                # Store the connection data
                dbConn.qConn.put((connCount, shost, sport, \
                                  caddr[0], caddr[1]))

 
                # Kick off the s2c and c2s data pumps
                thread.start_new_thread(self.forward, (protoinst, clientconn))                
                serverconn = copy.deepcopy(clientconn)
                serverconn.direction = 's2c'                
                thread.start_new_thread(self.forward, (protoinst, serverconn))

                
                connCount = connCount + 1
        
        except KeyboardInterrupt:
            self.log.info("Mallory: Goodbye.")
            proxy.close()
            sys.exit(0)
    
        except:
            self.log.error("Mallory: Blanket exception handler got an " \
                           "exception")
            traceback.print_exc()
            print sys.exc_info()
            proxy.close()
        
        
if __name__ == '__main__':
    print "MALLLLORYYY!!!!!!!!!!"
        
    opts = CmdLineOpts() 
    mallory = Mallory(opts)
    
    # If a protocol for a destination / server is listening on a nonstandard
    # port the protocol can be configured to target a different server port
    # In this case we will demonstrate how to configure an SSL based protocol
    # listening on port 987. 
    #
    #    nonstandardssl = sslproto.SSLProtocol(None, None, None)
    #    nonstandardssl.serverPort = 987
    #    mallory.configure_protocol(nonstandardssl, "add")
    #
    # And now mallory will treat traffic on port 987 as SSL protocol traffic.
    
#    mallory.configure_protocol(sslproto.SSLProtocol(None, None, None), "add")    
    #mallory.configure_protocol(http.HTTP(None, None, None), "add")
    #mallory.add_plugin_manager(http_plugin_manager.HttpPluginManager ())
#    
    #mallory.configure_protocol(https.HTTPS(None, None, None), "add")
#    mallory.configure_protocol(dnsp.DNS(None, None, None), "add")
#    mallory.configure_protocol(ssh.SSHProtocol(None, None, None), "add")
    # Pull in the protocol configured on the command line for use with the
    # no-transparent option when the proxy is not being used transparently
    if opts.options.proto:
        import protocol
        print "Proto is %s" % (opts.options.proto)
        
        modulename,protoname = opts.options.proto.split(".")
            
        try:
            protomodule = getattr(protocol, modulename)
            protoinstance = getattr(protomodule, protoname)(None, None, None)
            mallory.configure_protocol(protoinstance, "add")
            mallory.log.info("Configuring command line protocol instance: %s "
                             "for port %d" \
                             % (protoinstance, protoinstance.serverPort))
        except:
            print "Invalid protocol specified at command line"
            
        
    mallory.main()
