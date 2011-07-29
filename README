INTRO
============
Mallory is an extensible TCP/UDP man in the middle proxy that is designed 
to be run as a gateway. Unlike other tools of its kind, Mallory supports 
modifying non-standard protocols on the fly.

CONFIGURATION
============
The goal is to man in the middle traffic for testing purposes. The ideal 
setup for Mallory is to have a "LAN" or "Victim" network that mallory 
acts as the gateway for. 

Option 1: PPTP:
The easiest and quickest way to get up and going is to setup a pptp 
server and have victims log into it. This works great with mobile devices
as most of them support a PPTP VPN client.

Option 2: Virtual Interfaces
If you're installing Mallory on a virtual machine and your target is on
a virtual machine, you can create a virtual mallory setup by having one
interface bridge, and a host only interface shared between the two VMs.

Option 3: Wireless Hotspot
If you have the ability to setup a wifi hotspot, you can route of the 
traffic over wifi, through mallory, and back onto the internet. This
can be done in a few different ways depending on your hardware. See
airbase-ng as one possibility.  

Option 4: Other
There are of course tons of other ways to setup a MITM especially with
software tools. The above are recommended over options like ARP poisoning
or DHCP exhaustion just because they're more stable.
