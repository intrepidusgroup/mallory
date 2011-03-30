import ConfigParser
import protocol
import sets
import logging

"""
import protocol
print "Proto is %s" % (opts.options.proto)

modulename,protoname = opts.options.proto.split(".")
    
try:
    protomodule = getattr(protocol, modulename)
    protoinstance = getattr(protomodule, protoname)(None, None, None)
    mallory.configure_protocol(protoinstance, "add")
    mallory.log.info("Configuring command line protocol instance: %s "
                     "for port %d" \
                     % (protoinstance, protoinstance.serverPort))
except:
    print "Invalid protocol specified at command line"
            
        
"""

# Protocol Configuration

# Get list of configured protocols from Mallory

# Implement Save functionality

class ConfigProtocols(object):
    def __init__(self):
        self.config_path = "protos.ini"
        self.protocols = None
        self.log = logging.getLogger("mallorymain")
        
        self.load_config()
      
    def load_config(self):
        cp = ConfigParser.ConfigParser()
        cp.read(self.config_path)
        config_items = cp.items("protocols")
        
        protos = []
        proto_ports = sets.Set()
        for cur_proto in config_items: 
            proto_data = cur_proto[1].split(":")
            proto_name = proto_data[0]
            proto_port = int(proto_data[1])
            
            # Only one protocol per port
            if proto_port not in proto_ports:
                try:
                    module_name,proto_name_str = proto_name.split(".")
                    proto_module = getattr(protocol, module_name)
                    proto_instance = \
                        getattr(proto_module, proto_name_str)(None, None, None)
                    proto_instance.serverPort = proto_port
                    
                    protos.append(proto_instance)
                    proto_ports.add(proto_port)
                except:
                    self.log.info( ("ConfigProtocols.load_config: bad config "
                                    "line supplied (%s)") % proto_data)
        print protos
         
        self.protocols = protos
        
    def get_protocols(self):
        return self.protocols
    