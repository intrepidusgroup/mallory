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
from daemon import Daemon
from plugin.session_hijack import Session_Hijack
        
class HTTPD (Daemon):
    def __init__(self, rules = [], config = config.Config()):
        Daemon.__init__(self)
        self.serverPort = 80

    def rund (self):
        self.plugin_config()
        while True:
            time.sleep(1)
            while (self.eventQ.qsize() > 0):
               try:
                    currEvent = self.eventQ.get(False)
                    self.notify(event="HTTPD", data=currEvent)
               except:
                    break;

    def plugin_config (self):
        #Make this more generic
        #Will support persistent, non persistent, plygings
        plug = Session_Hijack ()
        self.attach(plug)
        thread.start_new_thread (plug.runp, ())
