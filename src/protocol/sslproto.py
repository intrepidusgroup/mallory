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
        return M2Crypto.RSA.gen_key(2048, M2Crypto.m2.RSA_F4)

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

    def makeCert(self, CN, caPkey):
        #ddpkey = req.get_pubkey()
        #sub = req.get_subject()
        
        name = M2Crypto.X509.X509_Name()
        name.CN = CN+"first"

        cert = M2Crypto.X509.X509()
        cert.set_serial_number(1)
        cert.set_version(2)
        cert.set_subject(name)
        
        issuer = M2Crypto.X509.X509_Name()
        issuer.CN = CN+"second"
        issuer.O = CN+"third"
        
        cert.set_issuer(issuer)
        cert.set_pubkey(caPkey)
        notBefore = M2Crypto.m2.x509_get_not_before(cert.x509)
        notAfter =  M2Crypto.m2.x509_get_not_after(cert.x509)
        M2Crypto.m2.x509_gmtime_adj(notBefore, 0)
        M2Crypto.m2.x509_gmtime_adj(notAfter, 60*60*24*365*10)
        
        cert.sign(caPkey,'sha1')
        return cert

    def ca(self):
        key = self.generateRSAKey()
        pkey =  self.makePKey(key)
        cert = self.makeCert("Test CA 1", pkey)
        return (cert, pkey)
                
    def configure_client_socket(self):
        """This is the socket from mallory to the victim"""
        self.log.debug("SSLProto: Getting common name from socket")
        

        caCert, caPkey = self.ca()


        cert_from_remote_server = self.destination.getpeercert(True)
        m2crypt_cert = M2Crypto.X509.load_cert_der_string(
            cert_from_remote_server)
        len_of_pub_key = m2crypt_cert.get_pubkey().size()
        
        self.log.debug("SSLProto: Generating a new key for cert")
        new_rsa_key = M2Crypto.RSA.gen_key(len_of_pub_key*8,
            M2Crypto.m2.RSA_F4)
        pkey = M2Crypto.EVP.PKey()
        pkey.assign_rsa(new_rsa_key)
        
        self.log.debug("SSLProto: Setting new keys in cert and signing")
        m2crypt_cert.set_pubkey(pkey)
        m2crypt_cert.set_serial_number(m2crypt_cert.get_serial_number()+100)
        m2crypt_cert.set_issuer(caCert.get_issuer())
        m2crypt_cert.sign(caPkey,"sha1") #NEED TO REMOVE FOR STEP 2

        self.log.debug("SSLProto: Making temp cert and key file")
        tempCer = m2crypt_cert.as_text()
        tempCer = tempCer + m2crypt_cert.as_pem ()
        tempCertFile = tempfile.NamedTemporaryFile(delete=False)
        tempCertFile.write(tempCer)
        tempCertFile.flush()

        tempKeyFile = tempfile.NamedTemporaryFile(delete=False)
        tempKeyFile.write(pkey.as_pem(None))
        tempKeyFile.flush()
          
        self.log.debug("SSLProto: Starting Socket")
        try:
            self.source = ssl.wrap_socket(self.source,
              server_side=True, certfile=tempCertFile.name, 
              keyfile=tempKeyFile.name, 
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
