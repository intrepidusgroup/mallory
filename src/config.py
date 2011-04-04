import logging
import sys

class Config(object):
    def __init__(self):
        self.debug = 1
        self.http = {}
        self.http['flip_images'] = True
        
    def logsetup(self, log):
        """
        Static method use to configure the logging. Housed in the config
        class as it is a reasonable place to hold logging configuration 
        """
        fmt = "[*] [%(asctime)s] %(levelname)s:%(message)s"
    
        logging.basicConfig(filename="mallory.log",
                            filemode="w",
                            format=fmt)        
    
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(logging.DEBUG)
        console.setFormatter(logging.Formatter(fmt))
        
        # Currently setup for debugging. Set this to logging.INFO to cut
        # down on the amount of logging detail.
        log.setLevel(logging.DEBUG)
        log.addHandler(console)
        
        log.info("Logging setup complete")    