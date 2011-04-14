import ConfigParser
import protocol
import sets
import logging
import Pyro.core
import observer


class ConfigRules(observer.Subject, Pyro.core.ObjBase):
    def __init__(self):
        observer.Subject.__init__(self)
        Pyro.core.ObjBase.__init__(self)
        
        self.config_path = "protos.ini"
        self.load_config()
        
        
    def load_config_raw(self):
        f = open(self.config_path, "r")
        config_raw = f.read()
        f.close()
        
        return config_raw
    
    
    def load_config(self):
        pass    