"""
This module interfaces with the getifaddrs libc function to return a list
of ethernet devices in a reliable fashion. This should be portable on 
any POSIX compliant system. Only tested on Linux.

(grepping ifconfig is nasty)
"""
from ctypes import *

import subprocess

# Structures as defined by:
# http://www.kernel.org/doc/man-pages/online/pages/man3/getifaddrs.3.html
class ifa_ifu(Union):
    _fields_ = [("ifu_broadaddr", c_void_p),
                ("ifu_dstaddr", c_void_p)
                ]
    
class ifaddrs(Structure):
    _fields_ = [("ifa_next", c_void_p),
                ("ifa_name", c_char_p),
                ("ifa_flags", c_int),
                ("ifa_addr", c_void_p),
                ("ifa_netmask", c_void_p),
                ("ifa_ifu", ifa_ifu),
                ("ifa_data", c_void_p)
                ]

class ConfigInterfaces(object):
    def __init__(self):
        """
        This class is the model for the configured interfaces. It will hold
        and store which interfaces have been selected for MiTM and which 
        interfaces has been selected to be the outbound interface. Currently
        the model is a simple one. 
        
        MiTM interfaces can't be outbound. You get one outbound interface
        at a time. 
        """
        self.interfaces = []
        self.mitm_interfaces = []
        self.outbound_interfaces = []
        self.banned_interfaces = ['lo']
     
    def set_interfaces(self, interfaces):
        self.interfaces = interfaces
        for interface in self.interfaces:
            if interface in self.banned_interfaces:
                self.interfaces.remove(interface)
                
    def get_idx_for_if(self, interface):
        return self.interfaces.index(interface)
    
    def get_if_for_idx(self, index):
        if index >= 0 and index < self.num_ifs():
            return self.interfaces[index]
        return ""
    
    def get_outbound(self):
        if len(self.outbound_interfaces) == 1:
            return self.outbound_interfaces[0]
        
        return None
    
    def get_mitm(self):
        return self.mitm_interfaces
    
    def is_mitm(self, interface):
        if interface in self.mitm_interfaces:
            return True
        else:
            return False

    def set_mitm(self, interface, state):
        if interface not in self.interfaces:
            return False
        
        self.set_outbound(interface, False)
            
        if state == False:
            if interface in self.mitm_interfaces:
                self.mitm_interfaces.remove(interface)
        if state == True:
            if interface not in self.mitm_interfaces:
                self.mitm_interfaces.append(interface)
        
        return True 
     
    def is_outbound(self, interface):
        if interface in self.outbound_interfaces:
            return True
        else:
            return False
    
    def set_outbound(self, interface, state):
        if interface not in self.interfaces:
            return False
        
        # Remove interface from MiTM list if setting as outbound
        if interface in self.mitm_interfaces and state == True:
            self.mitm_interfaces.remove(interface)
            
        # Add to outbound list
        if state == True:
            self.outbound_interfaces = [interface]
            return True
            
        if state == False and self.is_outbound(interface):
            self.outbound_interfaces.remove(interface)
            
        return False
            
    def num_ifs(self):
        return len(self.interfaces)
    
    def reset(self):
        self.interfaces = []
        self.mitm_interfaces = []
        self.outbound_interfaces = []
     
    def save(self):
        """
        This method saves the configuration of the MiTM and Outbond interfaces
        
        Note: Dire security implications here as we are calling a bunch of
        shell commands with *potentially* untrusted input. The only real input
        are network interface device names. We figure, if an attacker can get
        a malicious interface name onto your system to sneak into these shell
        commands you were already in trouble. Probably owned by an APT. 
        """
        cmds = []
        
        # Turn on ip_forwarding. Linux only
        cmds.append("echo 1 > /proc/sys/net/ipv4/ip_forward")
        
        # Delete all iptables rules and set it to 
        cmds.append("iptables -F")
        cmds.append("iptables -X")
        cmds.append("iptables -t nat -F")
        cmds.append("iptables -t nat -X")
        cmds.append("iptables -t mangle -F")
        cmds.append("iptables -t mangle -X")
        cmds.append("iptables -P INPUT ACCEPT")
        cmds.append("iptables -P FORWARD ACCEPT")
        cmds.append("iptables -P OUTPUT ACCEPT")
 
        # Turn on NAT on the outbound interfaces
        cmds.append(
                    ("iptables -t nat -A POSTROUTING -o "
                    "%s -j MASQUERADE") % self.outbound_interfaces[0]
                    )
        for interface in self.get_mitm():
            cmds.append( ("iptables -t nat -A PREROUTING -j REDIRECT -i "
                          "%s -p tcp -m tcp --to-ports 20755") %  interface)
            cmds.append( ("iptables -t nat -A PREROUTING -j REDIRECT -i "
                          "%s -p udp -m udp --to-ports 20755") %  interface)
            
        for cmd in cmds:
            subprocess.call(cmd, shell=True)
        
        print cmds
    def __str__(self):
        return ("ifs:%s, mitm_ifs:%s, outbound_ifs:%s" 
                    % (self.interfaces, self.mitm_interfaces, 
                       self.outbound_interfaces))
    def test(self):
        self.interfaces = ['eth1', 'eth2', 'ppp0']
        
        testif = 'eth1'
        self.set_mitm(testif, True)        
        if not self.is_mitm(testif):
            print "Test Fail: MiTM Setting"
        
        self.set_mitm(testif, False)
        if self.is_mitm(testif):
            print "Test Fail: MiTM Setting"
            
        self.set_mitm(testif, True)
        
        # Outbound interface test cases
        print self
        self.reset()
        self.interfaces = ['eth1', 'eth2', 'ppp0']
        self.set_mitm('eth2', True)
        self.set_mitm('ppp0', True)
        self.set_outbound('eth1', True)
        print "OB Testing: '%s'" % self
        self.set_outbound('eth2', True)
        print "OB Testing 2: '%s'" % (self)       
        self.set_mitm('eth2', True)
        print "OB Testing 3: '%s'" % (self)
        self.set_mitm('eth1', False)
        print "OB Testing 3: '%s'" % (self) 
        
class NetworkInterfaces(object):
    """
    This class provides a POSIX compliant method, using ctypes, to retrieve
    the available network interfaces available to the OS.
    """
    def __init__(self):
        self.libc = cdll.LoadLibrary("libc.so.6")
        self.getifaddrs = self.libc.getifaddrs   
        self.freeifaddrs = self.libc.freeifaddrs
             
    #TODO Package this in a class
    def get_ifs(self):
        """
        Get a list of available interfaces
        
        @return: array - networking interfaces
        """
        ifa = self.getifaddrs_c()
        ifa_orig = ifa
        
        ifnames = {}
        
        # Loop over linked list of devices
        while True:
            name = ifa.ifa_name
            ifnames[name] = True
            
            if ifa.ifa_next:
                # ifa.ifa_next is just a pointer. Convert to ctypes from mem addr
                ifa = ifaddrs.from_address(ifa.ifa_next)
            else:
                break
            
        self.freeifaddrs(pointer(ifa_orig))
        
        return ifnames 
        
    def getifaddrs_c(self):
        """
        Interface with libc to call libc.getifaddrs. 
        
        @return: ctypes type instance (ifaddrs struct).
        """
    
        ptr = c_void_p(None)    
        ifaddrs_struct_p = self.getifaddrs(pointer(ptr))
            
        return ifaddrs.from_address(ptr.value)
        
if __name__ == "__main__":
    ni = NetworkInterfaces()
    print ni.get_ifs()