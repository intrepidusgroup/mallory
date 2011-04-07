import base
import dns
import dns.message
import dns.rdatatype
import logging
import dnsconfig

class DNS(base.UdpProtocol):
    def __init__(self, trafficdb, source, destination):
        self.friendly_name = "DNS"
        self.serverPort = 53
        self.trafficdb = None
        self.log = logging.getLogger("mallorymain")
        self.supports = {}
    
    def s2c_data(self, pkt):
        pkt = self.dnsmod(pkt)
        return pkt
    
    def dnsmod(self, pkt):
        """
        This is a very crude mangling system for replacing the results of a DNS
        A record response from a DNS server. It will search for the key of
        the dictionary as an A record question and replace the returned
        address with the value for the key. The matching is if the string
        occurs anywhere inside of the A record lookup. So this would be easily
        tricked by providing "cnn.com.mydomain.com". However, it is sufficient
        for proof of concept code. 
        """
        
        m = dns.message.from_wire(pkt)
          
        arecord_manglemap = dnsconfig.arecord_manglemap
        
        self.log.debug("UDPProtocol[t]: DNS mangling %s\n" % (m))    
        for rrset in m.answer:
            self.log.debug("RRSET: rrset=%s rdclass=%s rdtype=%s" % 
                           (repr(rrset.name), rrset.rdclass, rrset.rdtype))
                                                
            if rrset.rdtype is dns.rdatatype.A:
                for item in rrset:
                    for mangling in arecord_manglemap:
                        if mangling in str(rrset.name):
                            item.address = arecord_manglemap[mangling]
                            self.log.debug("Item: %s,%s" % (item, repr(item)))

        return m.to_wire()    