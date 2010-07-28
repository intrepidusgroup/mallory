import optparse

class CmdLineOpts(object):    
    def __init__(self):
        parser = optparse.OptionParser()
        parser.add_option("-n", "--no-transparent", dest="notransparent", 
                          help="Turn off the transparent proxy. This puts " \
                          "the proxy into a static only mode. You must supply" \
                          "the destination IP:Port you want traffic to go to" \
                          " example: -n ip:port, -n a.b.c.d:443")
        
        parser.add_option("-l", "--listen", dest="listen", 
                            help="Specify the port to listen on. " \
                            "Only useful with --no-transparent. Format is: " \
                            "example: -l 443", 
                            default="20755")
        
        parser.add_option("-d", "--trafficdb", dest="trafficdb", 
                          help="Specify the traffic database name.", 
                          default="trafficdb")

        parser.add_option("-p", "--proto", dest="proto", 
                          help="Specify the protocol to use. This is only " \
                          "useful with the no-transparent option. You must " \
                          "specify the module inside of the protocol package " \
                          "as well as the exact protocol class to " \
                          "instantiate. example: -p sslproto.SSLProtocol," \
                          "or -p ssh.SSHProtocol or -p http.HTTP" \
                          "Note: this option will add and configure the " \
                          "protocol using the protocol's default settings. " \
                          "This adds one additional protocol. Ideally all " \
                          "other protocols are turned off to insure this " \
                          "protocol is correctly used.")
        
        parser.add_option("-x", "--proxify", dest="proxify", 
                          help="Proxify an HTTP connection. Specify the " \
                          "IP:Port to redirect connections to a proxy. " \
                          "Note:  There is a subtle difference between the " \
                          "--no-transparent option " \
                          "and --proxify. Proxify changes the destination " \
                          "after protocol determination has been performed. " \
                          "This means that the protocol (as mallory will " \
                          "interpret it) will be determined " \
                          "by the real destination, port 80 for HTTP, while " \
                          "the traffic is still sent to the proxy.")
          
                
        (self.options, self.args) = parser.parse_args()