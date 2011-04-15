import ConfigParser
import protocol
import sets
import logging
import Pyro.core
import observer


class ConfigProtocols(observer.Subject, Pyro.core.ObjBase):
    def __init__(self):
        observer.Subject.__init__(self)
        Pyro.core.ObjBase.__init__(self)
        
        self.config_path = "protos.ini"
        # self.protocols should be type array
        self.protocols = None
        self.log = logging.getLogger("mallorymain")
        self.load_config()
      
    def load_config_raw(self):
        f = open(self.config_path, "r")
        config_raw = f.read()
        f.close()
        
        return config_raw
    
    def save_config_raw(self, raw_config):
        f = open(self.config_path, "w")
        f.write(raw_config)
        f.close()
        
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
 
        self.protocols = protos
        
        self.notify(action="load_protos", protocols=protos)
            
    def num_protos(self):
        return len(self.protocols)
      
    def get_protocols(self):
        return self.protocols
    