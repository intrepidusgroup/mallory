import time
import socket
import config
import uuid
import Queue
import logging
import netfilter
import traceback
import select
import random
import thread
import rule


from observer import Subject
from debug import DebugEvent
from binascii import hexlify, unhexlify, crc32

        
class Plugin (Subject):
    def __init__(self, rules = [], config = config.Config()):
        Subject.__init__(self)
        self.log = logging.getLogger("mallorymain")
        self.config = config
        self.rules = rules
        #Will be used to know where to start new "runp" thread on plug in conf
        self.persistent = 0

    def update (self,publisher,**kwargs):
        pass
    
    def runp (self):
        pass
