import rule
"""
These are global rules that are always loaded when Mallory starts

The rule action for the first rule that matches the incoming datagram or stream
is used. 


Future Development: Passthrough rules, rules that execute their action but do 
not halt the rule chain matching, will ultimately be added. The goal is to add
a "passthrough":True, parameter to the rule, in which case the rule processing
does not terminate with that rule, even if it matches. 


Note: UDP is not currently supported, but it will eventually be supported.

 
"""

# ORDER IS IMPORTANT!
userrules = [
# Default wildcard ruleset, send everything to debugger when active.
{
 "name":"http_muck_mangle_c2s", 
 "action":rule.Muck(["gzip,deflate/ /1","deflate/ /1","gzip/ /1"]),
 "direction":"c2s",
 "passthru":"True"
},
{
 "name":"FuzzS2C",
 "action":rule.Fuzz(bit_flip_percentage=45, bof_injection_percentage=100, bit_flip_density=12), 
 "direction":"s2c",
 "passthru":"True"
},
{
 "name":"default",  
 "action":rule.Debug()
},
#{
# "name":"https_debug", 
# "port":443, 
# "action":rule.Debug()
#},   
#{
# "name":"ssh_nothing", 
# "port":22,
# "action":rule.Nothing()
#},
#{
# "name":"s2c_nothing", 
# "direction":"s2c", 
# "port":192,
# "addr":"192.168.1.40",
# "action":rule.Muck(["Google/OOOGLE/g","A-Z/a/g"])
#},
#{
# "action":rule.Debug()
#},
#{
# "name":"c2s_vnc", 
# "direction":"c2s",
# "port":"5900",
# "action":rule.Muck(["\x04\x01\x00\x00\x00\x00\x00\x41/\x04\x01\x00\x00\x00\x00\x00\x42/g"]),
# "passthru":true
#},
#{
# "name":"s2c_debug",
# "direction":"s2c",
# "action":rule.Debug()
#},
#{
# "name":"c2s_debug",
# "direction":"c2s",
# "action":rule.Debug()
#},
#{
# "name":"s2c_nothing", 
# "direction":"s2c", 
# "action":rule.Nothing()
#},
#{
# "name":"c2s_nothing", 
# "direction":"c2s", 
# "action":rule.Nothing()
#},  
]

# Do not modify below this line. Beware: sleeping dragons live here
globalrules = []
for a in userrules:
    globalrules.append(rule.Rule(a["name"]).fromdict(a))
