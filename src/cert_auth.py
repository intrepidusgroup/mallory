import os
import M2Crypto
import tempfile
import hashlib
import random
import time

class CertAndKeyContainer(object):
    def __init__(self,cert,key,cert_file_name,key_file_name):
        self.cert = cert
        self.key = key
        self.cert_file_name = cert_file_name
        self.key_file_name = key_file_name

class CertAuth(object):
    def __init__(self):
        self.store_of_certs = {}
        if (not os.path.exists("ca/ca.cer")):
            self.ca_cert, self.ca_pkey = self.ca()
            self.ca_cert_file = open ("ca/ca.cer","w")
            self.ca_cert_file.write(self.ca_cert.as_pem())
            self.ca_cert_file.close()
            self.ca_key_file = open ("ca/ca.key","w")
            self.ca_key_file.write(self.ca_pkey.as_pem(None))
            self.ca_key_file.close()
        else:
            self.ca_cert = M2Crypto.X509.load_cert_string(
                        open("ca/ca.cer","r").read())
            self.ca_pkey = M2Crypto.EVP.load_key_string(
                        open("ca/ca.key","r").read())


    def ca(self):
        key = self.generate_rsa_key()
        pkey =  self.make_pkey(key)
        cert = self.make_ca_cert(pkey)
        return (cert, pkey)

    def generate_rsa_key(self):
        return M2Crypto.RSA.gen_key(1024, M2Crypto.m2.RSA_F4)

    def make_pkey(self, key):
        pkey = M2Crypto.EVP.PKey()
        pkey.assign_rsa(key)
        return pkey

    def make_ca_cert(self, ca_pkey):
        name = M2Crypto.X509.X509_Name()
        # TODO: Make this editable
         
        name.C = "US"
        name.O = "VeriSign, Inc"
        name.CN = "VeriSign Clas 3 Secure Server CA - GG"
        #name.OU = "Verisign Trust Networks"
        cert = M2Crypto.X509.X509()
        cert.set_serial_number(1)
        cert.set_version(2)
        cert.set_subject(name)

        issuer = M2Crypto.X509.X509_Name()
        
        issuer.C = "US"
        issuer.O = "VeriSign, Inc"
        issuer.CN = "VeriSign Clas 3 Secure Server CA - GG"
 
        cert.set_issuer(issuer)
        cert.set_pubkey(ca_pkey)

        ext1 = M2Crypto.X509.new_extension('basicConstraints', 'CA:TRUE')
        ext1.set_critical(1)
        ext2 = M2Crypto.X509.new_extension('nsCertType', 'SSL CA, S/MIME CA, Object Signing CA') 
        #modulus = cert.get_pubkey().get_modulus()
        #sha_hash = hashlib.sha1(modulus).digest()
        #sub_key_id = ":".join(["%02X"%ord(byte) for byte in sha_hash])
        sub_key_id = "D1:AB:10:69:D1:AB:10:69:D1:AB:10:69:D1:AB:10:69:D1:AB:10:69" 
        ext3 = M2Crypto.X509.new_extension('subjectKeyIdentifier', sub_key_id)
        
        tempCert = open("ca/stubCa.cer")
        tempCert = tempCert.read()
        tempCert = M2Crypto.X509.load_cert_string(tempCert)
        ext4 = tempCert.get_ext('authorityKeyIdentifier')
        
        t = long(time.time())
        before = M2Crypto.ASN1.ASN1_UTCTIME()
        before.set_time(t-(60*60*24*30*6))
        after = M2Crypto.ASN1.ASN1_UTCTIME()
        after.set_time(t+(60*60*24*365*10))
        cert.set_not_before(before)
        cert.set_not_after(after)
        cert.add_ext(ext2)
        cert.add_ext(ext1)
        cert.add_ext(ext4)
        cert.add_ext(ext3)

        cert.sign(ca_pkey, 'sha1')
        return cert
    
    def cert (self, peer_sub, peer_iss, peer_not_after, peer_not_before,
              peer_serial, ca_key):
        key = self.generate_rsa_key()
        peer_key = self.make_pkey(key)
        peer_cert = self.make_peer_cert(peer_sub, peer_iss, peer_not_after, 
                                        peer_not_before, peer_serial, 
                                        peer_key, self.ca_pkey)
        return (peer_cert, peer_key)
    
    def make_peer_cert(self, peer_sub, peer_iss, peer_not_after, peer_not_before, 
                       peer_serial, peer_key, ca_key):

        cert = M2Crypto.X509.X509()
        cert.set_serial_number(random.randrange(0,0xffffff))
        cert.set_version(2)
        cert.set_subject(peer_sub)
        cert.set_issuer(self.ca_cert.get_subject())
        cert.set_pubkey(peer_key)
        cert.set_not_after(peer_not_after)
        cert.set_not_before(peer_not_before)
        ext1 = M2Crypto.X509.new_extension('basicConstraints', 'CA:FALSE')
        ext1.set_critical(1)
               
        modulus = cert.get_pubkey().get_modulus()
        sha_hash = hashlib.sha1(modulus).digest()
        sub_key_id = ":".join(["%02X"%ord(byte) for byte in sha_hash])

        ext2 = M2Crypto.X509.new_extension('subjectKeyIdentifier', sub_key_id)    
        ext3 = M2Crypto.X509.new_extension('keyUsage', 
               'Digital Signature, Non Repudiation, Key Encipherment, Data Encipherment')
        ext3.set_critical(1)
       
        tempCert = open("ca/stubPeer.cer")
        tempCert = tempCert.read()
        tempCert = M2Crypto.X509.load_cert_string(tempCert)
        ext4 = tempCert.get_ext('authorityKeyIdentifier')
        cert.add_ext(ext1)
        cert.add_ext(ext2)
        cert.add_ext(ext3) 
        cert.add_ext(ext4)
        cert.sign(self.ca_pkey,'sha1')
        return cert
    
    def get_fake_cert_and_key(self, real_cert):
        peer_sub = real_cert.get_subject()
        peer_iss = real_cert.get_issuer()
        peer_not_after = real_cert.get_not_after()
        peer_not_before = real_cert.get_not_before()
        peer_serial = real_cert.get_serial_number()
        fake_cert, fake_key = self.cert(peer_sub, peer_iss,
                                   peer_not_after, peer_not_before,
                                   peer_serial, self.ca_pkey)
        return (fake_cert, fake_key)

    def get_fake_cert_and_key_filename(self, real_cert):
        cert_subject = real_cert.get_subject().as_text()
        if cert_subject in self.store_of_certs:
            cert_container = self.store_of_certs[cert_subject]
            return cert_container.cert_file_name, cert_container.key_file_name
        else:
            fake_cert, fake_key = self.get_fake_cert_and_key(real_cert)
            
            temp_cert_file = tempfile.NamedTemporaryFile(delete=False)
            temp_cert_file.write(fake_cert.as_text() + "\n" + fake_cert.as_pem())
            temp_cert_file.flush()

            temp_key_file = tempfile.NamedTemporaryFile(delete=False)
            temp_key_file.write(fake_key.as_pem(None))
            temp_key_file.flush()
            self.store_of_certs[cert_subject] = CertAndKeyContainer(fake_cert, fake_key,
                    temp_cert_file.name, temp_key_file.name)
            return (temp_cert_file.name, temp_key_file.name)

ca = CertAuth()
