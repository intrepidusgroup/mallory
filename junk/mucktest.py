import muckpipe
import rule

ruledict = {
 "name":"http_muck_mangle", 
 "port":80, 
 #"action":rule.Muck(["\//fslash/g","T/t/2"])
 "action":rule.Muck(["Address/Arfdress/g"]),
 "direction":"s2c"
}


r = rule.Rule("").fromdict(ruledict)

f = open("tip.html", "r")
fdata = f.read()

result = r.action.execute(data=fdata)

print result