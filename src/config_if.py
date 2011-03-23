from ctypes import *

"""
This module interfaces with the getifaddrs libc function to return a list
of ethernet devices in a reliable fashion. This should be portable on 
any POSIX compliant system. Only tested on Linux.

(grepping ifconfig is nasty)
"""

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
    
#TODO Package this in a class
def get_ifs():
    """
    Get a list of available interfaces
    
    @return: array - networking interfaces
    """
    ifa = getifaddrs_c()
        
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
        
    # TODO: Convert to list
    # TODO: Free memory here
    return ifnames 
    
def getifaddrs_c():
    """
    Interface with libc to call libc.getifaddrs. 
    
    @return: ctypes type instance (ifaddrs struct).
    """
    libc = cdll.LoadLibrary("libc.so.6")
    printf = libc.printf
    getifaddrs = libc.getifaddrs

    ptr = c_void_p(None)    
    ifaddrs_struct_p = getifaddrs(pointer(ptr))
        
    return ifaddrs.from_address(ptr.value)
    
if __name__ == "__main__":
    print get_ifs()