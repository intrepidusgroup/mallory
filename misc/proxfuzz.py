# Proxyfuzz: a TCP and UDP proxy man-in-the-middle fuzzer
# v 0.1
# By Rodrigo Marcos
# http://www.theartoffuzzing.com

from twisted.protocols import portforward
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
import getopt, sys
from random import randint


# UDP Proxy stuff

class Client(DatagramProtocol):
	def __init__(self, server, host, port):
		self.server = server
		self.host = host
		self.port = port
    
	def startProtocol(self):
		self.transport.connect(desthost, destport)
    
	def datagramReceived(self, data, (host, port)):
		global verbose
		global notuntil
		global request
		global testclient
	
		if testclient:
			if request < notuntil:
				request = request + 1
			else:
				data = fuzz(data)
		if verbose:
			print "Server ------> Client"
			print "%r" % data
		
	        self.server.transport.write(data, (self.host, self.port))
 
class Server(DatagramProtocol):
	client = None
    
	def datagramReceived(self, data, (host, port)):
		if not self.client or self.client.host != host or self.client.port != port:
			self.client = Client(self, host, port)
			reactor.listenUDP(0, self.client)

		global verbose
		global notuntil
		global request
		global testserver
		
		if testserver:
			if request < notuntil:
				request = request + 1
			else:
				data = fuzz(data)
		if verbose:
			print "Client ------> Server"
			print "%r" % data 
		self.client.transport.write(data, (desthost, destport))
 
# TCP proxy stuff

def server_dataReceived(self, data):
	global verbose
	global notuntil
	global request
	global testserver
	
	if testserver:
		if request < notuntil:
			request = request + 1
		else:
			data = fuzz(data)

	if verbose:
		print "Client ------> server"
		print "%r" % data
		
	portforward.Proxy.dataReceived(self, data)

portforward.ProxyServer.dataReceived = server_dataReceived

def client_dataReceived(self, data):
	global verbose
	global notuntil
	global request
	global testclient
	
	if testclient:
		if request < notuntil:
			request = request + 1
		else:
			data = fuzz(data)
	if verbose:
		print "Server ------> Client"
		print "%r" % data
	
	portforward.Proxy.dataReceived(self, data)

portforward.ProxyClient.dataReceived = client_dataReceived

       
overflowstrings = ["A" * 255, "A" * 256, "A" * 257, "A" * 420, "A" * 511, "A" * 512, "A" * 1023, "A" * 1024, "A" * 2047, "A" * 2048, "A" * 4096, "A" * 4097, "A" * 5000, "A" * 10000, "A" * 20000, "A" * 32762, "A" * 32763, "A" * 32764, "A" * 32765, "A" * 32766, "A" * 32767, "A" * 32768, "A" * 65534, "A" * 65535, "A" * 65536, "%x" * 1024, "%n" * 1025 , "%s" * 2048, "%s%n%x%d" * 5000, "%s" * 30000, "%s" * 40000, "%.1024d", "%.2048d", "%.4096d", "%.8200d", "%99999999999s", "%99999999999d", "%99999999999x", "%99999999999n", "%99999999999s" * 1000, "%99999999999d" * 1000, "%99999999999x" * 1000, "%99999999999n" * 1000, "%08x" * 100, "%%20s" * 1000,"%%20x" * 1000,"%%20n" * 1000,"%%20d" * 1000, "%#0123456x%08x%x%s%p%n%d%o%u%c%h%l%q%j%z%Z%t%i%e%g%f%a%C%S%08x%%#0123456x%%x%%s%%p%%n%%d%%o%%u%%c%%h%%l%%q%%j%%z%%Z%%t%%i%%e%%g%%f%%a%%C%%S%%08x"]
	
def bitflipping(data):
	l = len(data)
	n = int(l*7/100) # 7% of the bytes to be modified
	
	for i in range(0,n): # We change the bytes
		r = randint(0,l-1)
		data = data[0:r] + chr(randint(0,255)) + data[r+1:]
	return data

def bofinjection(data):
	l = len(data)
	r = randint(0,len(overflowstrings)-1)
	data = data[0:r] + overflowstrings[r] + data[r-l:]
	return data

def fuzz(data):

	r = randint(0,5)
	if r==0:
		data = bitflipping(data)

	r = randint(0,5)
	if r==0:
		data = bofinjection(data)
	return data
	
def startudpproxy():
	reactor.listenUDP(localport, Server())
	reactor.run()
	
def starttcpproxy():
	reactor.listenTCP(localport, portforward.ProxyFactory(desthost, destport))
	reactor.run()

def usage():
	#print "###############################################################"
	print
	print "ProxyFuzz 0.1, Simple fuzzing proxy by Rodrigo Marcos"
	print "http://www.theartoffuzzing.com"
	print
	print "usage():"
	#print
	print "python proxyfuzz -l <localport> -r <remotehost> -p <remoteport> [options]"
	print
	print " [options]"
	print "		-c: Fuzz only client side (both otherwise)"
	print "		-s: Fuzz only server side (both otherwise)"
	print "		-w: Number of requests to send before start fuzzing"
	print "		-u: UDP protocol (otherwise TCP is used)"
	print "		-v: Verbose (outputs network traffic)"
	print "		-h: Help page"


verbose = False
notuntil = 0
request = 0
proto = "tcp"
localport = 0
desthost = ""
destport = 0
testclient = 1
testserver = 1
def main():
	global verbose
	global notuntil
	global proto
	global localport
	global desthost
	global destport
	global testclient
	global testserver
	
	try:
		opts, args = getopt.getopt(sys.argv[1:], "uvhcsl:r:p:w:", ["help"])
	except getopt.GetoptError:
		usage()
		sys.exit(2)
	try:
		for o, a in opts:
			if o in ("-h", "--help"):
				usage()
				sys.exit()
			if o == "-l":
				localport=int(a)
			if o == "-r":
				desthost=a
			if o == "-p":
				destport=int(a)
			if o == "-v":
				verbose = True
			if o == "-w":
				notuntil=int(a)
			if o == "-u":
				proto="udp"
			if o == "-c": # Only client
				testserver=0
			if o == "-s": # Only server
				testclient=0
				
				
	except:
		usage()
		sys.exit(2)
		
	if testserver==0 and testclient==0:
		usage()
		sys.exit(2)
	elif localport==0 or desthost=="" or destport==0:
		usage()
		sys.exit(2)
	else:
		if proto=="tcp":
			starttcpproxy()
		else: # UDP
			startudpproxy()

if __name__ == "__main__":
    main()
    
    
