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

 

        
class Daemon(Subject):
    def __init__(self, rules = [], config = config.Config()):
        Subject.__init__(self)
        self.log = logging.getLogger("mallorymain")
        self.config = config
        self.rules = rules
        self.eventQ = Queue.Queue(0)

    def update (self, publisher, **kwargs):
        self.eventQ.put(kwargs) 
    


