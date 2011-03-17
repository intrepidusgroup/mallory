import Pyro.core
import Pyro.naming
import logging
import sys

class RPCServer(object):
    
    def __init__(self):
        Pyro.core.initServer()        
        self.daemon = Pyro.core.Daemon()        
        self.log = logging.getLogger("mallorymain")
        
    def rpc_server(self):
        """
        rpcserver is intended to be launched as a separate thread. This class
        will launch an RPC server that can pass and receive debugging events
        to debugging clients.
        """

    def add_remote_obj(self, obj, name):
        # Register the Pyro object here
        self.log.info(("RPCServer: add_remote_obj - adding remote object %s " 
                      " with remote object name '%s'") % (obj, name))
        uri = self.daemon.connect(obj, name)
        
    def start_server(self):
        self.log.info("RPCServer: start_server - starting up")     

        try:
            # Implicitly starts on port 7766. 
            # TODO: Make sure this listens on localhost only
            self.daemon.requestLoop()                    
        except:
            self.log.error("Failed to start the daemon")
            self.log.error(sys.exc_info())