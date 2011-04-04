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
        self.serverPort = 443
        self.name = "SSL"
        self.log = logging.getLogger("mallorymain")
        self.log.debug("SSLProtocol: Initializing") 
        self.supports = {malloryevt.CSAFTERSS:True, malloryevt.SSCREATE:True}        
    
    def generateRSAKey(self):
        return M2Crypto.RSA.gen_key(1024, M2Crypto.m2.RSA_F4)

    def makePKey(self, key):
        pkey = M2Crypto.EVP.PKey()
        pkey.assign_rsa(key)
        return pkey
    
    def makeRequest(self, pkey,CN):
        req = M2Crypto.X509.Request()
        req.set_version(2)
        req.set_pubkey(pkey)
        name = M2Crypto.X509.X509_Name()
        name.CN = CN
        req.set_subject_name(name)
        req.sign(pkey,'sha1')
        return req

    def makeCaCert(self, caPkey):
        #ddpkey = req.get_pubkey()
        #sub = req.get_subject()
        
        name = M2Crypto.X509.X509_Name()
        name.CN = "VeriSign Clas 3 Secure Server CA - G2"
        name.O = "VeriSign, Inc."
        name.C = "US"
        name.OU = "Verisign Trust Network"

        cert = M2Crypto.X509.X509()
        cert.set_serial_number(1)
        cert.set_version(2)
        cert.set_subject(name)
        
        issuer = M2Crypto.X509.X509_Name()
        issuer.CN = "VeriSign Class 3 Secure Server CA - G2"
        issuer.O = "VeriSign, Inc."
        issuer.C = "US"
        issuer.OU = "Verisign Trust Network"
        
        cert.set_issuer(issuer)
        cert.set_pubkey(caPkey)
        notBefore = M2Crypto.m2.x509_get_not_before(cert.x509)
        notAfter =  M2Crypto.m2.x509_get_not_after(cert.x509)
        M2Crypto.m2.x509_gmtime_adj(notBefore, 0)
        M2Crypto.m2.x509_gmtime_adj(notAfter, 60*60*24*365*10)
        
        cert.sign(caPkey,'sha1')
        return cert

    def makePeerCert(self, peerSub, peerIss, peerNotAfter, peerNotBefore, peerSerial,
                     peerKey, caKey, caCert):
        
        cert = M2Crypto.X509.X509()
        cert.set_serial_number(peerSerial)
        cert.set_version(2)
        cert.set_subject(peerSub)
        cert.set_issuer(peerIss)
        #cert.set_issuer(caCert.get_subject())
        cert.set_pubkey(peerKey)
        cert.set_not_after(peerNotAfter)
        cert.set_not_before(peerNotBefore)
        cert.sign(caKey,'sha1')
        return cert

    def ca(self):
        key = self.generateRSAKey()
        pkey =  self.makePKey(key)
        cert = self.makeCaCert(pkey)
        return (cert, pkey)

    def cert(self, peerSub, peerIss, peerNotAfter, peerNotBefore, peerSerial, 
             caKey, caCert):
        key= self.generateRSAKey()
        peerKey = self.makePKey(key)
        cert = self.makePeerCert(peerSub, peerIss, peerNotAfter,
                                 peerNotBefore, peerSerial,
                                 peerKey, caKey, caCert)
        return (cert,peerKey)
                
    def configure_client_socket(self):
        """This is the socket from mallory to the victim"""
        self.log.debug("SSLProto: Getting common name from socket")
        cert_from_remote_server = self.destination.getpeercert(True)

        m2_crypto_cert = M2Crypto.X509.load_cert_der_string(
            cert_from_remote_server)
        fake_cert, fake_key = cert_auth.ca.get_fake_cert_and_key_filename(m2_crypto_cert)
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
#        cn = self.getCNfromSSLSock(self.destination) #server            
#        self.log.debug("SSLProto: got CN: " + cn)
#        
#        # Canonicalize and white list filter the common name
#        cn = re.sub("[^*A-Za-z0-9\-]+", ".", cn)
#                
#        # Execute the shell script that will create the certificate
#        if not (os.path.exists("./certs/" + cn + ".cer")): #SSL
#            ret = subprocess.call(['./cert.sh', cn])
#            
#        # Wrap the socket back to the victim with our new ssl 
#        try:
#            self.source = ssl.wrap_socket(self.source,
#              server_side=True, certfile="./certs/" +cn + ".cer", 
#              keyfile="./certs/" + cn + ".key", 
#              ssl_version=ssl.PROTOCOL_SSLv23)
#        except:
#            self.log.debug("SSLProto: Client Closed SSL Connection")
     
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
        
        self.log.debug("CN Extraction: Doing Stuff")
        m2crypt_cert = M2Crypto.X509.load_cert_der_string(derCert)
        #print m2crypt_cert.as_text()
        print m2crypt_cert.get_pubkey() 
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
