# This is a standard Python dictionary. The key (cnn.com, etc.) is a domain
# name you want to search for inside of an A record question. The value is an IP
# address as a string. The IP will be replaced if the key is found anywhere
# in the string. The rule "cnn.com" will match "m.cnn.com or www.cnn.com".
# If you want to be more specific you can specify the exact question you want
# replaced. By default the period at the end of the question is a part of
# the question that gets prased out by dnspython
#
# An example incoming question might be: 
#
# ;QUESTION
# login.yahoo.com. IN A
#               ^^^
#           Note the period.  
#
# Don't forget the comma after each entry. The last entry does not
# need the comma. See Python reference materials for more help with
# the syntax. 
#

arecord_manglemap = {
  "cnn.com":"216.34.181.45",
  "msnbc.com":"216.34.181.45",
  "digg.com":"24.29.138.57"
}