import os.path
import os
import Queue
import sqlite3
import time


# The traffic database class contains methods for creating the tables
# that get used to store all traffic. It also contains Queue management
# functionality to moderate the flow of data into the sqlite3 database
class TrafficDb:
    def __init__(self, dbName, dbPath="../db/", use_existing=False):
        self.dbName = dbName
        self.dbPath = dbPath
        self.use_existing = use_existing
        self.qFlow = Queue.Queue()
        self.qConn = Queue.Queue()
        self.dgram = Queue.Queue()
        self.qfuzztcp = Queue.Queue()
        self.qfuzzudp = Queue.Queue()

    # This method defines the traffic db schema. 
    # TODO: Clean this up a bit. Add PKs and FK refs to maintain ref integrity.  
    def makeTables(self):
        connections = """
            CREATE TABLE connections(
                connCount INTEGER,
                serverIp TEXT,
                serverPort INTEGER, 
                clientIp TEXT,
                clientPort INTEGER
            )"""
        
        flows = """
        CREATE TABLE flows(
            conncount INTEGER, 
            direction TEXT, 
            buffindex INTEGER, 
            timestamp FLOAT, 
            buffer BLOB
        )"""
        
        dgrams = """
            CREATE TABLE dgram(
                saddr TEXT,
                sport INTEGER,
                daddr TEXT,
                dport INTEGER,
                direction TEXT,
                body BLOB,
                timestamp TEXT         
            )
        """

        fuzztcp = """
            CREATE TABLE fuzztcp(
                conncount INTEGER,
                buffindex INTEGER,
                direction TEXT,
                orgString BLOB,
                fuzzString BLOB      
            )
        """
 
        fuzzudp = """
            CREATE TABLE fuzzudp(
                saddr TEXT,
                sport INTEGER,
                daddr TEXT,
                dport INTEGER,
                direction TEXT,
                oldBody BLOB,
                fuzzBody BLOB,
                timestamp TEXT         
            )
        """


        self.curr.execute(connections)
        self.curr.execute(flows)
        self.curr.execute(dgrams)
        self.curr.execute(fuzztcp)
        self.curr.execute(fuzzudp)
        self.curr.execute("")
        
    # This method should be kicked off as a separate thread
    def fillDB(self):
        # Avoid overwriting existing traffic databases
        # TODO: make this nice and proper file handling with exceptions and 
        dbName = os.path.join(self.dbPath, self.dbName)
        if not os.path.exists(dbName):
            if not os.path.exists(self.dbPath):
               try:
                   os.mkdir(self.dbPath)
               except:
                   print "Failed to create the directory for the DB"
                   return 
        
        existed = os.path.exists(dbName)
        if not self.use_existing and existed:
            self.dbName = self.dbName + "_" + str(time.time())
            dbName = os.path.join(self.dbPath, self.dbName)
            existed = os.path.exists(dbName)
        
       
        self.conn = sqlite3.connect(dbName)
        self.curr = self.conn.cursor()

        if not existed:
            self.makeTables()
        
        # Main loop
        while True:
            # Tune this to space out disk i/o. 100ms is a good default. 
            time.sleep(.1)
            
            while not self.qConn.empty():
                entry = self.qConn.get()
                self.curr.execute("insert into connections values(?,?,?,?,?)",\
                                   entry)
            
            while not self.qFlow.empty():
                entry = self.qFlow.get()
                self.curr.execute("insert into flows values(?,?,?,?,?)", entry)
            
            while not self.dgram.empty():
                entry = self.dgram.get()
                self.curr.execute("insert into dgram values(?,?,?,?,?,?,?)",
                                  entry);

            while not self.qfuzztcp.empty():
                entry = self.qfuzztcp.get()
                self.curr.execute("insert into fuzztcp values(?,?,?,?,?)",
                                  entry);
 
            while not self.qfuzzudp.empty():
                entry = self.qfuzzudp.get()
                self.curr.execute("insert into fuzzudp values(?,?,?,?,?,?,?,?)",
                                  entry);


                
            self.conn.commit()
            
            
    # Clean up shop
    def killConn(self):
        self.conn.commit()
        self.curr.close()
        self.conn.close() 

