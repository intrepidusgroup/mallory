from base import TcpProtocol
import sslproto
import http
import malloryevt

class HTTPS(http.HTTP, sslproto.SSLProtocol):
    """
    """
    def __init__(self, trafficdb, source, destination):
        http.HTTP.__init__(self, trafficdb, source, destination)
        sslproto.SSLProtocol.__init__(self, trafficdb, source, destination)
        self.friendly_name = "HTTPS"      
        self.serverPort = 443
        self.name = "HTTPS"
        self.log.debug("HTTPS: Initializing") 
        self.supports = {malloryevt.STARTS2C:True, malloryevt.STARTC2S:True,
                         malloryevt.CSAFTERSS:True, malloryevt.SSCREATE:True}