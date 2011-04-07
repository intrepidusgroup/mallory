from base import TcpProtocol

import os
import os.path
import socket
import ssl
import malloryevt
import logging
import subprocess
import re
import M2Crypto
import tempfile
import traceback
import cert_auth

from x509 import *
from   pyasn1.codec.der import decoder

class SSLProtocol(TcpProtocol):
    """This class knows how to wrap a socket using SSL and create fake 
    certificates to fully facilitate SSL MiTM"""
    
    def __init__(self, trafficdb, source, destination):
        TcpProtocol.__init__(self, trafficdb, source, destination) 
        self.friendly_name = "SSL Base"      
        self.serverPort = 443
        self.name = "SSL"
        self.log = logging.getLogger("mallorymain")
        self.log.debug("SSLProtocol: Initializing") 
        self.supports = {malloryevt.CSAFTERSS:True, malloryevt.SSCREATE:True}        
    
                
    def configure_client_socket(self):
        """This is the socket from mallory to the victim"""
        self.log.debug("SSLProto: Getting common name from socket")
        cert_from_remote_server = self.destination.getpeercert(True)

        fake_cert, fake_key = cert_auth.ca.get_fake_cert_and_key_filename(cert_from_remote_server)
        self.log.debug("SSLProto: Starting Socket")
        try:
            self.source = ssl.wrap_socket(self.source,
              server_side=True, 
              certfile=fake_cert, 
              keyfile=fake_key, 
              ssl_version=ssl.PROTOCOL_SSLv23)
        except:
            self.log.debug("SSLProto: Client Closed SSL Connection")
            traceback.print_exc()       
        self.log.debug("SSLProto: WoWzer!!")
     
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
        
#    def getCNfromSSLSock(self, sslSock):
#        derCert = sslSock.getpeercert(True)
#        
#        self.log.debug("CN Extraction: Doing Stuff")
#        m2crypt_cert = M2Crypto.X509.load_cert_der_string(derCert)
#        #print m2crypt_cert.as_text()
#        print m2crypt_cert.get_pubkey() 
#        buff = decoder.decode(derCert,asn1Spec=certType)[0].\
#               getComponentByName('tbsCertificate').\
#               getComponentByName('subject').\
#               getComponentByType(RDNSequence().getTagSet())
#               
#        
#        #print buff.__class__.__name__
#        #print buff.prettyPrint()
#        for item in buff:
#            if item[0].getComponentByName('type') == (2, 5, 4, 3):
#                cn = item[0].getComponentByName('value')
#                break
#        for item in cn:
#            if item != None:
#                return str(item)        
