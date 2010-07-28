import config
import socket
import struct
import sys
import debug
import logging
from   pynetfilter_conntrack import Conntrack


class NetfilterTool():
    def __init__(self):
        # Come up with a good pattern for passing the config around at some 
        # point.
        self.config = config.Config()
        self.log = logging.getLogger("mallorymain")
        self.log.debug("NetfilterTool: Instantiating object.")
    
    def ltoip(self, n):
        """Convert a long(big number) to an IP address"""
        return socket.inet_ntoa(struct.pack('!L',n))

    def getrealdest(self, csock):   
        """
        This method only supports linux 2.4+. 
        
        Cross platform support coming soon.
        """ 
        try:
            socket.SO_ORIGINAL_DST
        except AttributeError:
            # This is not a defined socket option
            socket.SO_ORIGINAL_DST = 80
            
        # Use the Linux specific socket option to query NetFilter
        odestdata = csock.getsockopt(socket.SOL_IP, socket.SO_ORIGINAL_DST, 16)
        
        # Unpack the first 6 bytes, which hold the destination data needed                                
        _, port, a1, a2, a3, a4 = struct.unpack("!HHBBBBxxxxxxxx", odestdata)
        address = "%d.%d.%d.%d" % (a1, a2, a3, a4)
        
        return address, port
    
    def getrealdest_ct(self, newip, newport):
        if self.config.debug > 1:
            self.log.debug("Netfilter: BEGIN")
        try:
            # Create conntrack object; get conntrack table
            nf = Conntrack()
            table = nf.dump_table(socket.AF_INET)
        except:
            if self.config.debug > 0:
                self.log.error(sys.exc_info())                
            return -1,-1
        if self.config.debug > 1:
            self.log.debug("Netfilter: local socket %s:%s" % \
                (newip, newport))
            
        # Search conntrack table for target destination IP:port
        for entry in table:
            repl_ipv4_dst_ip = self.ltoip(entry.repl_ipv4_dst)
            orig_ipv4_dst_ip = self.ltoip(entry.orig_ipv4_dst)
            
            if self.config.debug > 1:
                self.log.debug("Netfilter: Trying: %s:%s" % (repl_ipv4_dst_ip, entry.repl_port_dst))
                
            if repl_ipv4_dst_ip == newip and entry.repl_port_dst == newport:
                if self.config.debug > 1:
                    self.log.debug("Netfilter: remote socket %s:%s" % \
                        (orig_ipv4_dst_ip, entry.orig_port_dst))
                return orig_ipv4_dst_ip, entry.orig_port_dst
        if self.config.debug > 0:
            self.log.debug("Netfilter: no socket match")            
            self.log.debug("Netfilter: END")
        
        return -1, -1            