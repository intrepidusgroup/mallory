from base import TcpProtocol

import os
import os.path
import socket
import ssl
import malloryevt
import logging
import subprocess
import re

from x509 import *
from   pyasn1.codec.der import decoder

class SSLProtocol(TcpProtocol):
    """This class knows how to wrap a socket using SSL and create fake 
    certificates to fully facilitate SSL MiTM"""
    
    def __init__(self, trafficdb, source, destination):
        TcpProtocol.__init__(self, trafficdb, source, destination)       
        self.serverPort = 443
        self.name = "SSL"
        self.log = logging.getLogger("mallorymain")
        self.log.debug("SSLProtocol: Initializing") 
        self.supports = {malloryevt.CSAFTERSS:True, malloryevt.SSCREATE:True}        
                        
    def configure_client_socket(self):
        """This is the socket from mallory to the victim"""
        self.log.debug("SSLProto: Getting common name from socket")        
        cn = self.getCNfromSSLSock(self.destination) #server
                
        self.log.debug("SSLProto: got CN: " + cn)
        
        # Canonicalize and white list filter the common name
        cn = re.sub("[^*A-Za-z0-9\-]+", ".", cn)
                
        # Execute the shell script that will create the certificate
        if not (os.path.exists("./certs/" + cn + ".cer")): #SSL
            ret = subprocess.call(['./cert.sh', cn])
            
        # Wrap the socket back to the victim with our new ssl 
        self.source = ssl.wrap_socket(self.source, \
              server_side=True, certfile="./certs/" +cn + ".cer", 
              keyfile="./certs/" + cn + ".key",
              #ssl_version=ssl.PROTOCOL_TLSv1) 
              ssl_version=ssl.PROTOCOL_SSLv23)
         
      
    def configure_server_socket(self):
        """This is the socket from mallory to the server"""
        self.log.debug("SSLProto: configure_server_socket")
        self.destination = ssl.wrap_socket(self.destination)
        return None, None
      
#    def supports(self, mevt):
#        if mevt == malloryevt.CSAFTERSS:
#            return True       
#        if mevt == malloryevt.SSCREATE:
#            return True
#       
#        return False              
        
    def getCNfromSSLSock(self, sslSock):
        derCert = sslSock.getpeercert(True)

        #print repr(derCert)
        
        #print decoder.decode(derCert,asn1Spec=certType)[0].prettyPrint()
        buff = decoder.decode(derCert,asn1Spec=certType)[0].\
               getComponentByName('tbsCertificate').\
               getComponentByName('subject').\
               getComponentByType(RDNSequence().getTagSet())
               
        
        #print buff.__class__.__name__
        #print buff.prettyPrint()
        for item in buff:
            if item[0].getComponentByName('type') == (2, 5, 4, 3):
                cn = item[0].getComponentByName('value')
                break
        for item in cn:
            if item != None:
                return str(item)        